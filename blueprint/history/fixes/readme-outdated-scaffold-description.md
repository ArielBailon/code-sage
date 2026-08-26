## Title

README describes an unimplemented scaffold

**Type:** Fix
**Fixes:** F-01

## The problem

`README.md`'s server-section bullet and its "Estado actual" section still
describe the service as an early scaffold: `/explain` "emite eventos con
datos hardcodeados," and the real LLM call, retries/backoff, cost
calculation, and prompt v2/v3 are listed as "aún no implementado."

All five build-plan features are actually complete and tested:

- Real LLM streaming over SSE (`app/llm_client.py`, `app/main.py`)
- Per-field SSE events validated against `ExplainResponse` (`app/response_parser.py`, `app/models.py`)
- Retries with exponential backoff on 429/5xx (`app/llm_client.py`)
- Per-request cost tracking, emitted as a `cost` SSE event (`app/cost.py`, `app/main.py`)
- Three versioned prompts v1-v3 with a changelog, selectable via `PROMPT_VERSION` (`app/prompts/`)

`project-overview.md` names portfolio reviewers/interviewers as a primary
user who evaluate this project as a technical demo, so a stale README
directly undersells the finished work to that audience.

## The fix

Rewrite the "Correr el servidor" bullet list and "Estado actual" section in
`README.md` to describe the real, current behavior. Must not touch app code,
tests, or other docs.

## Build steps

- [x] Update `README.md`'s server section and "Estado actual" to accurately
      describe: real LLM streaming, per-field SSE events validated against
      `ExplainResponse`, retries with exponential backoff, per-request cost
      tracking (emitted as a `cost` event), and three selectable prompt
      versions (v1-v3, `PROMPT_VERSION` env var) with a changelog.
      Done when: README no longer claims hardcoded data or lists any of the
      five build-plan features as unimplemented, and each claim matches the
      current code in `app/`.

## Verify

Read the updated `README.md` and cross-check each claim against
`app/main.py`, `app/llm_client.py`, `app/cost.py`, and `app/prompts/` to
confirm accuracy. No automated check applies (documentation-only change).

## Findings

### readme-outdated-scaffold-description/F-01 [P2] fixed - README still describes the service as an unimplemented scaffold

**File:** README.md:28-44
**Found:** 2026-08-25 by /audit (scope: full; lens: quality)
**Why it matters:** `project-overview.md` names portfolio reviewers/interviewers as a primary user who "evaluate the project as a technical demo." The README's server section says `/explain` "emite eventos con datos hardcodeados," and "Estado actual" lists the real LLM call, retries/backoff, cost calculation, and v2/v3 prompts as "aún no implementado." All five build-plan features are complete and tested (`build-plan.md` fully checked), so a reader relying on the README alone would underestimate what the service actually does.
**Suggested fix:** Update the server section and "Estado actual" to describe the real behavior: real LLM streaming, retries with backoff, per-request cost tracking, and three versioned prompts.
**Resolution:** Fixed via `fix/readme-outdated-scaffold-description` - rewrote both sections to describe real LLM streaming, per-field SSE events, retries/backoff, cost tracking, and the three prompt versions.
