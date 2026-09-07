CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    source_path TEXT NOT NULL,
    chunk_type TEXT NOT NULL CHECK (chunk_type IN ('code', 'doc')),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content TEXT NOT NULL,
    -- Placeholder dimension (OpenAI text-embedding-3-small); revisit once
    -- feature 7 (hybrid search) picks the actual embedding model.
    embedding VECTOR(1536),
    symbol_name TEXT
);
