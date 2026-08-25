# Feature: Structured output con Pydantic

**From build-plan:** feature 2
**Status:** complete

## Goal

Turn the raw text stream from feature 1 into a real structured response: the
model emits its answer as four ordered lines (one per `ExplainResponse` field),
each line is parsed and pushed to the client as its own named SSE event as
soon as it's complete, and the full accumulated object is validated against
`ExplainResponse` when the stream closes.

## In scope

- Update `PROMPT_V1` to instruct the model to answer as exactly four lines, in
  a fixed order, each `"<field>: <JSON value>"` - no prose before, between, or
  after them.
- A new parser (`app/response_parser.py`) that consumes raw text chunks as
  they arrive, and as soon as a line is complete, decodes its JSON value and
  reports it - independent of how the underlying chunk boundaries happen to
  split the text.
- Wire `/explain` to emit one named SSE event per completed field
  (`event: resumen`, `event: complejidad`, `event: posibles_bugs`,
  `event: sugerencia`), then a final `event: done` with the complete,
  Pydantic-validated `ExplainResponse` object once the stream ends. A parse or
  validation failure is surfaced as `event: error` instead of an unhandled
  exception.

## Out of scope

- Rate limit handling and retry/backoff on the provider call itself - feature 3.
  A malformed/incomplete model *response* still gets minimal, non-retrying
  error surfacing in this feature (see below); that's a different failure mode
  than a provider-level rate limit or network error.
- Cost tracking - feature 4. Prompt versions v2/v3 - feature 5.
- Changes to `ExplainRequest`/`ExplainResponse` themselves (`app/models.py`) -
  they're already correct; this feature only adds a consumer that validates
  against `ExplainResponse`.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Structured `PROMPT_V1`** - rewrite the prompt so it instructs
  the model to answer with exactly these four lines, in this order, nothing
  else:

      resumen: <JSON string>
      complejidad: <JSON string>
      posibles_bugs: <JSON array of strings>
      sugerencia: <JSON string>

  *Done when:* the diff reads clearly as a prompt-text change; no logic added,
  no test required (matches the Testing gate's "what not to test" - this isn't
  parseable/assertable code, it's prompt text); `pytest` stays green (existing
  `llm_client` tests only assert `code`/`question` substrings, not exact
  prompt text, so they're unaffected).
- [x] **Step 2 - `FieldStreamParser`** - a class in `app/response_parser.py`
  with two methods:
  - `feed(chunk: str) -> list[tuple[str, object]]` - appends `chunk` to an
    internal buffer, splits off every complete (`\n`-terminated) line, and for
    each line matching a known field name (`resumen`, `complejidad`,
    `posibles_bugs`, `sugerencia`), `json.loads()`s the value after the
    `:` and returns it as `(field_name, value)`. Unknown field names are
    ignored. Returns `[]` when no line completed.
  - `finalize() -> ExplainResponse` - constructs `ExplainResponse(**collected_fields)`
    from everything collected so far and returns it (raises
    `pydantic.ValidationError` if a field is missing or malformed).

  A line whose value is malformed JSON should raise `json.JSONDecodeError`
  from `feed()` itself, not be silently dropped - Step 3 catches it.
  *Done when:* unit tests cover (a) a full multi-line buffer fed in one
  `feed()` call returns all four fields in order, (b) a single line's JSON
  value split across two `feed()` calls returns nothing until the line
  completes, then returns it correctly, (c) `finalize()` after all four
  fields returns a valid `ExplainResponse` equal to the fed values, (d)
  `finalize()` with a missing field raises `pydantic.ValidationError`, (e)
  `feed()` with a malformed JSON value raises `json.JSONDecodeError`. `pytest`
  green, no real network call.
- [x] **Step 3 - Wire `/explain` to the parser** - in `_explain_event_stream`,
  create one `FieldStreamParser` per request; for each raw chunk from
  `llm_client.stream_explanation`, call `parser.feed(chunk)` and yield
  `event: <field>\ndata: <json.dumps(value)>\n\n` for every field it returns.
  After the LLM stream ends, call `parser.feed("\n")` once more to flush a
  final line that didn't end in a newline, emitting its event the same way.
  Then call `parser.finalize()`: on success, yield
  `event: done\ndata: <response.model_dump_json()>\n\n`; on
  `json.JSONDecodeError` or `pydantic.ValidationError` (from either `feed` or
  `finalize`), yield `event: error\ndata: {"error": "<message>"}\n\n` instead
  of letting the exception propagate. *Done when:* an endpoint test
  (`TestClient` + a monkeypatched `app.main.llm_client.stream_explanation`
  yielding a canned multi-line text stream) asserts the SSE body contains
  `event: resumen`, `event: complejidad`, `event: posibles_bugs`,
  `event: sugerencia`, and `event: done` with a data payload that round-trips
  through `ExplainResponse`; a manual `curl -N` against the running dev server
  with a real `ANTHROPIC_API_KEY` shows the same five named events with real
  model content; `pytest` stays green.

## Files / areas

- `app/prompts/v1.py` - structured, four-line prompt format
- `app/response_parser.py` - new, `FieldStreamParser`
- `app/main.py` - `/explain` emits named per-field events + `done`/`error`
- `tests/test_response_parser.py` - new, unit tests for the parser
- `tests/test_main.py` - new, endpoint test with a monkeypatched `LLMClient`

## Data / contracts

- **New, locked SSE contract for `/explain`** (this replaces feature 1's
  throwaway `{"chunk": ...}` format):
  - `event: resumen` -> `data: "<string>"`
  - `event: complejidad` -> `data: "<string>"`
  - `event: posibles_bugs` -> `data: [<string>, ...]`
  - `event: sugerencia` -> `data: "<string>"`
  - `event: done` -> `data: <ExplainResponse JSON>` (the full validated object)
  - `event: error` -> `data: {"error": "<message>"}` (parse/validation failure)

  Feature 4 (cost tracking) will likely extend the `done` payload or add a
  sibling event - not decided here, but the five events above are the stable
  base later features build on.
- `ExplainResponse` (`app/models.py`) - unchanged, now actually used to
  validate the model's real output for the first time.

## Testing

- Test gate is active (`pytest` declared in `AGENTS.md`).
- In-scope logic: `FieldStreamParser.feed`/`finalize` (pure parsing/validation
  over strings - exactly the "parsers, formatters, validators" the gate
  targets) gets the five unit tests listed in Step 2.
- The `/explain` wiring in Step 3 is tested two ways: a mocked-LLM endpoint
  test (`TestClient`, no network) proves the routing/event logic; a manual
  `curl -N` against the real provider proves it end to end, per the "API
  Verification" convention (this is the same split feature 1 used).
- `tests/test_health.py` and `tests/test_llm_client.py` must keep passing.

## Notes for the AI

- Keep `FieldStreamParser` free of any FastAPI/Anthropic imports - it's pure
  string/JSON/Pydantic logic, which is exactly why it's unit-testable without
  mocking the SDK.
- Reuse `feed()` for the trailing-line flush (`parser.feed("\n")`) instead of
  writing separate flush logic in `finalize()` - one code path for "a line is
  complete" avoids duplicating the parsing rules.
- To monkeypatch the endpoint test, patch the `stream_explanation` method on
  the module-level `app.main.llm_client` instance (or the instance itself)
  rather than patching the `anthropic` package - `main.py` never imports
  `anthropic` directly, only `LLMClient`.
- `json.dumps(value)` on a value that's already been through `json.loads()`
  round-trips safely for both `str` and `list[str]` fields.
