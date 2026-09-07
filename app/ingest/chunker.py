from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChunkRecord:
    source_path: str
    chunk_type: str
    start_line: int
    end_line: int
    content: str
    symbol_name: str | None = None


def chunk_file(path: Path, chunk_type: str) -> list[ChunkRecord]:
    """Placeholder chunker: one chunk covering the whole file.

    Replaced by real per-strategy chunking (AST for code, semantic for docs)
    in feature 6b.
    """
    content = path.read_text(encoding="utf-8")
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
