import anthropic
import httpx
import pytest

from app.llm_client import LLMClient


def _status_error(status_code: int) -> anthropic.APIStatusError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code=status_code, request=request)
    return anthropic.APIStatusError("boom", response=response, body=None)


class _FakeStream:
    def __init__(self, chunks: list[str]) -> None:
        async def _gen():
            for chunk in chunks:
                yield chunk

        self.text_stream = _gen()

    async def __aenter__(self) -> "_FakeStream":
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class _FakeMessages:
    def __init__(self, chunks: list[str], calls: list[dict]) -> None:
        self._chunks = chunks
        self._calls = calls

    def stream(self, **kwargs: object) -> _FakeStream:
        self._calls.append(kwargs)
        return _FakeStream(self._chunks)


class _FakeAnthropicClient:
    def __init__(self, chunks: list[str], calls: list[dict]) -> None:
        self.messages = _FakeMessages(chunks, calls)


@pytest.mark.anyio
async def test_stream_explanation_yields_chunks_in_order():
    calls: list[dict] = []
    fake_client = _FakeAnthropicClient(["Hola", " mundo"], calls)
    client = LLMClient(model_name="test-model", client=fake_client)

    chunks = [c async for c in client.stream_explanation("def f(): pass", "que hace?")]

    assert chunks == ["Hola", " mundo"]


@pytest.mark.anyio
async def test_stream_explanation_formats_prompt_and_uses_model():
    calls: list[dict] = []
    fake_client = _FakeAnthropicClient([], calls)
    client = LLMClient(model_name="test-model", client=fake_client)

    [c async for c in client.stream_explanation("def f(): pass", "que hace?")]

    assert len(calls) == 1
    assert calls[0]["model"] == "test-model"
    prompt = calls[0]["messages"][0]["content"]
    assert "def f(): pass" in prompt
    assert "que hace?" in prompt


class _FlakyStream:
    def __init__(self, attempt: int, fail_times: int, chunks: list[str]) -> None:
        self._attempt = attempt
        self._fail_times = fail_times
        self._chunks = chunks

    async def __aenter__(self) -> "_FlakyStream":
        if self._attempt <= self._fail_times:
            raise _status_error(503)

        async def _gen():
            for chunk in self._chunks:
                yield chunk

        self.text_stream = _gen()
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class _FlakyMessages:
    def __init__(self, fail_times: int, chunks: list[str], calls: list[dict]) -> None:
        self._fail_times = fail_times
        self._chunks = chunks
        self._calls = calls
        self._attempts = 0

    def stream(self, **kwargs: object) -> _FlakyStream:
        self._calls.append(kwargs)
        self._attempts += 1
        return _FlakyStream(self._attempts, self._fail_times, self._chunks)


class _FlakyAnthropicClient:
    def __init__(self, fail_times: int, chunks: list[str], calls: list[dict]) -> None:
        self.messages = _FlakyMessages(fail_times, chunks, calls)


class _MidStreamFailureStream:
    def __init__(self, first_chunk: str) -> None:
        self._first_chunk = first_chunk

    async def __aenter__(self) -> "_MidStreamFailureStream":
        async def _gen():
            yield self._first_chunk
            raise _status_error(500)

        self.text_stream = _gen()
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class _MidStreamFailureMessages:
    def __init__(self, first_chunk: str, calls: list[dict]) -> None:
        self._first_chunk = first_chunk
        self._calls = calls

    def stream(self, **kwargs: object) -> _MidStreamFailureStream:
        self._calls.append(kwargs)
        return _MidStreamFailureStream(self._first_chunk)


class _MidStreamFailureAnthropicClient:
    def __init__(self, first_chunk: str, calls: list[dict]) -> None:
        self.messages = _MidStreamFailureMessages(first_chunk, calls)


class _AlwaysFailsMessages:
    def __init__(self, exc: Exception, calls: list[dict]) -> None:
        self._exc = exc
        self._calls = calls

    def stream(self, **kwargs: object) -> None:
        self._calls.append(kwargs)
        raise self._exc


class _AlwaysFailsAnthropicClient:
    def __init__(self, exc: Exception, calls: list[dict]) -> None:
        self.messages = _AlwaysFailsMessages(exc, calls)


@pytest.mark.anyio
async def test_stream_explanation_retries_retryable_error_then_succeeds(monkeypatch):
    async def _no_wait(_seconds: float) -> None:
        return None

    monkeypatch.setattr("asyncio.sleep", _no_wait)
    calls: list[dict] = []
    fake_client = _FlakyAnthropicClient(fail_times=2, chunks=["Hola", " mundo"], calls=calls)
    client = LLMClient(model_name="test-model", client=fake_client)

    chunks = [c async for c in client.stream_explanation("def f(): pass", "que hace?")]

    assert chunks == ["Hola", " mundo"]
    assert len(calls) == 3


@pytest.mark.anyio
async def test_stream_explanation_does_not_retry_after_first_chunk_yielded():
    calls: list[dict] = []
    fake_client = _MidStreamFailureAnthropicClient(first_chunk="Hola", calls=calls)
    client = LLMClient(model_name="test-model", client=fake_client)

    received: list[str] = []
    with pytest.raises(anthropic.APIStatusError):
        async for chunk in client.stream_explanation("def f(): pass", "que hace?"):
            received.append(chunk)

    assert received == ["Hola"]
    assert len(calls) == 1


@pytest.mark.anyio
async def test_stream_explanation_does_not_retry_non_retryable_error():
    calls: list[dict] = []
    fake_client = _AlwaysFailsAnthropicClient(exc=_status_error(400), calls=calls)
    client = LLMClient(model_name="test-model", client=fake_client)

    with pytest.raises(anthropic.APIStatusError):
        async for _ in client.stream_explanation("def f(): pass", "que hace?"):
            pass

    assert len(calls) == 1
