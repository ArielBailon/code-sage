import json
import os
from collections.abc import AsyncIterator

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.llm_client import LLMClient
from app.models import ExplainRequest
from app.response_parser import FieldStreamParser

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
    parser = FieldStreamParser()
    try:
        async for chunk in llm_client.stream_explanation(code, question):
            for name, value in parser.feed(chunk):
                yield f"event: {name}\ndata: {json.dumps(value)}\n\n"
        for name, value in parser.feed("\n"):
            yield f"event: {name}\ndata: {json.dumps(value)}\n\n"
        response = parser.finalize()
        yield f"event: done\ndata: {response.model_dump_json()}\n\n"
    except (json.JSONDecodeError, ValidationError) as exc:
        yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
    except anthropic.AnthropicError:
        yield (
            "event: error\ndata: "
            f"{json.dumps({'error': 'LLM provider request failed'})}\n\n"
        )


@app.post("/explain")
async def explain(request: ExplainRequest) -> StreamingResponse:
    return StreamingResponse(
        _explain_event_stream(request.code, request.question),
        media_type="text/event-stream",
    )
