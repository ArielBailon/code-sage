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

## Estado actual

Las cinco features del build plan están implementadas: streaming SSE real
contra el LLM, salida estructurada validada por campo con Pydantic, retries
con backoff exponencial, tracking de costo por request, y tres versiones de
prompt (v1-v3, seleccionable con la variable de entorno `PROMPT_VERSION`; ver
`app/prompts/CHANGELOG.md`). Se construyó vía el workflow de
[AI Blueprint](https://ai-blueprint.dev) con `/feature`.
