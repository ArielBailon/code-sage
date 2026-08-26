import json

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.cost import calculate_cost

client = TestClient(main.app)


def _status_error(status_code: int) -> anthropic.APIStatusError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code=status_code, request=request)
    return anthropic.APIStatusError("boom", response=response, body=None)


class _FakeUsage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


async def _fake_stream_explanation(code: str, question: str, *, on_usage=None):
    for part in [
        'resumen: "La funcion suma una lista."\n',
        'complejidad: "O(n)"\nposibles_bugs: []\n',
        'sugerencia: "Usar sum()."',
    ]:
        yield part


def test_explain_streams_named_events_and_done(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_explanation)

    response = client.post(
        "/explain",
        json={"code": "def f(nums): return sum(nums)", "question": "que hace?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    body = response.text
    assert 'event: resumen\ndata: "La funcion suma una lista."' in body
    assert 'event: complejidad\ndata: "O(n)"' in body
    assert "event: posibles_bugs\ndata: []" in body
    assert 'event: sugerencia\ndata: "Usar sum()."' in body

    done_line = next(
        line for line in body.splitlines() if line.startswith("data: ") and '"resumen"' in line
    )
    done_payload = json.loads(done_line.removeprefix("data: "))
    assert done_payload == {
        "resumen": "La funcion suma una lista.",
        "complejidad": "O(n)",
        "posibles_bugs": [],
        "sugerencia": "Usar sum().",
    }


async def _fake_stream_incomplete(code: str, question: str, *, on_usage=None):
    yield 'resumen: "La funcion suma una lista."\n'


def test_explain_emits_error_event_on_incomplete_response(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_incomplete)

    response = client.post(
        "/explain",
        json={"code": "def f(): pass", "question": "que hace?"},
    )

    assert response.status_code == 200
    assert "event: error" in response.text


async def _fake_stream_provider_failure(code: str, question: str, *, on_usage=None):
    if False:
        yield ""
    raise _status_error(503)


def test_explain_emits_error_event_on_exhausted_provider_retries(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_provider_failure)

    response = client.post(
        "/explain",
        json={"code": "def f(): pass", "question": "que hace?"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'event: error\ndata: {"error": "LLM provider request failed"}' in response.text


async def _fake_stream_with_usage(code: str, question: str, *, on_usage=None):
    for part in [
        'resumen: "La funcion suma una lista."\n',
        'complejidad: "O(n)"\nposibles_bugs: []\n',
        'sugerencia: "Usar sum()."',
    ]:
        yield part
    if on_usage is not None:
        on_usage(_FakeUsage(input_tokens=1000, output_tokens=500))


def test_explain_emits_cost_event_after_done(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_with_usage)

    response = client.post(
        "/explain",
        json={"code": "def f(nums): return sum(nums)", "question": "que hace?"},
    )

    assert response.status_code == 200
    body = response.text
    done_index = body.index("event: done")
    cost_index = body.index("event: cost")
    assert done_index < cost_index

    cost_line = next(
        line for line in body.splitlines() if line.startswith("data: ") and '"tokens_in"' in line
    )
    cost_payload = json.loads(cost_line.removeprefix("data: "))
    assert cost_payload == {
        "tokens_in": 1000,
        "tokens_out": 500,
        "model": main.llm_client.model_name,
        "cost": pytest.approx(
            calculate_cost(1000, 500, main.llm_client.model_name)
        ),
        "prompt_version": main.llm_client.prompt_version,
    }


def test_explain_cost_event_reflects_configured_prompt_version(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_with_usage)
    monkeypatch.setattr(main.llm_client, "prompt_version", "v2")

    response = client.post(
        "/explain",
        json={"code": "def f(nums): return sum(nums)", "question": "que hace?"},
    )

    assert response.status_code == 200
    cost_line = next(
        line
        for line in response.text.splitlines()
        if line.startswith("data: ") and '"tokens_in"' in line
    )
    cost_payload = json.loads(cost_line.removeprefix("data: "))
    assert cost_payload["prompt_version"] == "v2"


def test_explain_skips_cost_event_for_unrecognized_model(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_with_usage)
    monkeypatch.setattr(main.llm_client, "model_name", "not-a-real-model")

    response = client.post(
        "/explain",
        json={"code": "def f(nums): return sum(nums)", "question": "que hace?"},
    )

    assert response.status_code == 200
    assert "event: done" in response.text
    assert "event: cost" not in response.text


def test_explain_rejects_oversized_code(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_explanation)

    response = client.post(
        "/explain",
        json={"code": "x" * 20_001, "question": "que hace?"},
    )

    assert response.status_code == 422


def test_explain_rejects_oversized_question(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_explanation)

    response = client.post(
        "/explain",
        json={"code": "def f(): pass", "question": "x" * 2_001},
    )

    assert response.status_code == 422


def test_explain_accepts_code_and_question_at_the_length_limit(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_explanation)

    response = client.post(
        "/explain",
        json={"code": "x" * 20_000, "question": "x" * 2_000},
    )

    assert response.status_code == 200
