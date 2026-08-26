# Findings

> **Generated file.** The findings ledger: review findings raised by `/audit`
> against the work in progress, each with a durable ID, severity (P0-P3), and
> status. `/implement` marks repaired findings `fixed`, a later `/audit` pass
> moves them to `closed`, and `/complete` refuses to merge while any P0 or P1
> finding is `open` or `fixed`, then archives resolved findings with the work
> and resets this file.

### F-02 [P2] open - Default PROMPT_VERSION falls back to v1, the version documented as prone to malformed output

**File:** app/main.py:26; .env.example:3
**Found:** 2026-08-25 by /audit (scope: full; lens: quality)
**Why it matters:** `app/prompts/CHANGELOG.md` documents that v1 (and v2) can drift from the required four-line contract - wrapped complexity sentences, generic bug lists, and leading preambles - and that v3 was written specifically to stop preambles that break `FieldStreamParser` mid-stream (it expects the first line to already be `resumen: ...`). Both `app/main.py`'s `os.getenv("PROMPT_VERSION", "v1")` fallback and the checked-in `.env.example` default to v1, so a fresh setup runs on the least reliable prompt version and is more likely to hit the `event: error` path than necessary.
**Suggested fix:** Default `PROMPT_VERSION` to `v3` in both `app/main.py` and `.env.example`, unless v1 is deliberately kept as the default for side-by-side comparison purposes.
**Resolution:**

### F-03 [P3] open - No length bound on ExplainRequest.code/question

**File:** app/models.py:4-6
**Found:** 2026-08-25 by /audit (scope: full; lens: performance)
**Why it matters:** Cost is billed per token from provider-reported usage, but `ExplainRequest` accepts `code` and `question` of unbounded length. An oversized payload directly drives token cost and can exceed the model's context window, with no pre-flight validation - the only guard is the provider itself rejecting the request after it's already been sent.
**Suggested fix:** Add a reasonable `max_length` (via Pydantic `Field`) to `code` and `question`, so oversized requests are rejected with a 422 before an LLM call is made.
**Resolution:**
