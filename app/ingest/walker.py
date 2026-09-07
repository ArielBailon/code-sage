import os
from pathlib import Path

CODE_EXTENSIONS = {".py"}
DOC_EXTENSIONS = {".md", ".rst", ".txt"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def classify_files(repo_path: Path) -> list[tuple[Path, str]]:
    """Walk repo_path and classify relevant files as "code" or "doc".

    Paths are returned relative to repo_path, sorted for deterministic
    output. Files with an unrecognized extension, or that fail to decode as
    UTF-8, are skipped.
    """
    classified: list[tuple[Path, str]] = []

    for dirpath, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix in CODE_EXTENSIONS:
                chunk_type = "code"
            elif path.suffix in DOC_EXTENSIONS:
                chunk_type = "doc"
            else:
                continue

            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            classified.append((path.relative_to(repo_path), chunk_type))

    return sorted(classified, key=lambda item: str(item[0]))
