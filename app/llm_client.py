class LLMClient:
    """Single entry point for LLM calls. Retries/backoff land here later."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key
        self.model_name = model_name

    async def stream_explanation(self, code: str, question: str):
        raise NotImplementedError
