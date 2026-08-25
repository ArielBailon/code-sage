# Prompt Changelog

## v1 - baseline

The first working prompt: instructs the model to emit exactly four lines,
one per `ExplainResponse` field, each a `"field: <JSON value>"` line in a
fixed order. This line-per-field shape was chosen so the response could be
streamed and parsed incrementally by `FieldStreamParser` (feature 2) without
waiting for the whole completion - each field becomes its own SSE event as
soon as its line closes.

## v1 -> v2 - reduce malformed completions

Early manual testing showed the model would occasionally drift from the
exact format - most often by describing complexity across a wrapped
sentence, or writing `posibles_bugs` as generic best-practice advice instead
of bugs grounded in the actual snippet. v2 adds:

- A worked one-shot example showing the exact expected output for a real
  snippet, which is the most reliable lever for getting a model to match an
  exact, unusual output format.
- Tightened `complejidad` guidance (Big-O when it applies, a qualitative note
  otherwise) so the model doesn't invent a Big-O bound for code that doesn't
  have one.
- An explicit instruction that `posibles_bugs` must be grounded in the given
  snippet, not generic advice, to cut down on boilerplate answers.

## v2 -> v3 - handle degenerate input and leading preambles

v2 assumed the snippet is always real code and the question is always
relevant. Real inputs aren't always that clean: an empty snippet, a
non-code paste, or a question that has nothing to do with the code. v3
adds:

- Explicit instructions for degenerate input: still emit all four fields
  (say so in `resumen`, `"N/A"` for `complejidad`, an empty array for
  `posibles_bugs`, explain what's missing in `sugerencia`) instead of asking
  a clarifying question, which would break the fixed four-field contract.
- A stronger zero-preamble constraint ("the first character you output must
  be `r`") after observing the model occasionally emit a short greeting or
  acknowledgment before the first field, which `FieldStreamParser` can't
  handle since it expects the first line to already be `resumen: ...`.
