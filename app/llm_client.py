from collections.abc import AsyncIterator

import anthropic

from app.prompts.v1 import PROMPT_V1


class LLMClient:
    """Single entry point for LLM calls. Retries/backoff land here later."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key)

    async def stream_explanation(self, code: str, question: str) -> AsyncIterator[str]:
        prompt = PROMPT_V1.format(code=code, question=question)
        async with self._client.messages.stream(
            model=self.model_name,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
