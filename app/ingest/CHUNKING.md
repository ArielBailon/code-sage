# Why code and docs chunk differently

`app/ingest/chunker.py` uses two different chunking strategies because code
and documentation have different units of meaning.

## Code: syntactic units (AST)

A Python file's meaningful boundaries are defined by its grammar, not its
prose - a function or class is a complete, self-contained unit whether or not
it's separated from its neighbors by comments or blank lines. `_chunk_code`
parses the file with the standard library `ast` module and chunks by
top-level `def`/`async def`/`class`, using each definition's own line range
(including its decorators) as the chunk boundary. This gives exact,
unambiguous boundaries that line up with how a reader (or a keyword search
over `symbol_name`) would look for "the `foo` function" - something a
text-based heuristic could get wrong on code with unusual formatting.

Top-level statements outside any function/class (imports, module docstring,
constants, script-level code) don't have a "symbol" of their own, so they're
grouped into `symbol_name=None` chunk(s) covering the gaps between/around the
real definitions. This keeps every line of the file inside some chunk, which
matters for exact-line citation (build-plan item 9).

Methods inside a class are not split into their own chunks - the whole class,
methods included, is one chunk. That matches the build-plan wording
("chunking ... por función/clase") and keeps the strategy simple; it can be
revisited later if keyword search over method names proves too coarse.

If a `.py` file fails to parse (`SyntaxError`), `_chunk_code` falls back to
one whole-file chunk rather than dropping the file from ingestion.

## Docs: topical units (headings)

Documentation doesn't have a grammar to parse - its structure is whatever the
author expressed with headings. `_chunk_doc` detects heading boundaries
(Markdown ATX `#`...`######`, and RST/Markdown setext underlines) and chunks
by section: each heading starts a new chunk that runs through the line before
the next heading. Content before the first heading becomes its own leading
chunk, so nothing is dropped.

This is a heuristic, not a full Markdown/RST parser - it's deliberately kept
to the standard library with no new dependency, matching how simple the rest
of the ingestion pipeline is. A file with no detected heading (plain `.txt`,
or `.rst`/`.md` without heading markup) falls back to one whole-file chunk,
the same behavior the placeholder chunker had for every file before this
feature.

## Why this split matters

Chunking code by syntax and docs by topic means each strategy produces
chunks that match how someone would actually reference that content - "the
`chunk_file` function" for code, "the Installation section" for docs -
instead of forcing both into one generic, structure-blind strategy.
