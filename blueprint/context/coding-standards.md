# Coding Standards

> Your conventions, tuned to this project by `/onboard`. Review and edit
> directly as the stack evolves.

## Python

- Type hints on all function signatures; no bare `Any` unless truly dynamic
- Pydantic models for every request/response shape crossing an API boundary
  (see `app/models.py`) - no raw dicts in or out of endpoints
- No typechecker configured yet (mypy/pyright); add via `/ci` if wanted

## FastAPI

- Async endpoints (`async def`) by default
- Use `StreamingResponse` with `text/event-stream` for streaming/SSE endpoints,
  not a single buffered response
- All LLM calls go through `app/llm_client.py` - the single entry point where
  retries and backoff live, never call the LLM SDK directly from an endpoint
- Raise `HTTPException` for client-facing errors; don't leak raw exceptions

## File Organization

- App code: `app/`
- Endpoints: `app/main.py` (split into `app/routers/` if it grows past a
  handful of routes)
- Request/response models: `app/models.py`
- Prompts: `app/prompts/` - versioned (`v1.py`, `v2.py`, ...) with changes
  logged in `app/prompts/CHANGELOG.md`
- Tests: `tests/`, one `test_*.py` per module under test

## Naming

- Modules and files: snake_case
- Functions and variables: snake_case
- Classes (including Pydantic models): PascalCase
- Constants: SCREAMING_SNAKE_CASE

## Data & Storage

- Postgres with the pgvector extension, for the `chunks` table used by the
  RAG ingestion pipeline (Phase 2 onward)
- No ORM: raw SQL via `asyncpg`, with a connection pool in
  `app/db/connection.py` (`get_pool()` / `close_pool()`)
- Schema lives in `app/db/schema.sql` (plain SQL, no migration tool); apply
  it manually against the target database when it changes
- Local dev database: `docker-compose.yml` (`pgvector/pgvector` Postgres
  image); connection string via `DATABASE_URL` in `.env`
- Single-consumer service, no auth or multi-tenant scoping yet; revisit this
  note if that changes

## Error Handling

- Use try/except in `app/llm_client.py` and endpoints for calls that can fail
  (LLM API, network)
- Raise `HTTPException` with a client-appropriate status code and message from
  endpoints; don't let raw SDK exceptions reach the client

## Testing

The blueprint installs no test runner; testing is opt-in at the project level,
because the overlay can't know your stack. Adding unit testing is an explicit
setup task the AI can do through the normal workflow, either as a build-plan item
or with `/tests`. The setup should choose the stack-native runner, wire the
scripts or commands, add a small example test, and update the Commands section
of `AGENTS.md`.

When `AGENTS.md` declares a `Verify` command, treat it as the umbrella automated
gate. It combines only the checks this project actually has, in this order when
available: typecheck, tests, then build. The command does not enable an absent
test runner or replace focused evidence. It gives local work and optional CI one
exact command to run. `/ci` owns Verify and CI setup. `/tests` adds the real test
command to Verify when it already exists, but never creates CI only because
testing was configured.

**The opt-in switch is one signal: a `test` command in the Commands section of
`AGENTS.md`.** Declare one and **tests become a gate for logic-bearing steps**,
not an optional extra; leave it out and the loop verifies logic with the evidence
it already uses (run it, a screenshot, the build). Adding the runner is itself a
deliberate step, never a silent mid-step install. This is the single definition
of the switch; the skills and `ai-interaction.md` only point back here.

- **What to test (the scope rule):** pure logic where a wrong answer is possible -
  parsers, formatters, validators, id/slug builders, server actions. These have
  assertable inputs and outputs and real edge cases (empty, missing, malformed).
- **What not to test:** UI components and integration-level surfaces (render or
  export routes, anything driving a real browser or external service). Verify those
  with a screenshot and the build, not brittle unit tests.
- **The gate (when a runner is configured):** a build step that adds in-scope logic
  must ship a passing test in the same reviewable diff. The project's test command
  must be green before the step is approved, before any checkpoint commit, and
  before `/complete` merges. UI and integration-only steps are exempt and ride on
  screenshot plus build evidence.
- **When it's named:** the `/feature` spec's Testing section predicts the coverage,
  `/implement` writes the test with the step, and if a step surfaces logic the spec
  didn't foresee, add a focused test then.
- An empty suite should fail, not pass, so "no tests ran" never looks like "passed".
- Test files live next to source files (for example `feature.test.ts`).
- Run them via the project's test command (see Commands in `AGENTS.md`), not a
  hardcoded tool name.

Stack binding: this project uses pytest (`tests/test_*.py`), with
`unittest.mock` / `monkeypatch` for external dependencies (the Anthropic SDK,
`httpx`) and `pytest`'s `tmp_path`/fixtures where needed. The test command is
declared in `AGENTS.md` (`pytest`), so the test gate above is active: a step
that adds logic (parsers, cost calculation, retry logic, response validation)
ships a passing test in the same diff.

## API Verification

This is an API-only service, no browser UI. Verify endpoint behavior with real
HTTP calls against the running dev server (`curl`, `httpx`, or the FastAPI
`TestClient` in tests) rather than reading the code and assuming it works.
Streaming endpoints (`/explain`) should be checked for the real
`text/event-stream` content type and multiple discrete SSE events, not just a
200 status.

## Code Quality

- No commented-out code unless specified
- No unused imports or variables
- Keep functions under 50 lines when possible

## Comments

Write code that explains itself; comment only what the code cannot say.
Over-commenting is a common AI tell, so resist it.

- Comment the **why**, not the **what**. Delete any comment that restates the code.
- No banner/header blocks, section dividers, or step-by-step narration of obvious
  code. A file does not need a comment announcing each region.
- A comment earns its place only when it captures something the code can't: a
  non-obvious decision, a gotcha or workaround, why a value is what it is, or a
  link to a spec or issue.
- Prefer self-documenting names and small functions over explanatory comments.
- Keep doc comments minimal: a one-line purpose on an exported type or function is
  plenty; don't write JSDoc that just repeats the signature.
- When in doubt, leave the comment out.

## Writing

- No em dashes (U+2014) in generated content: docs, comments, commit messages,
  READMEs, specs. They read as AI-generated.
- Use a hyphen for `term - description` separators; rephrase prose with commas,
  parentheses, or a colon. Avoid en dashes and the ellipsis character too.
