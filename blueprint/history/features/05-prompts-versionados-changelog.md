# Feature: Prompts versionados (v1-v3) con changelog

**From build-plan:** feature 5
**Status:** complete

## Goal

`app/prompts/v2.py` and `v3.py` are still `# pendiente` stubs, and there's no
`CHANGELOG.md`, even though `coding-standards.md` already documents that
convention. Feature 4 hardcoded `RequestCost.prompt_version` to `"v1"` as a
placeholder specifically because this feature didn't exist yet. This feature
writes two real prompt iterations, makes the active version selectable and
actually reflected in the cost log, and documents why each version changed.

## In scope

- Real content for `PROMPT_V2` and `PROMPT_V3`, each a genuine iteration on
  `PROMPT_V1` - not placeholder text. Both must preserve the exact four-line,
  one-JSON-value-per-line output contract `FieldStreamParser` depends on
  (`resumen`, `complejidad`, `posibles_bugs`, `sugerencia`, in that order) -
  versioning changes the instructions/guidance, never the wire shape.
- A small lookup (`app/prompts/__init__.py`): `get_prompt(version) -> str`,
  raising `ValueError` for an unrecognized version - same shape as
  `app/cost.py`'s `MODEL_PRICING`/`calculate_cost` pattern already in this
  codebase.
- `LLMClient` takes a `prompt_version` constructor parameter (default
  `"v1"`), resolves the template once at construction (fail fast on a bad
  version, not on the first request), and uses it in `stream_explanation`.
- `/explain`'s process reads a `PROMPT_VERSION` env var (default `"v1"`,
  mirroring how `MODEL_NAME` already works) into the `llm_client` singleton,
  and the cost log/event uses `llm_client.prompt_version` instead of the
  hardcoded constant.
- `app/prompts/CHANGELOG.md` explaining the reasoning behind v1 (baseline)
  and the v1->v2 and v2->v3 changes.

## Out of scope

- Per-request prompt version override - `ExplainRequest` is a locked
  contract (`project-overview.md`), and this feature doesn't touch it.
  Version selection is a deployment-time choice (env var), not a per-call one.
- Any mechanism to automatically pick a version (A/B testing, quality-based
  switching) - out of scope; this just makes the existing v1/v2/v3 iterations
  real and selectable.
- Changing `MODEL_NAME`'s selection pattern - `PROMPT_VERSION` follows the
  same pattern for consistency, but this feature doesn't touch model
  selection itself.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - write real `PROMPT_V2` and `PROMPT_V3`** - replace both
  `# pendiente` stubs. `PROMPT_V2` adds a worked one-shot example of the
  exact expected output (reduces malformed/parse-failure completions) and
  clarifies `complejidad` guidance (Big-O when it applies, otherwise a
  qualitative note). `PROMPT_V3` additionally handles degenerate input
  (empty/non-code snippet, or a question unrelated to the snippet - still
  emit all four fields rather than asking a clarifying question) and adds a
  stronger zero-preamble constraint. Both keep the same four fields, same
  order, same "field: JSON-on-one-line" shape as `PROMPT_V1`.
  *Done when:* a new `tests/test_prompts.py` parametrized across
  `PROMPT_V1`/`PROMPT_V2`/`PROMPT_V3` asserts all four field markers
  (`resumen:`, `complejidad:`, `posibles_bugs:`, `sugerencia:`) appear in
  that relative order in each - a guard against a future edit silently
  breaking the parser contract.
- [x] **Step 2 - `get_prompt` version registry** - `app/prompts/__init__.py`
  exposes `PROMPT_VERSIONS = {"v1": PROMPT_V1, "v2": PROMPT_V2, "v3":
  PROMPT_V3}` and `get_prompt(version: str) -> str`, raising `ValueError` for
  a version not in the table.
  *Done when:* unit tests confirm `get_prompt("v1"|"v2"|"v3")` returns the
  matching constant, and `get_prompt("v4")` (or any unrecognized string)
  raises `ValueError`.
- [x] **Step 3 - wire version selection through `LLMClient` and `/explain`**
  - `LLMClient.__init__` gains `prompt_version: str = "v1"`, calls
  `get_prompt(prompt_version)` immediately (so a bad version fails at
  construction) and stores both `self.prompt_version` and the resolved
  template; `stream_explanation` formats using the resolved template instead
  of the module-level `PROMPT_V1` import. In `app/main.py`, construct
  `llm_client` with `prompt_version=os.getenv("PROMPT_VERSION", "v1")`,
  delete the hardcoded `PROMPT_VERSION = "v1"` constant, and use
  `llm_client.prompt_version` when building `RequestCost`.
  *Done when:* a unit test constructs `LLMClient(..., prompt_version="v2")`
  and confirms the prompt sent to the fake Anthropic client contains v2's
  distinguishing content and not v3's; a second test confirms
  `LLMClient(..., prompt_version="not-a-version")` raises `ValueError` at
  construction, before any request is made; a `TestClient` test against
  `/explain` (monkeypatching `main.llm_client.prompt_version`, same pattern
  already used for the unrecognized-model cost test) confirms the
  `event: cost` frame's `prompt_version` field reflects the configured value
  instead of a hardcoded `"v1"`.
- [x] **Step 4 - `CHANGELOG.md` and env example** - write
  `app/prompts/CHANGELOG.md` documenting why v1 looks the way it does and
  the reasoning behind the v1->v2 and v2->v3 changes; add `PROMPT_VERSION=v1`
  to `.env.example`.
  *Done when:* both files exist with real content (not a placeholder) and
  the full test suite still passes (this step adds no logic, so no new test
  is required - see Testing).

## Files / areas

- `app/prompts/v2.py`, `app/prompts/v3.py` - real prompt content.
- `app/prompts/__init__.py` - `PROMPT_VERSIONS` + `get_prompt`.
- `app/prompts/CHANGELOG.md` - new, version rationale.
- `app/llm_client.py` - `prompt_version` constructor param, resolved template.
- `app/main.py` - env-driven `prompt_version`, dynamic `RequestCost.prompt_version`.
- `.env.example` - document `PROMPT_VERSION`.
- `tests/test_prompts.py` - new, field-order contract check across versions.
- `tests/test_llm_client.py` - version-selection and fail-fast tests.
- `tests/test_main.py` - cost-event `prompt_version` reflects configuration.

## Data / contracts

- No change to `ExplainRequest`, `ExplainResponse`, or the SSE event shapes
  locked by earlier features.
- `RequestCost.prompt_version` (already locked in feature 4) now carries the
  real configured version instead of a hardcoded placeholder - the field
  itself is unchanged, only where its value comes from.

## Testing

- Test runner is `pytest` (declared in `AGENTS.md`), so this is a gate: Steps
  1-3 add logic (content/contract invariants, registry lookup, version
  wiring) and each ships tests in the same step. Step 4 is docs/env-example
  only, so it rides on the full suite staying green rather than a new test.
- `tests/test_prompts.py` is new, one `test_*.py` per module per
  `coding-standards.md`.
- Step 3's `LLMClient` test extends the existing fake-client pattern in
  `tests/test_llm_client.py` (same fakes used for the retry/usage tests).

## Notes for the AI

- Do not change `FieldStreamParser`'s expected wire format - every prompt
  version must still produce exactly one line per field, in the same order,
  with a JSON value on that same line. Versioning is about instruction
  quality, not the output contract.
- `LLMClient` resolving `prompt_version` eagerly at construction (not lazily
  on first request) matches how the app already fails at startup for other
  misconfiguration and gives a clear, immediate error if `PROMPT_VERSION` is
  ever set to something that doesn't exist.
- Keep `app/cost.py`'s `MODEL_PRICING`/`calculate_cost` shape in mind as the
  precedent for `PROMPT_VERSIONS`/`get_prompt` - same "small table + raise on
  unknown key" pattern, for consistency across the codebase.
