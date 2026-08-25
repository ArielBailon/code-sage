from collections.abc import AsyncIterator

import anthropic
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.prompts.v1 import PROMPT_V1

MAX_ATTEMPTS = 4


def _is_retryable_status(exc: BaseException) -> bool:
    return isinstance(exc, anthropic.APIStatusError) and (
        exc.status_code == 429 or exc.status_code >= 500
    )


class LLMClient:
    """Single entry point for LLM calls. Retries/backoff on 429/5xx live here."""

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
        yielded_any = False

        def _should_retry(exc: BaseException) -> bool:
            return not yielded_any and _is_retryable_status(exc)

        async for attempt in AsyncRetrying(
            retry=retry_if_exception(_should_retry),
            stop=stop_after_attempt(MAX_ATTEMPTS),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                async with self._client.messages.stream(
                    model=self.model_name,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                ) as stream:
                    async for text in stream.text_stream:
                        yielded_any = True
                        yield text
                return
