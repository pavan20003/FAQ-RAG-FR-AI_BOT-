"""PostgreSQL connection and idempotent schema setup."""

from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row

from app.config import get_settings


def connect() -> psycopg.Connection:
    """Open a database connection and register pgvector values."""
    connection = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    return connection


def get_connection() -> Iterator[psycopg.Connection]:
    """FastAPI dependency that closes its connection after the request."""
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


def resolve_embedding_dim(model_name: str, configured_dim: int | None = None) -> int:
    """Get vector width from the embedding model, with a test-only override."""
    if configured_dim is not None:
        return configured_dim
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    dimension = model.get_sentence_embedding_dimension()
    if dimension is None:
        raise RuntimeError(f"Could not determine embedding dimension for {model_name}")
    return dimension


def init_db() -> None:
    """Create required extensions, tables, and indexes if they are missing."""
    settings = get_settings()
    dimension = resolve_embedding_dim(settings.embedding_model, settings.embedding_dim)
    statements = [
        "CREATE EXTENSION IF NOT EXISTS vector",
        "CREATE TABLE IF NOT EXISTS documents ("
        "id BIGSERIAL PRIMARY KEY, source TEXT NOT NULL UNIQUE, title TEXT NOT NULL, "
        "doc_type TEXT NOT NULL, content_hash TEXT NOT NULL, "
        "ingested_at TIMESTAMPTZ NOT NULL DEFAULT now())",
        f"CREATE TABLE IF NOT EXISTS chunks ("
        f"id BIGSERIAL PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, "
        f"chunk_index INTEGER NOT NULL, heading TEXT NOT NULL DEFAULT '', text TEXT NOT NULL, "
        f"embedding vector({dimension}) NOT NULL, "
        f"tsv tsvector GENERATED ALWAYS AS (to_tsvector('french', text)) STORED, page INTEGER NULL, "
        f"UNIQUE(document_id, chunk_index))",
        "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx "
        "ON chunks USING hnsw (embedding vector_cosine_ops)",
        "CREATE INDEX IF NOT EXISTS chunks_tsv_gin_idx ON chunks USING gin (tsv)",
        "CREATE TABLE IF NOT EXISTS conversations ("
        "id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())",
        "CREATE INDEX IF NOT EXISTS conversations_session_idx ON conversations(session_id)",
        "CREATE TABLE IF NOT EXISTS messages ("
        "id BIGSERIAL PRIMARY KEY, conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, "
        "role TEXT NOT NULL, content TEXT NOT NULL, sources JSONB NOT NULL DEFAULT '[]'::jsonb, "
        "abstained BOOLEAN NOT NULL DEFAULT FALSE, latency_ms INTEGER NOT NULL DEFAULT 0, "
        "created_at TIMESTAMPTZ NOT NULL DEFAULT now())",
    ]
    with connect() as connection:
        for statement in statements:
            connection.execute(statement)
