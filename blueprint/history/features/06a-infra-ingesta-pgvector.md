# Feature: Infra de ingesta y pgvector

**From build-plan:** feature 6a
**Status:** complete

## Goal

Stand up the storage and file-classification plumbing that Phase 2's RAG
pipeline needs: a `chunks` table in Postgres/pgvector, a walker that tells
code files from documentation files in a locally cloned repository, and a
placeholder (whole-file) chunker wired end to end so the ingestion pipeline
provably writes rows into the database. The real chunking strategies (AST for
code, semantic for docs) land in the next feature (6b) on top of this.

## In scope

- `chunks` table in Postgres with the `vector` extension enabled, matching
  the shape locked in `project-overview.md` (`source_path`, `chunk_type`,
  `start_line`, `end_line`, `content`, `embedding`, `symbol_name`).
- A Postgres connection pool for the app (`asyncpg`, no ORM).
- A local dev setup for Postgres+pgvector via `docker-compose.yml`.
- A walker that classifies files in a given local repo path as `code` (`.py`)
  or `doc` (`.md`, `.rst`, `.txt`), skipping everything else (`.git`, virtual
  envs, `node_modules`, binaries, unreadable/non-UTF-8 files).
- A placeholder chunker: one chunk per file, covering the whole file
  (`start_line=1`, `end_line=<last line>`, `symbol_name=None`).
- An ingestion pipeline function that runs walker -> chunker -> DB insert for
  a given repo path, runnable as a script.

## Out of scope

- Real chunking by function/class (code) or by section (docs) - feature 6b.
- Generating embeddings - `embedding` stays `NULL` here; filled in by feature
  7 (hybrid search).
- Cloning the target repo automatically - the user clones it locally by hand;
  the pipeline takes a local path.
- An HTTP endpoint to trigger ingestion - it runs as a script/CLI for now.
  Background-job scheduling for ingestion is a separate, later infra item.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Walker de clasificación de archivos** - `app/ingest/walker.py`
      with `classify_files(repo_path: Path) -> list[tuple[Path, str]]`,
      walking the repo and tagging each relevant file `"code"` or `"doc"`,
      skipping `.git`, virtual envs, `node_modules`, binaries, and files that
      fail to decode as UTF-8. *Done when:* a unit test over a temp directory
      with a mix of `.py`, `.md`, and irrelevant files asserts the exact
      classified list.
- [x] **Step 2 - ChunkRecord y chunker placeholder** - `app/ingest/chunker.py`
      defines `ChunkRecord` (the pre-insert shape: `source_path`,
      `chunk_type`, `start_line`, `end_line`, `content`, `symbol_name`) and
      `chunk_file(path: Path, chunk_type: str) -> list[ChunkRecord]`,
      returning one whole-file chunk. *Done when:* a unit test confirms a
      file of N lines yields one `ChunkRecord` with `end_line == N` and the
      full file content.
- [x] **Step 3 - Dependencias, docker-compose y esquema Postgres/pgvector** -
      add `asyncpg` and `pgvector` to `pyproject.toml`; add
      `docker-compose.yml` with a `pgvector/pgvector` Postgres image; add
      `DATABASE_URL` to `.env.example`; add `app/db/schema.sql` creating the
      `vector` extension and the `chunks` table. Update the Data & Storage
      section of `coding-standards.md` to document the choice (asyncpg, no
      ORM, plain SQL schema file). *Done when:* `docker compose up -d db`
      starts Postgres with pgvector, and applying `schema.sql` creates the
      table without error.
- [x] **Step 4 - Conexión a la base de datos** - `app/db/connection.py` with
      `get_pool()` / `close_pool()` wrapping an `asyncpg` pool built from
      `DATABASE_URL` (moved from the originally-specced `app/db.py`: that
      path collided with `app/db/schema.sql` needing `app/db` to be a
      package, not a module). *Done when:* a manual `SELECT 1` through the
      pool against the local Docker Postgres succeeds.
- [x] **Step 5 - Pipeline de ingesta end to end** - `app/ingest/pipeline.py`
      with `ingest_repo(repo_path: Path, pool) -> int` chaining
      walker -> chunker -> insert (returns rows written), runnable via
      `python -m app.ingest.pipeline <repo_path>`. *Done when:* running it
      against any local directory (this repo itself is enough to validate
      the pipeline - the real target open source repo isn't chosen until
      feature 6b/7 need real content) populates `chunks` with one row per
      classified file, confirmed via `SELECT count(*) FROM chunks`.

## Files / areas

- `pyproject.toml` - `asyncpg`, `pgvector` dependencies
- `docker-compose.yml` - new, local Postgres+pgvector
- `.env.example` - `DATABASE_URL`
- `app/db/__init__.py`, `app/db/schema.sql`, `app/db/connection.py` - new package
- `app/ingest/__init__.py`, `app/ingest/walker.py`, `app/ingest/chunker.py`,
  `app/ingest/pipeline.py` - new package
- `blueprint/context/coding-standards.md` - Data & Storage section
- `tests/test_ingest_walker.py`, `tests/test_ingest_chunker.py` - new

## Data / contracts

- `chunks` table (locked in `project-overview.md`): `id`, `source_path`,
  `chunk_type` (`code`|`doc`), `start_line`, `end_line`, `content`,
  `embedding` (vector, nullable for now), `symbol_name` (nullable).
- `ChunkRecord` (Python, internal - not an API boundary shape, so a
  `dataclass` is fine rather than a Pydantic model): mirrors the table minus
  `id` and `embedding`.

## Testing

`pytest` is the declared test command in `AGENTS.md`, so the test gate is
active. In-scope pure logic: `classify_files` (walker) and `chunk_file`
(chunker) - both take a path and return data, no I/O beyond reading local
files, straightforward edge cases (mixed file types, unreadable/non-UTF-8
files, empty directory). Both ship a passing test in the same step.

`app/db.py` and `app/ingest/pipeline.py` are integration glue against a real
Postgres - verified manually (Step 3-5 done-when criteria: docker compose up,
run the pipeline, inspect rows with `psql`/`SELECT`), not unit-tested. The
repo has no DB test fixture pattern yet (no testcontainers, no test database
config), and building one is out of scope for this infra-sized feature.

## Notes for the AI

- No ORM in this project; keep the DB layer to `asyncpg` + plain SQL, per the
  updated Data & Storage section in `coding-standards.md`.
- `ChunkRecord` is internal data, not a request/response shape, so it doesn't
  need to live in `app/models.py` or be a Pydantic model - a `dataclass` in
  `app/ingest/chunker.py` is consistent with the project's existing style.
- The `chunks` table shape is locked in `project-overview.md`; don't add or
  remove columns without updating it there too.
- Keep instructions/commands in the spec and docs Windows-friendly (Docker
  Desktop + PowerShell or Git Bash), matching this project's dev environment.
