# codesage-service

Microservicio FastAPI que recibe un fragmento de código + una pregunta y
responde en streaming (SSE) con un análisis estructurado: resumen,
complejidad, posibles bugs y sugerencia.

## Requisitos

- Python 3.11+

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

pip install -e ".[dev]"
cp .env.example .env        # y completa ANTHROPIC_API_KEY
```

## Correr el servidor

```bash
uvicorn app.main:app --reload
```

- `GET /health` - healthcheck
- `POST /explain` - recibe `{code, question}` y responde vía SSE
  (`text/event-stream`), streameando la respuesta real del LLM. Emite un
  evento por campo (`resumen`, `complejidad`, `posibles_bugs`, `sugerencia`),
  validado como `ExplainResponse` al cerrar el stream (`event: done`), seguido
  de un evento `cost` con el costo calculado del request. Reintenta
  automáticamente con backoff exponencial ante errores 429/5xx del proveedor.

## Tests

```bash
pytest
```

## Roadmap

CodeSage es el proyecto central de un roadmap de transición a AI Engineer en
4 fases. El detalle completo (checklist de estudio + entregable) vive en
[`blueprint/roadmap.md`](blueprint/roadmap.md).

| Fase | Foco | Estado |
| --- | --- | --- |
| 1 | Python + fundamentos de LLMs: streaming SSE, structured output, retries, costos, prompts versionados | Completa |
| 2 | RAG end to end: chunking código/docs, hybrid search con pgvector, re-ranking, citación de fuente | En progreso |
| 3 | Agentes + evals + observabilidad: tool use, suite de evals, Langfuse, prompt injection | Pendiente |
| 4 | Producción: deploy en AWS con CI/CD, semantic caching, model routing | Pendiente |

## Estado actual (Fase 1 - completa)

Las cinco features del build plan de Fase 1 están implementadas: streaming
SSE real contra el LLM, salida estructurada validada por campo con Pydantic,
retries con backoff exponencial, tracking de costo por request, y tres
versiones de prompt (v1-v3, seleccionable con la variable de entorno
`PROMPT_VERSION`; ver `app/prompts/CHANGELOG.md`). Se construyó vía el
workflow de [AI Blueprint](https://ai-blueprint.dev) con `/feature`.

Fase 2 (RAG sobre un repositorio real) está en progreso; ver
[`blueprint/build-plan.md`](blueprint/build-plan.md) para el detalle de items.
