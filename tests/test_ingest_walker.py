from pathlib import Path

from app.ingest.walker import classify_files


def test_classify_files_returns_code_and_doc_files(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# Notes\n", encoding="utf-8")
    (tmp_path / "guide.rst").write_text("Guide\n=====\n", encoding="utf-8")
    (tmp_path / "todo.txt").write_text("- item\n", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")

    result = classify_files(tmp_path)

    assert result == [
        (Path("app.py"), "code"),
        (Path("guide.rst"), "doc"),
        (Path("notes.md"), "doc"),
        (Path("todo.txt"), "doc"),
    ]


def test_classify_files_skips_ignored_directories(tmp_path: Path) -> None:
    skipped_dir = tmp_path / "node_modules"
    skipped_dir.mkdir()
    (skipped_dir / "lib.py").write_text("ignored\n", encoding="utf-8")
    (tmp_path / "keep.py").write_text("print('keep')\n", encoding="utf-8")

    result = classify_files(tmp_path)

    assert result == [(Path("keep.py"), "code")]


def test_classify_files_skips_undecodable_files(tmp_path: Path) -> None:
    (tmp_path / "broken.py").write_bytes(b"\xff\xfe\x00invalid")
    (tmp_path / "good.py").write_text("print('ok')\n", encoding="utf-8")

    result = classify_files(tmp_path)

    assert result == [(Path("good.py"), "code")]


def test_classify_files_returns_empty_list_for_empty_directory(tmp_path: Path) -> None:
    assert classify_files(tmp_path) == []
