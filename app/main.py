import json
import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.llm_client import LLMClient
from app.models import ExplainRequest

load_dotenv()

app = FastAPI(title="codesage-service")

llm_client = LLMClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model_name=os.getenv("MODEL_NAME", "claude-sonnet-5"),
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _explain_event_stream(code: str, question: str) -> AsyncIterator[str]:
    async for chunk in llm_client.stream_explanation(code, question):
        yield f"data: {json.dumps({'chunk': chunk})}\n\n"


@app.post("/explain")
async def explain(request: ExplainRequest) -> StreamingResponse:
    return StreamingResponse(
        _explain_event_stream(request.code, request.question),
        media_type="text/event-stream",
    )
