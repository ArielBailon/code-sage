# Feature: Chunking especializado

**From build-plan:** feature 6b
**Build attempt:** 1
**Branch:** feature/chunking-especializado
**Status:** verified

## Goal

Replace the whole-file placeholder chunker from feature 6a with two real,
format-appropriate strategies: AST-based chunking by function/class for Python
code, and section-based chunking by heading for documentation. This is the
part of build-plan item 6 that actually differentiates code from docs instead
of treating every file the same way.

## In scope

- A code chunker that parses a `.py` file's AST and emits one `ChunkRecord`
  per top-level `def`/`async def`/`class`, each with `symbol_name` set to
  that function or class name and `start_line`/`end_line` spanning its
  decorators through its last line.
- Coverage for top-level code that isn't inside a function/class (imports,
  module docstring, constants, script-level statements): grouped into
  `symbol_name=None` chunk(s) so no line of the file is dropped from
  citation coverage.
- A resilience fallback: if a `.py` file fails to parse (`SyntaxError`), fall
  back to the existing whole-file chunk instead of crashing ingestion.
- A doc chunker that splits on heading boundaries - Markdown ATX (`#`, `##`,
  ...) and RST/Markdown setext (a line followed by a same-length line of
  repeated `=`/`-`/`~`/`^`) - emitting one `ChunkRecord` per section with
  `symbol_name=None` (the locked schema ties `symbol_name` to code lookup
  only, per `project-overview.md`).
- A fallback to the existing whole-file chunk for doc files with no detected
  heading (plain `.txt`, or `.rst`/`.md` without heading markup) - no
  regression from 6a's behavior for those files.
- `chunk_file(path, chunk_type)` keeps its exact signature and dispatches to
  the code or doc strategy internally, so `app/ingest/pipeline.py` needs no
  changes.
- A short write-up of why code and docs need different chunking strategies,
  per build-plan item 6's explicit ask.

## Out of scope

- Per-method chunking inside a class - a class (with its methods) is one
  chunk, matching "por función/clase" literally. Revisit only if feature 7/8
  keyword search proves class-level granularity insufficient.
- Choosing/cloning the real target open source repo - deferred to whichever
  of feature 7 or 11 first needs real ingested content, per 6a's own
  deferral note. This feature validates chunkers with test fixtures.
- Generating embeddings - still `NULL`, feature 7's job.
- An HTTP endpoint or background scheduling for ingestion - still a script.
- A real RST/Markdown parser dependency - the heading heuristic below is
  intentionally simple and repository-native (stdlib only, no new
  dependency), matching this project's existing "no unneeded dependency"
  pattern.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Chunker de código por AST** - in `app/ingest/chunker.py`, add
      an AST-based code strategy: parse the file with the `ast` module, walk
      `tree.body` in source order, and for each top-level
      `FunctionDef`/`AsyncFunctionDef`/`ClassDef` emit a `ChunkRecord` with
      `symbol_name=<name>`, `start_line=min(decorator lines, node.lineno)`,
      `end_line=node.end_lineno`, `content=<exact original lines joined>`.
      Gaps between/around those nodes (module docstring, imports, constants,
      other top-level statements) become their own `symbol_name=None`
      chunk(s) covering the untouched line ranges, so total chunk coverage
      equals the whole file with no gaps or overlaps. On `SyntaxError`, fall
      back to one whole-file chunk (today's placeholder behavior). Wire
      `chunk_type == "code"` in `chunk_file` to this strategy.
      *Done when:* unit tests cover a top-level function, a top-level class
      (asserting its methods stay inside the class chunk, not split out), a
      decorated function (decorator line included in its range), leftover
      module-level code before/after/between defs, an empty file, and a file
      with invalid syntax (whole-file fallback) - `pytest` passes.
- [x] **Step 2 - Chunker de docs por secciones** - in the same file, add a
      section-based doc strategy: scan the file's lines for heading
      boundaries (Markdown ATX `^#{1,6}\s+\S` or a setext underline - a
      non-blank line immediately followed by a line of one repeated
      `=`/`-`/`~`/`^` character of the same length) and emit one
      `ChunkRecord` per section (`symbol_name=None`), including any content
      before the first heading as its own leading chunk. A file with no
      detected heading falls back to one whole-file chunk. Wire
      `chunk_type == "doc"` in `chunk_file` to this strategy.
      *Done when:* unit tests cover a Markdown file with multiple ATX
      headings, an RST-style file with setext headings, content preceding
      the first heading, and a heading-less file (whole-file fallback) -
      `pytest` passes, and the two pre-existing doc placeholder tests in
      `tests/test_ingest_chunker.py` still pass unchanged (both are
      heading-less inputs).
- [x] **Step 3 - Documentar la diferencia de estrategia** - add
      `app/ingest/CHUNKING.md` explaining why code is chunked by syntactic
      unit (AST-defined function/class boundaries) while docs are chunked by
      topical unit (author-defined heading boundaries), and why each
      fallback exists. Update `chunk_file`'s and `chunk_code`/`chunk_doc`'s
      docstrings to describe the real strategies instead of the retired
      placeholder note. *Done when:* `app/ingest/CHUNKING.md` exists and
      `pytest` still passes (no behavior change in this step).

## Files / areas

- `app/ingest/chunker.py` - replaces the placeholder body of `chunk_file`
  with the AST and section strategies; `ChunkRecord` shape is unchanged.
- `app/ingest/CHUNKING.md` - new, strategy rationale.
- `tests/test_ingest_chunker.py` - new cases per step; existing heading-less
  doc cases must keep passing as-is.
- `app/ingest/pipeline.py`, `app/ingest/walker.py` - unchanged (no signature
  or wiring changes needed).

## Data / contracts

- `ChunkRecord` shape is unchanged (`source_path`, `chunk_type`, `start_line`,
  `end_line`, `content`, `symbol_name`).
- `symbol_name` is populated only for code chunks (function/class name), per
  the schema note in `project-overview.md` that ties it to keyword search
  over code; doc chunks always keep `symbol_name=None`.
- Line ranges are 1-indexed and inclusive on both ends, matching the existing
  placeholder convention and the locked `chunks` table columns.
- Heading detection is a heuristic, not a full RST/Markdown parser: it covers
  ATX and setext heading styles and intentionally does not handle every RST
  directive. This is a recorded, reversible implementation choice - no schema
  or API impact if a richer parser replaces it later.

## Testing

`pytest` is the declared test command and the test gate is active. Both
strategies are pure logic (path in, `ChunkRecord` list out, no I/O beyond
reading the local file) and get full unit coverage per the done-when criteria
above, following the existing style in `tests/test_ingest_chunker.py`. No
integration/DB test is added - `chunk_file`'s callers (`pipeline.py`) are
unchanged, so 6a's existing manual verification (`docker compose up`, run the
pipeline, inspect rows) still covers the end-to-end path and doesn't need to
be re-run for this feature's done-when criteria.

## Notes for the AI

- Do not change `ChunkRecord`'s fields or `chunk_file`'s signature -
  `pipeline.py` depends on both staying exactly as they are.
- Use `ast.parse` from the standard library; no new dependency for either
  strategy (`pyproject.toml` stays unchanged).
- Reconstruct chunk `content` from the file's own lines (e.g.
  `str.splitlines(keepends=True)` sliced by line range), not from
  re-serializing the AST, so whitespace/comments/formatting inside a chunk
  are byte-for-byte what's in the file.
- Per-method chunking is explicitly deferred (see Out of scope) - don't
  recurse into class bodies to split out methods.
- Keep instructions and file references Windows-friendly, matching this
  project's dev environment (no shell-specific syntax in docstrings or
  `CHUNKING.md`).


<!-- blueprint:completion {"schemaVersion":1,"specBytes":8722,"specSha256":"5c557bae26b590892730fcb5fc15b6973d00cb6ac1db2c60e8f7e8786cbb45f0","branch":"refs/heads/feature/chunking-especializado","head":"27d1b893bd80d9b64e492e33eedd7db9b667f1e2","baseRef":"refs/heads/master","baseCommit":"27d1b893bd80d9b64e492e33eedd7db9b667f1e2","sourceTree":"30d1651c734c377c1f326886621f74a20d2238b7","absentOptional":["blueprint/context/review.md"]} -->
