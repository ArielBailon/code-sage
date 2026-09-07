from pathlib import Path

from app.ingest.chunker import ChunkRecord, chunk_file


def test_chunk_file_returns_one_chunk_covering_whole_file(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.py"
    file_path.write_text("line1\nline2\nline3\n", encoding="utf-8")

    chunks = chunk_file(file_path, "code")

    assert chunks == [
        ChunkRecord(
            source_path=str(file_path),
            chunk_type="code",
            start_line=1,
            end_line=3,
            content="line1\nline2\nline3\n",
            symbol_name=None,
        )
    ]


def test_chunk_file_handles_file_without_trailing_newline(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.md"
    file_path.write_text("a\nb", encoding="utf-8")

    chunks = chunk_file(file_path, "doc")

    assert chunks[0].end_line == 2
    assert chunks[0].start_line == 1


def test_chunk_file_handles_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    chunks = chunk_file(file_path, "doc")

    assert chunks == [
        ChunkRecord(
            source_path=str(file_path),
            chunk_type="doc",
            start_line=1,
            end_line=1,
            content="",
            symbol_name=None,
        )
    ]
