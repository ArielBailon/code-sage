import asyncio
import sys
from pathlib import Path

import asyncpg

from app.db.connection import close_pool, get_pool
from app.ingest.chunker import chunk_file
from app.ingest.walker import classify_files


async def ingest_repo(repo_path: Path, pool: asyncpg.Pool) -> int:
    """Walk repo_path, chunk each classified file, and insert into `chunks`.

    Returns the number of rows written.
    """
    rows_written = 0

    for relative_path, chunk_type in classify_files(repo_path):
        for record in chunk_file(repo_path / relative_path, chunk_type):
            record.source_path = relative_path.as_posix()
            await pool.execute(
                """
                INSERT INTO chunks
                    (source_path, chunk_type, start_line, end_line, content, symbol_name)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                record.source_path,
                record.chunk_type,
                record.start_line,
                record.end_line,
                record.content,
                record.symbol_name,
            )
            rows_written += 1

    return rows_written


async def _main(repo_path: Path) -> None:
    pool = await get_pool()
    try:
        rows_written = await ingest_repo(repo_path, pool)
        print(f"Ingested {rows_written} chunk(s) from {repo_path}")
    finally:
        await close_pool()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m app.ingest.pipeline <repo_path>", file=sys.stderr)
        raise SystemExit(1)
    asyncio.run(_main(Path(sys.argv[1])))
