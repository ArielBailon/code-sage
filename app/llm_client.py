from collections.abc import AsyncIterator, Callable

import anthropic
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.prompts import get_prompt

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
        prompt_version: str = "v1",
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.prompt_version = prompt_version
        self._prompt_template = get_prompt(prompt_version)
        self._client = client or anthropic.AsyncAnthropic(api_key=api_key)

    async def stream_explanation(
        self,
        code: str,
        question: str,
        *,
        on_usage: Callable[[anthropic.types.Usage], None] | None = None,
    ) -> AsyncIterator[str]:
        prompt = self._prompt_template.format(code=code, question=question)
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
                    if on_usage is not None:
                        message = await stream.get_final_message()
                        on_usage(message.usage)
                return
