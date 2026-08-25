import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.models import ExplainRequest

app = FastAPI(title="codesage-service")

_HARDCODED_EVENTS = [
    {"resumen": "La funcion recorre una lista y suma sus elementos."},
    {"complejidad": "O(n)"},
    {
        "posibles_bugs": ["No valida que la lista no este vacia"],
        "sugerencia": "Usar sum(lista) en vez de un bucle manual.",
    },
]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _explain_event_stream() -> AsyncIterator[str]:
    for event in _HARDCODED_EVENTS:
        yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(0.1)


@app.post("/explain")
async def explain(request: ExplainRequest) -> StreamingResponse:
    return StreamingResponse(
        _explain_event_stream(),
        media_type="text/event-stream",
    )
