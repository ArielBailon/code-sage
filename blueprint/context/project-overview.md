# codesage-service - Project Overview

> FastAPI microservice that explains a code snippet + question via real SSE streaming, with a Pydantic-validated structured response.

## Problem

There's no fast, explainable way to understand an unfamiliar code snippet: what
it does, how complex it is, where it might break, and how to improve it.
CodeSage exposes that explanation as a service, streamed, with structured
output that's verifiable rather than free-form text.

## Users

- **Portfolio reviewers / interviewers** - evaluate the project as a technical
  demo: real streaming, structured output, resilience to API failures, cost
  control, and prompt versioning in a production-shaped setup.
- **The author** - uses it as the centerpiece of an AI Engineer transition
  portfolio.

No access tiers; single-consumer API, no auth in this phase.

## Features

1. **Streaming SSE real** - `/explain` connected to the real LLM, streaming the
   response over SSE end to end (mechanism proven, not yet field-structured).
2. **Structured output con Pydantic** - the streamed response is emitted as
   per-field SSE events and validated as a whole against `ExplainResponse` when
   the stream closes.
3. **Rate limiting y retries con backoff exponencial** - automatic retries with
   exponential backoff on provider 429/5xx errors.
4. **Tracking de costo por request** - cost computed from input/output tokens x
   model price, exposed in the response or logs.
5. **Prompts versionados (v1-v3) con changelog** - three prompt iterations with
   `app/prompts/CHANGELOG.md` explaining the reason for each change.

## Data model

No user or history persistence in this phase. The API contract and the
per-request log are the only concrete shapes.

### ExplainRequest

- `code` (str) - the code snippet to explain
- `question` (str) - the user's question about it

### ExplainResponse

- `resumen` (str) - summary of what the code does
- `complejidad` (str) - complexity assessment
- `posibles_bugs` (list[str]) - potential bugs or edge cases
- `sugerencia` (str) - improvement suggestion

> Streamed as one SSE event per field (`event: resumen`, `event: complejidad`,
> `event: posibles_bugs`, `event: sugerencia`), each independently validatable;
> the full object is validated against this schema when the stream closes.
> Locked shape - feature 2 depends on it, already scaffolded in `app/models.py`.

### Request cost log

Not a database row - a log line (or response field) per request, so prompt
versions can be compared later.

- `tokens_in` (int)
- `tokens_out` (int)
- `model` (str) - model used
- `cost` (float) - `tokens_in`/`tokens_out` x model price
- `prompt_version` (str) - which of v1/v2/v3 produced the response

## Tech stack

- **Python 3.11+ / FastAPI** - async HTTP service, `StreamingResponse` for SSE
- **Pydantic** - request/response schema validation, including the streamed
  `ExplainResponse` shape
- **httpx / Anthropic SDK** - LLM provider calls
- **tenacity** - retry/backoff logic for rate limits and transient failures
- **pytest** - test suite (test gate is active - see `coding-standards.md`)

## Monetization

Not a commercial product in this phase. Its value is as a portfolio piece
(CodeSage) and applied practice on the AI Engineer roadmap.

## UI/UX

No visual interface - this is a backend microservice. The "experience" to
optimize is the API consumer's: fast time-to-first-byte (streaming), clear
errors, and a stable, predictable JSON contract.

- `POST /explain` - `{code, question}` in, SSE stream of `ExplainResponse`
  fields out
- `GET /health` - healthcheck

## Deployment

> TODO - out of scope for Phase 1. Validated locally (`uvicorn` + automated and
> manual tests). Deployment is planned as a later phase once this build plan is
> closed.
