# Feature: Tracking de costo por request

**From build-plan:** feature 4
**Status:** complete

## Goal

Every `/explain` call spends real Anthropic tokens. Right now nothing records
how many, or what that cost. This feature captures the real input/output
token counts the Anthropic API reports for a completed request, turns them
into a dollar cost using the model's per-token price, and records it both as
a structured log line (the durable record the project overview says will let
prompt versions be compared once feature 5 adds v2/v3) and as a terminal SSE
event on the response (so the cost is visible to whoever is calling
`/explain`, not just in server logs).

## In scope

- `calculate_cost(tokens_in, tokens_out, model)` in `app/cost.py`, using a
  small per-model price table (input/output $ per million tokens). Raises for
  a model it doesn't recognize, rather than silently returning a wrong number.
- Real usage from the Anthropic SDK (`stream.get_final_message().usage` -
  `input_tokens`/`output_tokens`), not an estimate - captured per request,
  never stored on the shared `LLMClient` instance (it serves every request,
  so instance-level state would race across concurrent calls).
- A `RequestCost` model (`app/models.py`) matching the project overview's
  contract: `tokens_in`, `tokens_out`, `model`, `cost`, `prompt_version`.
- `/explain` logs the `RequestCost` as a structured log line and emits it as
  a terminal `event: cost` SSE frame, after `event: done`, only when the
  request actually completed (see Out of scope).

## Out of scope

- Cost tracking for a request that errors out (rate-limit exhaustion,
  validation failure) - only a successfully completed explanation produces a
  cost record. Retried-then-succeeded requests still cost exactly what the
  final successful attempt used, since usage comes from the one completed
  message.
- `prompt_version` is hardcoded to `"v1"` for now - real per-version tracking
  needs feature 5 (prompt versioning) to exist first; this feature just
  reserves the field so that later feature doesn't have to touch the cost
  contract.
- Persisting cost records anywhere queryable (database, file) - "log line"
  per the overview means the process's log output, not a store.
- Pricing table entries beyond the models this project can realistically be
  pointed at (`MODEL_NAME` env var) - not every model Anthropic offers.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - `calculate_cost` in `app/cost.py`** - replace the
  `NotImplementedError` stub with a real calculation: a `MODEL_PRICING` table
  of `(input $/1M tokens, output $/1M tokens)` for the models this project
  can be configured to use (at minimum `claude-sonnet-5`, the project's
  default `MODEL_NAME`), and `calculate_cost(tokens_in, tokens_out, model)`
  returning `(tokens_in / 1_000_000) * input_price + (tokens_out / 1_000_000)
  * output_price`. Raise `ValueError` for a model not in the table.
  *Done when:* unit tests cover a known model with a hand-checked expected
  cost, the zero-tokens edge case (cost `0.0`), and an unrecognized model
  raising `ValueError`.
- [x] **Step 2 - surface real token usage from `LLMClient.stream_explanation`**
  - add an optional `on_usage: Callable[[anthropic.types.Usage], None] | None
  = None` keyword parameter. Once the `text_stream` loop finishes (all text
  yielded, still inside the open `async with` block from feature 3's retry
  work), call `await stream.get_final_message()` and pass its `.usage` to
  `on_usage` if it was given. No new instance attribute on `LLMClient` - the
  callback is the only channel, so nothing is shared across concurrent
  requests.
  *Done when:* a unit test (extending the existing fake-client pattern in
  `tests/test_llm_client.py`) drives a fake stream with a fake
  `get_final_message()` and asserts the `on_usage` callback receives the
  expected `input_tokens`/`output_tokens` exactly once, after the text
  chunks; a second test confirms omitting `on_usage` changes nothing
  (existing tests keep passing unmodified).
- [x] **Step 3 - wire cost into `/explain`** - add `RequestCost` to
  `app/models.py`. In `app/main.py`'s `_explain_event_stream`, pass an
  `on_usage` callback into `stream_explanation` that captures the usage
  locally (a plain local variable/dict inside the generator call, not module
  or client state), and after the `event: done` frame, when usage was
  captured, build a `RequestCost` (via `calculate_cost` and the hardcoded
  `"v1"` prompt version), log it with the standard `logging` module, and
  yield it as `event: cost\ndata: <RequestCost JSON>\n\n`. Guard the
  `calculate_cost` call: if `MODEL_NAME` is ever misconfigured to a model
  outside the pricing table, that must not crash the stream after `done` has
  already been sent (the response already succeeded from the client's point
  of view) - catch the `ValueError`, log it as a warning, and skip the cost
  event instead of raising.
  *Done when:* a `TestClient` test against `/explain` (extending
  `tests/test_main.py`'s fake-stream pattern, updated to accept the new
  `on_usage` kwarg) shows the response contains an `event: cost` frame with
  the expected `tokens_in`/`tokens_out`/`cost`/`model`/`prompt_version`
  fields, appearing after `event: done`; a second test (the existing
  incomplete/error-path tests, updated for the new kwarg) confirms no
  `event: cost` frame appears when the request doesn't complete; a third
  test simulates an unrecognized model and confirms the response still ends
  cleanly with `event: done` and no `event: cost` frame, instead of an
  unhandled exception.

## Files / areas

- `app/cost.py` - real `calculate_cost` implementation and pricing table.
- `app/llm_client.py` - `on_usage` callback parameter on `stream_explanation`.
- `app/models.py` - new `RequestCost` model.
- `app/main.py` - wiring: capture usage, compute cost, log, emit `event: cost`.
- `tests/test_cost.py` - new, for `calculate_cost`.
- `tests/test_llm_client.py` - `on_usage` callback tests.
- `tests/test_main.py` - end-to-end cost-event test; existing fakes updated
  to accept the new keyword.

## Data / contracts

- `RequestCost` (new, `app/models.py`): `tokens_in: int`, `tokens_out: int`,
  `model: str`, `cost: float`, `prompt_version: str`. Matches the "Request
  cost log" shape already locked in `project-overview.md`.
- New terminal SSE event, additive to the existing contract: `event: cost` /
  `data: <RequestCost JSON>`, sent once, only after `event: done`, only on a
  successfully completed explanation.
- No change to `ExplainResponse` or the existing per-field / `done` / `error`
  events.

## Testing

- Test runner is `pytest` (declared in `AGENTS.md`), so this is a gate: all
  three steps add logic (pricing math, usage capture, cost wiring) and each
  ships tests in the same step.
- `tests/test_cost.py` is a new file, one `test_*.py` per module per
  `coding-standards.md`.
- Step 2's fake stream needs a fake `get_final_message()` returning an object
  with a `.usage` attribute exposing `.input_tokens`/`.output_tokens` (a
  small stand-in is enough - no need to construct a real `anthropic.types.
  Message`).
- Step 3's existing fakes in `tests/test_main.py` (`_fake_stream_explanation`,
  `_fake_stream_incomplete`, `_fake_stream_provider_failure`) all need an
  `on_usage` parameter added to their signatures (accepting it and calling it
  where relevant) since `main.py` will now always pass that keyword.

## Notes for the AI

- Reuse `anthropic.types.Usage` (the SDK's own type, exposed as
  `message.usage` from `get_final_message()`) instead of inventing a
  duplicate dataclass - it already has `input_tokens`/`output_tokens`.
- `get_final_message()` after `text_stream` is already exhausted doesn't
  trigger a second network round trip: `text_stream` is itself driven by
  consuming the same underlying raw event stream, so by the time all text
  deltas have been yielded, the raw stream is already fully consumed and the
  final message snapshot is already assembled.
- Don't disturb feature 3's retry/backoff logic - the `on_usage` call must
  happen after the `async for text in stream.text_stream` loop, still inside
  the same `async with` block, so it runs only on the attempt that actually
  completed (retries on earlier attempts never reach this line).
- All LLM-facing logic stays in `app/llm_client.py` per `coding-standards.md`;
  `main.py` only turns the callback's data into a `RequestCost`, a log line,
  and an SSE event - it does not know about the Anthropic SDK's `Usage` type
  itself beyond passing it through.
