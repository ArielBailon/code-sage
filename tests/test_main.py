import json

from fastapi.testclient import TestClient

import app.main as main

client = TestClient(main.app)


async def _fake_stream_explanation(code: str, question: str):
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


async def _fake_stream_incomplete(code: str, question: str):
    yield 'resumen: "La funcion suma una lista."\n'


def test_explain_emits_error_event_on_incomplete_response(monkeypatch):
    monkeypatch.setattr(main.llm_client, "stream_explanation", _fake_stream_incomplete)

    response = client.post(
        "/explain",
        json={"code": "def f(): pass", "question": "que hace?"},
    )

    assert response.status_code == 200
    assert "event: error" in response.text
