# Feature: Streaming SSE real

**From build-plan:** feature 1
**Status:** complete

## Goal

Connect `POST /explain` to the real Anthropic LLM and stream its response over
SSE end to end, replacing the hardcoded stub. This proves the streaming
mechanism works with a real provider before feature 2 adds structured,
per-field validation on top of it.

## In scope

- `LLMClient.stream_explanation` makes a real streaming call to the Anthropic
  API (async), formatting `PROMPT_V1` with the request's `code` and `question`.
- `POST /explain` calls `LLMClient` instead of the hardcoded event list and
  forwards each text chunk as an SSE `data:` event as it arrives.
- Reading `ANTHROPIC_API_KEY` / `MODEL_NAME` from the environment (`.env` via
  `python-dotenv`), matching `.env.example`.

## Out of scope

- Structured, per-field response validation (`event: resumen`, etc.) against
  `ExplainResponse` - feature 2.
- Rate limit handling and retry/backoff - feature 3. If the provider call
  fails, the stream simply ends/errors for now.
- Cost tracking - feature 4. Prompt versions v2/v3 - feature 5.
- Any change to `ExplainRequest`/`ExplainResponse` validation beyond what
  already exists in `app/models.py`.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Real `LLMClient.stream_explanation`** - implement the async
  generator: build the prompt from `PROMPT_V1.format(code=..., question=...)`,
  open an Anthropic async streaming call (`AsyncAnthropic().messages.stream(...)`)
  using `model_name`/`api_key`, and `yield` each text delta from
  `stream.text_stream`. Accept an optional injected client in `__init__` so the
  Anthropic SDK can be swapped for a fake in tests. *Done when:* a unit test
  with a mocked Anthropic client asserts the prompt is formatted correctly and
  the method yields the mocked chunks in order; `pytest` is green with no real
  network call.
- [x] **Step 2 - Wire `/explain` to the real client** - remove
  `_HARDCODED_EVENTS`/`_explain_event_stream`; construct `LLMClient` from
  `ANTHROPIC_API_KEY`/`MODEL_NAME` (via `python-dotenv`'s `load_dotenv()`), and
  stream its chunks as SSE events (`data: {"chunk": "<text>"}\n\n`) from
  `/explain`. *Done when:* with a real `ANTHROPIC_API_KEY` set, `uvicorn app.main:app`
  running, `POST /explain` with a real code snippet + question returns
  `Content-Type: text/event-stream` and at least 2 discrete `data:` events
  containing real model output (verified with `curl -N`); `pytest` stays green.

## Files / areas

- `app/llm_client.py` - real `stream_explanation` implementation
- `app/main.py` - `/explain` wired to `LLMClient` instead of the hardcoded stub
- `tests/test_llm_client.py` - new, mocked-SDK unit test
- `.env` (local, not committed) - needs a real `ANTHROPIC_API_KEY` for Step 2's manual check

## Data / contracts

- `ExplainRequest`/`ExplainResponse` (`app/models.py`) - unchanged, not yet
  used to validate the streamed output (that's feature 2).
- SSE event shape for this feature is a **temporary, unlocked** wire format:
  `data: {"chunk": "<raw text delta>"}\n\n`. Feature 2 replaces this entirely
  with per-field events (`event: resumen`, `event: complejidad`, ...) - nothing
  here should be treated as load-bearing beyond this feature.

## Testing

- Test gate is active (`pytest` declared in `AGENTS.md`). In-scope logic:
  `LLMClient.stream_explanation`'s prompt formatting and chunk relaying - test
  it with the Anthropic SDK mocked/monkeypatched (per
  `coding-standards.md`'s stack binding), no real API call in the suite.
- The `/explain` endpoint's real-provider integration is not unit-tested (it
  depends on a live external API and a real key) - verify it manually per the
  "API Verification" convention: run the dev server and hit `/explain` with
  `curl -N` or `httpx`, confirming `text/event-stream` and multiple real SSE
  events (Step 2's done-when).
- `tests/test_health.py` must keep passing.

## Notes for the AI

- Use `anthropic.AsyncAnthropic` (async client) since `/explain` is an async
  endpoint streaming into a `StreamingResponse`.
- Model id comes from `MODEL_NAME` env var (`.env.example` defaults to
  `claude-sonnet-5`) - don't hardcode a model string in `llm_client.py`.
- Keep `LLMClient` the single entry point for LLM calls per
  `coding-standards.md` - no direct SDK calls from `app/main.py`.
- A chunk of streamed text can contain newlines; JSON-encode each chunk before
  writing the `data:` line so the SSE framing (`\n\n`-terminated) never breaks.
