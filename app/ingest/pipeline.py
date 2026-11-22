"""Hash-based ingestion from a local folder into PostgreSQL."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from app.ingest.chunker import chunk_text
from app.ingest.loaders import SUPPORTED_SUFFIXES, load_document


class Encoder(Protocol):
    def encode(self, texts: list[str], *, kind: str = "passage", batch_size: int = 32) -> list[list[float]]: ...


@dataclass(frozen=True)
class IngestResult:
    added: int
    updated: int
    skipped: int
    deleted: int
    chunks: int


def ingest_directory(
    directory: str | Path,
    *,
    connection=None,
    encoder: Encoder | None = None,
) -> IngestResult:
    """Ingest supported files, replacing changed chunks atomically."""
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError(f"Ingestion path is not a directory: {root}")
    owns_connection = connection is None
    if owns_connection:
        from app.db import connect, init_db

        init_db()
        connection = connect()

    if hasattr(connection, "info"):
        from pgvector.psycopg import register_vector

        register_vector(connection)

    if encoder is None:
        from app.config import get_settings
        from app.ingest.embed import get_embedder

        settings = get_settings()
        encoder = get_embedder(settings.embedding_model)

    try:
        with connection.transaction():
            existing_rows = connection.execute("SELECT source, id, content_hash FROM documents").fetchall()
            existing = {row["source"]: row for row in existing_rows}
            paths = sorted(
                path for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
            )
            current_sources = {path.relative_to(root).as_posix() for path in paths}
            stale_sources = set(existing) - current_sources
            prepared: list[tuple[str, str, object, list[object], list[str]]] = []
            skipped = 0

            for path in paths:
                source = path.relative_to(root).as_posix()
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                old = existing.get(source)
                if old is not None and old["content_hash"] == digest:
                    skipped += 1
                    continue
                document = load_document(path, source=source)
                chunks = []
                for loaded_page in document.pages:
                    page_chunks = chunk_text(
                        loaded_page.text, title=document.title, page=loaded_page.page
                    )
                    index_offset = len(chunks)
                    chunks.extend(
                        replace(chunk, chunk_index=index_offset + index)
                        for index, chunk in enumerate(page_chunks)
                    )
                vectors = encoder.encode([chunk.text for chunk in chunks], kind="passage")
                if len(vectors) != len(chunks):
                    raise ValueError(f"Encoder returned {len(vectors)} vectors for {len(chunks)} chunks in {source}")
                prepared.append((source, digest, document, chunks, vectors))

            added = sum(source not in existing for source, *_ in prepared)
            updated = len(prepared) - added
            chunk_count = sum(len(chunks) for _, _, _, chunks, _ in prepared)

            # All document replacement and stale-file deletion changes commit together.
            for source in stale_sources:
                connection.execute("DELETE FROM documents WHERE source = %s", (source,))
            for source, digest, document, chunks, vectors in prepared:
                row = connection.execute(
                    "INSERT INTO documents (source, title, doc_type, content_hash) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (source) DO UPDATE SET title = EXCLUDED.title, "
                    "doc_type = EXCLUDED.doc_type, content_hash = EXCLUDED.content_hash, "
                    "ingested_at = now() RETURNING id",
                    (source, document.title, document.doc_type, digest),
                ).fetchone()
                document_id = row["id"]
                connection.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
                for chunk, vector in zip(chunks, vectors):
                    connection.execute(
                        "INSERT INTO chunks (document_id, chunk_index, heading, text, embedding, page) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (document_id, chunk.chunk_index, chunk.heading, chunk.text, vector, chunk.page),
                    )
        return IngestResult(added, updated, skipped, len(stale_sources), chunk_count)
    finally:
        if owns_connection:
            connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest local website and PDF sources")
    parser.add_argument("directory", type=Path, help="directory containing source documents")
    args = parser.parse_args()
    result = ingest_directory(args.directory)
    print(
        f"Ajoutés : {result.added}; mis à jour : {result.updated}; "
        f"inchangés : {result.skipped}; supprimés : {result.deleted}; "
        f"nouveaux passages : {result.chunks}"
    )


if __name__ == "__main__":
    main()
