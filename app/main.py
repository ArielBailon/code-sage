import json
import logging
import os
from collections.abc import AsyncIterator

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.cost import calculate_cost
from app.llm_client import LLMClient
from app.models import ExplainRequest, RequestCost
from app.response_parser import FieldStreamParser

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="codesage-service")

llm_client = LLMClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model_name=os.getenv("MODEL_NAME", "claude-sonnet-5"),
    prompt_version=os.getenv("PROMPT_VERSION", "v1"),
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _explain_event_stream(code: str, question: str) -> AsyncIterator[str]:
    parser = FieldStreamParser()
    usage: anthropic.types.Usage | None = None

    def _capture_usage(reported: anthropic.types.Usage) -> None:
        nonlocal usage
        usage = reported

    try:
        async for chunk in llm_client.stream_explanation(
            code, question, on_usage=_capture_usage
        ):
            for name, value in parser.feed(chunk):
                yield f"event: {name}\ndata: {json.dumps(value)}\n\n"
        for name, value in parser.feed("\n"):
            yield f"event: {name}\ndata: {json.dumps(value)}\n\n"
        response = parser.finalize()
        yield f"event: done\ndata: {response.model_dump_json()}\n\n"

        if usage is not None:
            try:
                cost = RequestCost(
                    tokens_in=usage.input_tokens,
                    tokens_out=usage.output_tokens,
                    model=llm_client.model_name,
                    cost=calculate_cost(
                        usage.input_tokens, usage.output_tokens, llm_client.model_name
                    ),
                    prompt_version=llm_client.prompt_version,
                )
            except ValueError:
                logger.warning(
                    "skipping cost event: unrecognized model %r", llm_client.model_name
                )
            else:
                logger.info("request_cost", extra={"request_cost": cost.model_dump()})
                yield f"event: cost\ndata: {cost.model_dump_json()}\n\n"
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
