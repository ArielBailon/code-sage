import ast
import re
from dataclasses import dataclass
from pathlib import Path

_TOP_LEVEL_DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_ATX_HEADING = re.compile(r"^#{1,6}\s+\S")
_SETEXT_UNDERLINE = re.compile(r"^([=\-~^])\1*$")


@dataclass
class ChunkRecord:
    source_path: str
    chunk_type: str
    start_line: int
    end_line: int
    content: str
    symbol_name: str | None = None


def chunk_file(path: Path, chunk_type: str) -> list[ChunkRecord]:
    """Chunk a file using the strategy for its type.

    Code (`chunk_type="code"`) is chunked by AST-defined function/class
    boundaries (see `_chunk_code`). Docs (`chunk_type="doc"`) are chunked by
    heading boundaries (see `_chunk_doc`).
    """
    if chunk_type == "code":
        return _chunk_code(path)
    return _chunk_doc(path)


def _chunk_code(path: Path) -> list[ChunkRecord]:
    """Chunk a Python file by top-level function/class boundaries.

    Each top-level `def`/`async def`/`class` becomes its own chunk, with
    `symbol_name` set to its name and its range extended to cover any
    decorators. Everything else at module level (imports, docstring,
    constants, script-level statements) is grouped into `symbol_name=None`
    chunk(s) covering the untouched line ranges, so the chunks together cover
    the whole file with no gaps or overlaps. Falls back to one whole-file
    chunk when the file doesn't parse as Python (e.g. non-standard syntax).
    """
    content = path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _whole_file_chunk(path, "code", content)

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    if total_lines == 0:
        return _whole_file_chunk(path, "code", content)

    intervals: list[tuple[int, int, str]] = []
    for node in tree.body:
        if isinstance(node, _TOP_LEVEL_DEF_TYPES):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            intervals.append((start, node.end_lineno, node.name))

    chunks: list[ChunkRecord] = []
    cursor = 1
    for start, end, symbol_name in intervals:
        if cursor < start:
            chunks.append(_make_chunk(path, "code", lines, cursor, start - 1, None))
        chunks.append(_make_chunk(path, "code", lines, start, end, symbol_name))
        cursor = end + 1

    if cursor <= total_lines:
        chunks.append(_make_chunk(path, "code", lines, cursor, total_lines, None))

    return chunks


def _chunk_doc(path: Path) -> list[ChunkRecord]:
    """Chunk a doc file by heading boundaries.

    Detects Markdown ATX headings (`#` through `######`) and RST/Markdown
    setext headings (a non-blank line followed by a line of one repeated
    `=`/`-`/`~`/`^` character). Each detected heading starts a new chunk that
    runs through the line before the next heading (or end of file); content
    before the first heading becomes its own leading chunk. Falls back to one
    whole-file chunk when no heading is detected.
    """
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    if total_lines == 0:
        return _whole_file_chunk(path, "doc", content)

    stripped = [line.rstrip("\r\n") for line in lines]
    heading_starts: list[int] = []

    i = 0
    while i < total_lines:
        text = stripped[i]
        if _ATX_HEADING.match(text):
            heading_starts.append(i + 1)
            i += 1
            continue
        if text.strip() and i + 1 < total_lines and _SETEXT_UNDERLINE.match(stripped[i + 1]):
            heading_starts.append(i + 1)
            i += 2
            continue
        i += 1

    if not heading_starts:
        return _whole_file_chunk(path, "doc", content)

    chunks: list[ChunkRecord] = []
    if heading_starts[0] > 1:
        chunks.append(_make_chunk(path, "doc", lines, 1, heading_starts[0] - 1, None))

    for idx, start in enumerate(heading_starts):
        end = heading_starts[idx + 1] - 1 if idx + 1 < len(heading_starts) else total_lines
        chunks.append(_make_chunk(path, "doc", lines, start, end, None))

    return chunks


def _make_chunk(
    path: Path,
    chunk_type: str,
    lines: list[str],
    start: int,
    end: int,
    symbol_name: str | None,
) -> ChunkRecord:
    return ChunkRecord(
        source_path=str(path),
        chunk_type=chunk_type,
        start_line=start,
        end_line=end,
        content="".join(lines[start - 1 : end]),
        symbol_name=symbol_name,
    )


def _whole_file_chunk(path: Path, chunk_type: str, content: str) -> list[ChunkRecord]:
    end_line = max(len(content.splitlines()), 1)
    return [
        ChunkRecord(
            source_path=str(path),
            chunk_type=chunk_type,
            start_line=1,
            end_line=end_line,
            content=content,
            symbol_name=None,
        )
    ]
