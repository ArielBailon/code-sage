## Title

Default to the hardened prompt version and bound request size

**Type:** Fix
**Fixes:** F-02, F-03

## The problem

Two small, independent gaps from the last full audit:

1. **F-02** - `app/main.py`'s `os.getenv("PROMPT_VERSION", "v1")` fallback and
   `.env.example`'s `PROMPT_VERSION=v1` both default to v1. `app/prompts/CHANGELOG.md`
   documents that v1 (and v2) can drift from the required four-line contract
   - wrapped complexity sentences, generic bug lists, leading preambles - and
   that v3 was written specifically to stop preambles that break
   `FieldStreamParser` mid-stream (it expects the first line to already be
   `resumen: ...`). A fresh setup runs on the least reliable prompt version by
   default.
2. **F-03** - `ExplainRequest.code` and `.question` (`app/models.py`) have no
   length bound. Cost is billed per token from provider-reported usage, so an
   oversized payload directly drives cost and can exceed the model's context
   window, with no pre-flight rejection - the only guard today is the
   provider itself failing the request after it's already been sent.

## The fix

1. Change the `PROMPT_VERSION` fallback in `app/main.py` from `"v1"` to
   `"v3"`, and update `.env.example`'s `PROMPT_VERSION=v1` to
   `PROMPT_VERSION=v3`. Must not change the `get_prompt`/`PROMPT_VERSIONS`
   mechanism itself - v1 and v2 stay selectable, just not the default.
2. Add a `max_length` constraint to `ExplainRequest.code` and
   `ExplainRequest.question` via Pydantic `Field`. Pick a generous but
   concrete bound: 20,000 characters for `code` (comfortably covers a large
   file/snippet) and 2,000 characters for `question`. FastAPI/Pydantic already
   turns a validation failure into a 422, so no endpoint code changes needed.

Must not change `ExplainResponse`, `RequestCost`, or any other model shape.

## Build steps

- [x] Step 1 - default `PROMPT_VERSION` to v3 in `app/main.py` and
      `.env.example`.
      Done when: `main.py`'s fallback and `.env.example` both read
      `PROMPT_VERSION=v3` (or the `os.getenv` default is `"v3"`), v1/v2/v3
      remain independently selectable via the env var, and the existing
      prompt-version tests (`tests/test_prompts.py`,
      `tests/test_llm_client.py`) still pass unchanged since they set the
      version explicitly.
- [x] Step 2 - add `max_length` to `ExplainRequest.code` and `.question` in
      `app/models.py`, plus a focused test in `tests/test_main.py` (or a new
      `tests/test_models.py`) proving an oversized `code`/`question` gets a
      422, and a request at/under the limit still succeeds.
      Done when: the new test passes and the existing `/explain` tests in
      `tests/test_main.py` still pass unchanged.

## Verify

Run `pytest` - all existing tests plus the new length-validation test(s) must
pass. Manually confirm via `curl`/`httpx` against the running dev server that
a `code` longer than the new limit returns `422`, and that a normal-size
request still streams normally.

## Findings

### prompt-version-default-and-request-limits/F-02 [P2] fixed - Default PROMPT_VERSION falls back to v1, the version documented as prone to malformed output

**File:** app/main.py:26; .env.example:3
**Found:** 2026-08-25 by /audit (scope: full; lens: quality)
**Why it matters:** `app/prompts/CHANGELOG.md` documents that v1 (and v2) can drift from the required four-line contract - wrapped complexity sentences, generic bug lists, and leading preambles - and that v3 was written specifically to stop preambles that break `FieldStreamParser` mid-stream (it expects the first line to already be `resumen: ...`). Both `app/main.py`'s `os.getenv("PROMPT_VERSION", "v1")` fallback and the checked-in `.env.example` default to v1, so a fresh setup runs on the least reliable prompt version and is more likely to hit the `event: error` path than necessary.
**Suggested fix:** Default `PROMPT_VERSION` to `v3` in both `app/main.py` and `.env.example`, unless v1 is deliberately kept as the default for side-by-side comparison purposes.
**Resolution:** Fixed via `fix/prompt-version-default-and-request-limits` - defaulted `PROMPT_VERSION` to `v3` in both `app/main.py` and `.env.example`; v1/v2 remain selectable via the env var.

### prompt-version-default-and-request-limits/F-03 [P3] fixed - No length bound on ExplainRequest.code/question

**File:** app/models.py:4-6
**Found:** 2026-08-25 by /audit (scope: full; lens: performance)
**Why it matters:** Cost is billed per token from provider-reported usage, but `ExplainRequest` accepts `code` and `question` of unbounded length. An oversized payload directly drives token cost and can exceed the model's context window, with no pre-flight validation - the only guard is the provider itself rejecting the request after it's already been sent.
**Suggested fix:** Add a reasonable `max_length` (via Pydantic `Field`) to `code` and `question`, so oversized requests are rejected with a 422 before an LLM call is made.
**Resolution:** Fixed via `fix/prompt-version-default-and-request-limits` - added `max_length=20_000` on `code` and `max_length=2_000` on `question`, both enforced by Pydantic/FastAPI as a 422.
