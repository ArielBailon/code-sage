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
  (`text/event-stream`). Por ahora emite eventos con datos hardcodeados
  para validar el mecanismo de streaming.

## Tests

```bash
pytest
```

## Estado actual

Este es un scaffold inicial. Aún no implementado: llamada real al LLM,
retries/backoff, cálculo de costo real, y prompts v2/v3. Se construyen
después vía el workflow de [AI Blueprint](https://ai-blueprint.dev) con
`/feature`.
