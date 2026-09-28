from pathlib import Path

from app.ingest.chunker import ChunkRecord, chunk_file


# -- code chunking (AST-based) --------------------------------------------


def test_chunk_file_code_splits_top_level_function(tmp_path: Path) -> None:
    file_path = tmp_path / "mod.py"
    file_path.write_text(
        "import os\n"
        "\n"
        "def greet(name):\n"
        "    return f'hi {name}'\n"
        "\n"
        "x = 1\n",
        encoding="utf-8",
    )

    chunks = chunk_file(file_path, "code")

    assert [(c.symbol_name, c.start_line, c.end_line) for c in chunks] == [
        (None, 1, 2),
        ("greet", 3, 4),
        (None, 5, 6),
    ]
    assert chunks[1].content == "def greet(name):\n    return f'hi {name}'\n"
    assert all(c.chunk_type == "code" for c in chunks)


def test_chunk_file_code_keeps_class_methods_inside_class_chunk(tmp_path: Path) -> None:
    file_path = tmp_path / "mod.py"
    file_path.write_text(
        "class Greeter:\n"
        "    def hello(self):\n"
        "        return 'hi'\n"
        "\n"
        "    def bye(self):\n"
        "        return 'bye'\n",
        encoding="utf-8",
    )

    chunks = chunk_file(file_path, "code")

    assert len(chunks) == 1
    assert chunks[0].symbol_name == "Greeter"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 6
    assert "def hello" in chunks[0].content
    assert "def bye" in chunks[0].content


def test_chunk_file_code_includes_decorator_in_function_range(tmp_path: Path) -> None:
    file_path = tmp_path / "mod.py"
    file_path.write_text(
        "@app.get('/health')\n"
        "def health():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )

    chunks = chunk_file(file_path, "code")

    assert len(chunks) == 1
    assert chunks[0].symbol_name == "health"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert chunks[0].content.startswith("@app.get")


def test_chunk_file_code_falls_back_to_whole_file_on_syntax_error(tmp_path: Path) -> None:
    file_path = tmp_path / "broken.py"
    file_path.write_text("def broken(:\n    pass\n", encoding="utf-8")

    chunks = chunk_file(file_path, "code")

    assert chunks == [
        ChunkRecord(
            source_path=str(file_path),
            chunk_type="code",
            start_line=1,
            end_line=2,
            content="def broken(:\n    pass\n",
            symbol_name=None,
        )
    ]


def test_chunk_file_code_handles_empty_file(tmp_path: Path) -> None:
    file_path = tmp_path / "empty.py"
    file_path.write_text("", encoding="utf-8")

    chunks = chunk_file(file_path, "code")

    assert chunks == [
        ChunkRecord(
            source_path=str(file_path),
            chunk_type="code",
            start_line=1,
            end_line=1,
            content="",
            symbol_name=None,
        )
    ]


def test_chunk_file_code_handles_module_with_no_functions_or_classes(tmp_path: Path) -> None:
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


# -- doc chunking (section-based) ------------------------------------------


def test_chunk_file_doc_splits_on_markdown_atx_headings(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.md"
    file_path.write_text(
        "# Title\n"
        "intro line\n"
        "## Section A\n"
        "content a\n"
        "## Section B\n"
        "content b\n",
        encoding="utf-8",
    )

    chunks = chunk_file(file_path, "doc")

    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 2), (3, 4), (5, 6)]
    assert chunks[0].content == "# Title\nintro line\n"
    assert all(c.symbol_name is None and c.chunk_type == "doc" for c in chunks)


def test_chunk_file_doc_splits_on_rst_setext_headings(tmp_path: Path) -> None:
    file_path = tmp_path / "guide.rst"
    file_path.write_text(
        "Guide\n"
        "=====\n"
        "intro\n"
        "Section\n"
        "-------\n"
        "body\n",
        encoding="utf-8",
    )

    chunks = chunk_file(file_path, "doc")

    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 3), (4, 6)]


def test_chunk_file_doc_keeps_content_before_first_heading_as_leading_chunk(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.md"
    file_path.write_text(
        "preamble\n"
        "# Heading\n"
        "body\n",
        encoding="utf-8",
    )

    chunks = chunk_file(file_path, "doc")

    assert [(c.start_line, c.end_line) for c in chunks] == [(1, 1), (2, 3)]
    assert chunks[0].content == "preamble\n"


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
