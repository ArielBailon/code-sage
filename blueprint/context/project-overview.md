# codesage-service - Project Overview

<!-- blueprint:source-hash 3d1e44a722b34c0e47fa511f70cedf3b70cae86fff1f990a379d79939a1a2bd9 -->

> FastAPI microservice that explains a code snippet + question via real SSE streaming with a Pydantic-validated structured response, now extending into retrieval-augmented generation (RAG) over a real open source repository.

## Problem

There's no fast, explainable way to understand an unfamiliar code snippet: what
it does, how complex it is, where it might break, and how to improve it.
CodeSage exposes that explanation as a service, streamed, with structured
output that's verifiable rather than free-form text. Phase 2 extends this to
answering questions grounded in a real repository's code and docs, not just an
isolated snippet.

## Users

- **Portfolio reviewers / interviewers** - evaluate the project as a technical
  demo: real streaming, structured output, resilience to API failures, cost
  control, prompt versioning, and (from Phase 2) a working RAG pipeline with
  hybrid search, re-ranking, and source citation.
- **The author** - uses it as the centerpiece of an AI Engineer transition
  portfolio, built in phases (full roadmap in `blueprint/roadmap.md`).

No access tiers; single-consumer API, no auth in this phase.

## Features

**Phase 1 (complete, archived in `blueprint/history/features/`):**

1. **Streaming SSE real** - `/explain` connected to the real LLM, streaming
   the response over SSE end to end.
2. **Structured output con Pydantic** - the streamed response is emitted as
   per-field SSE events and validated as a whole against `ExplainResponse`
   when the stream closes.
3. **Rate limiting y retries con backoff exponencial** - automatic retries
   with exponential backoff on provider 429/5xx errors.
4. **Tracking de costo por request** - cost computed from input/output tokens
   x model price, exposed in the response or logs.
5. **Prompts versionados (v1-v3) con changelog** - three prompt iterations
   with `app/prompts/CHANGELOG.md` explaining the reason for each change.

**Phase 2 (active - RAG end to end):**

6. **Ingesta y chunking especializado** - clone a real open source repo (5k+
   lines of code + docs); chunk code by function/class and docs semantically,
   documenting why the two need different strategies.
7. **Hybrid search con pgvector** - retrieval combining semantic search
   (pgvector) with keyword search (function name, file name).
8. **Re-ranking de resultados** - reorder retrieval results before they're
   passed to the LLM for generation.
9. **Citación de fuente exacta** - every generated answer cites the file and
   line it came from.
10. **Caso documentado de "RAG que falló"** - a real retrieval/generation
    failure, how it was diagnosed, and the fix applied.
11. **Demo y post de cierre de Fase 2** - a deployed demo of the RAG pipeline
    plus a writeup of the chunking decisions.

**Phase 5 (extra, after Phase 4 - not yet started):**

12. **Cliente OpenAI con streaming y retries** - a second provider client
    mirroring the Anthropic client's interface (streaming + usage reporting)
    with the same retry/backoff handling, plus OpenAI pricing in cost
    calculation.
13. **Fallback automático entre proveedores** - if the primary provider
    exhausts retries without having yielded any chunk yet, fall back
    automatically to the secondary provider (OpenAI <-> Anthropic) for that
    same request; provider selection configurable via env vars.

## Data model

### Request cost log (Phase 1)

Not a database row - a log line (or response field) per request.

- `tokens_in` (int)
- `tokens_out` (int)
- `model` (str) - model used
- `cost` (float) - `tokens_in`/`tokens_out` x model price
- `prompt_version` (str) - which of v1/v2/v3 produced the response

### Chunk (Phase 2)

Persisted in Postgres with pgvector. One row per ingested chunk of the target
repository.

- `id` (uuid/int) - primary key
- `source_path` (str) - file path within the ingested repo
- `chunk_type` (str) - `code` or `doc`, drives which chunking strategy produced it
- `start_line` / `end_line` (int) - exact source location, used for citation
- `content` (str) - the chunked text
- `embedding` (vector) - pgvector embedding of `content`
- `symbol_name` (str, nullable) - function/class name, when `chunk_type` is `code`; used by keyword search

> Locked shape - features 7, 8, and 9 all depend on `source_path` +
> `start_line`/`end_line` being accurate for citation, and on `chunk_type` +
> `symbol_name` for hybrid search.

## Tech stack

- **Python 3.11+ / FastAPI** - async HTTP service, `StreamingResponse` for SSE
- **Pydantic** - request/response schema validation, including the streamed
  `ExplainResponse` shape
- **httpx / Anthropic SDK** - LLM provider calls
- **tenacity** - retry/backoff logic for rate limits and transient failures
- **pytest** - test suite (test gate is active - see `coding-standards.md`)
- **Postgres + pgvector** (Phase 2) - vector store for ingested chunks and their embeddings
- **Embedding model** (Phase 2) - generates vectors for chunked code and documentation

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

> TODO - Phase 2's ingestion/retrieval endpoints (querying the ingested
> repository) are not yet named; define them when `/feature` specs item 6.

## Deployment

Out of scope through Phase 3. Phase 1 and Phase 2 are validated locally
(`uvicorn` + local Postgres/pgvector + automated and manual tests). Phase 2's
deliverable includes a deployed demo of the RAG pipeline (not production
infrastructure). Formal deployment to AWS with CI/CD is Phase 4's deliverable
(see `blueprint/roadmap.md`).

> TODO - Phase 4 owns the real deployment target, build/start commands, env
> vars, and health checks for production.

## Open questions

> None currently blocking. Phase 1's original deliverable also listed a
> provider fallback (OpenAI <-> Anthropic) that was deferred rather than
> shipped; it now lives as Phase 5 (features 12-13 above), after Phase 4.
