import pytest

from app.llm_client import LLMClient


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
