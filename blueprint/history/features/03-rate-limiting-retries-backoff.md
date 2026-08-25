# Feature: Rate limiting y retries con backoff exponencial

**From build-plan:** feature 3
**Status:** complete

## Goal

The Anthropic API can reject or fail a request transiently (429 rate limit,
5xx server errors). Right now any such failure either crashes the `/explain`
SSE generator mid-stream or propagates as an unhandled exception. This feature
adds automatic retries with exponential backoff around the LLM call, and makes
sure a failure that survives retries reaches the client as a clean SSE error
event instead of a broken connection.

## In scope

- Retry the Anthropic call automatically on 429 (rate limit) and 5xx (server
  error) responses, using exponential backoff between attempts.
- Only retry before any content has been yielded to the caller. Once a chunk
  of the explanation has already been streamed out, a later failure must not
  trigger a silent re-stream (that would duplicate or corrupt output the
  client already received) - it propagates instead.
- A bounded number of attempts; once exhausted, the original provider error is
  raised to the caller.
- `/explain` catches that provider error and emits a client-safe
  `event: error` SSE frame (same shape as the existing JSON/validation error
  path), instead of letting the exception crash the stream.

## Out of scope

- Retrying 4xx errors other than 429 (bad request, auth, etc. are not
  transient - fail fast).
- Cost tracking (build-plan item 4) and prompt versioning (item 5).
- Circuit breaking, jitter tuning, or making retry count/backoff configurable
  via environment variables - fixed sensible defaults for now.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Retry with backoff in `LLMClient.stream_explanation`** - wrap
  the `messages.stream(...)` call with `tenacity` so a retryable failure
  (`anthropic.APIStatusError` with `status_code == 429` or `>= 500`) retries
  the connection with exponential backoff, up to a fixed max attempts, then
  reraises the original error once exhausted. Track whether any chunk has
  already been yielded and skip retrying (reraise immediately) if a failure
  happens after streaming has started.
  *Done when:* a unit test that makes the fake Anthropic client raise a 429
  once then succeed shows the retried call still yields the expected chunks;
  a second test shows an error occurring after the first chunk was yielded
  propagates without a retry; a third test shows a non-retryable error (e.g.
  400) propagates immediately with no retry attempted.
- [x] **Step 2 - Surface exhausted-retry errors as an SSE error event** - in
  `app/main.py`'s `_explain_event_stream`, catch `anthropic.AnthropicError` in
  addition to the existing `(json.JSONDecodeError, ValidationError)` and yield
  `event: error` with a client-safe message (don't leak the raw SDK exception
  string - use a generic "LLM provider request failed" message).
  *Done when:* a `TestClient` request to `/explain`, with the LLM client
  mocked to always raise a retryable `anthropic.APIStatusError`, receives a
  200 response whose SSE body contains a well-formed `event: error` frame
  instead of the connection dropping with an unhandled exception.

## Files / areas

- `app/llm_client.py` - retry/backoff wrapper around the stream call.
- `app/main.py` - broaden the exception handling in `_explain_event_stream`.
- `tests/test_llm_client.py` - retry, no-retry-after-yield, and non-retryable
  cases.
- `tests/test_main.py` - end-to-end SSE error-event case.
- `tenacity` is already a declared dependency (`pyproject.toml`); no new deps.

## Data / contracts

- No change to `ExplainResponse` or the per-field SSE event contract.
- New error-path contract (matches the existing validation-error shape):
  `event: error` / `data: {"error": "<message>"}`, sent as the terminal event
  of the stream when the provider call ultimately fails.

## Testing

- Test runner is `pytest` (declared in `AGENTS.md`), so this is a gate: both
  steps add logic (retry predicate, retry loop, error translation) and each
  ships tests in the same step.
- Construct fake `anthropic.APIStatusError` / `RateLimitError` instances in
  tests via `httpx.Response(status_code=..., request=httpx.Request(...))`
  passed as the `response` argument - no real network call needed.
- Keep retry tests fast: use small backoff bounds (or monkeypatch
  `tenacity`'s sleep/wait) so the suite doesn't actually sleep for seconds.
- Step 1: unit tests directly on `LLMClient.stream_explanation` (extends
  `tests/test_llm_client.py`'s existing fake-client pattern).
- Step 2: an integration-style test via FastAPI's `TestClient` against
  `/explain` (extends `tests/test_main.py`), with `llm_client` swapped for a
  fake that raises after retries are exhausted.

## Notes for the AI

- All LLM calls go through `app/llm_client.py` per `coding-standards.md` -
  keep the retry logic there, not in `main.py`. `main.py` only translates the
  final error into an SSE event.
- `stream_explanation` is an async generator; tenacity's `AsyncRetrying` can
  be driven with `async for attempt in AsyncRetrying(...): with attempt: ...`
  inside it. The "don't retry after a chunk was yielded" rule needs the retry
  predicate to see a mutable "have we yielded yet" flag, not just the
  exception type.
- Match the existing SSE frame format (`f"event: {name}\ndata:
  {json.dumps(value)}\n\n"`) for the new error event so parsing stays
  consistent for any client.
