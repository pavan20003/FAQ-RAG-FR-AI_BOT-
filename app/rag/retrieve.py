"""Vector, French full-text, and reciprocal-rank hybrid retrieval."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Iterator, Literal, Protocol

from app.config import get_settings

SearchMode = Literal["vector", "keyword", "hybrid"]


class Encoder(Protocol):
    def encode(self, texts: list[str], *, kind: str = "query", batch_size: int = 32) -> list[list[float]]: ...


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    text: str
    heading: str
    source: str
    page: int | None
    vector_rank: int | None = None
    vector_score: float | None = None
    keyword_rank: int | None = None
    keyword_score: float | None = None
    rrf_score: float = 0.0


@contextmanager
def _database_connection(connection=None) -> Iterator[object]:
    """Use an injected connection or open and close the configured one."""
    owns_connection = connection is None
    if owns_connection:
        from app.db import connect

        connection = connect()
    if hasattr(connection, "info"):
        from pgvector.psycopg import register_vector

        register_vector(connection)
    try:
        yield connection
    finally:
        if owns_connection:
            connection.close()


def _query_embedding(query: str, encoder: Encoder | None) -> list[float]:
    if encoder is None:
        from app.ingest.embed import get_embedder

        encoder = get_embedder(get_settings().embedding_model)
    vectors = encoder.encode([query], kind="query")
    if not vectors:
        raise ValueError("Encoder returned no vector for a non-empty query")
    return vectors[0]


def _rows_to_vector_results(rows: list[dict]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id=row["chunk_id"],
            text=row["text"],
            heading=row["heading"],
            source=row["source"],
            page=row["page"],
            vector_rank=rank,
            vector_score=float(row["vector_score"]),
        )
        for rank, row in enumerate(rows, start=1)
    ]


def vector_search(
    query: str,
    *,
    connection=None,
    encoder: Encoder | None = None,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Find nearest chunks using cosine distance in pgvector."""
    if not query.strip() or top_k <= 0:
        return []
    embedding = _query_embedding(query.strip(), encoder)
    sql = (
        "SELECT c.id AS chunk_id, c.text, c.heading, d.source, c.page, "
        "1 - (c.embedding <=> %s::vector) AS vector_score "
        "FROM chunks AS c JOIN documents AS d ON d.id = c.document_id "
        "ORDER BY c.embedding <=> %s::vector, c.id LIMIT %s"
    )
    with _database_connection(connection) as db:
        rows = db.execute(sql, (embedding, embedding, top_k)).fetchall()
    return _rows_to_vector_results(rows)


def _or_query_terms(query: str) -> str:
    """Build a safe web-search tsquery with OR between plain word tokens."""
    terms = re.findall(r"[\wÀ-ÖØ-öø-ÿ]+", query, flags=re.UNICODE)
    return " OR ".join(terms)


def keyword_search(
    query: str,
    *,
    connection=None,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Rank chunks with French text search; query words use OR semantics."""
    if not query.strip() or top_k <= 0:
        return []
    tsquery_text = _or_query_terms(query)
    if not tsquery_text:
        return []
    sql = (
        "WITH search AS (SELECT websearch_to_tsquery('french', %s) AS tsquery) "
        "SELECT c.id AS chunk_id, c.text, c.heading, d.source, c.page, "
        "ts_rank_cd(c.tsv, search.tsquery) AS keyword_score "
        "FROM chunks AS c JOIN documents AS d ON d.id = c.document_id CROSS JOIN search "
        "WHERE c.tsv @@ search.tsquery "
        "ORDER BY keyword_score DESC, c.id LIMIT %s"
    )
    with _database_connection(connection) as db:
        rows = db.execute(sql, (tsquery_text, top_k)).fetchall()
    return [
        RetrievedChunk(
            chunk_id=row["chunk_id"],
            text=row["text"],
            heading=row["heading"],
            source=row["source"],
            page=row["page"],
            keyword_rank=rank,
            keyword_score=float(row["keyword_score"]),
        )
        for rank, row in enumerate(rows, start=1)
    ]


def retrieve(
    query: str,
    *,
    mode: SearchMode = "hybrid",
    connection=None,
    encoder: Encoder | None = None,
    top_k: int = 5,
    candidate_k: int = 20,
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    """Run one retrieval mode; hybrid fuses two top-20 lists with RRF."""
    if mode not in {"vector", "keyword", "hybrid"}:
        raise ValueError(f"Unknown retrieval mode: {mode}")
    if not query.strip() or top_k <= 0:
        return []
    if candidate_k <= 0 or rrf_k <= 0:
        raise ValueError("candidate_k and rrf_k must be positive")

    with _database_connection(connection) as db:
        if mode == "vector":
            return vector_search(query, connection=db, encoder=encoder, top_k=top_k)
        if mode == "keyword":
            return keyword_search(query, connection=db, top_k=top_k)

        vector_results = vector_search(query, connection=db, encoder=encoder, top_k=candidate_k)
        keyword_results = keyword_search(query, connection=db, top_k=candidate_k)
    fused: dict[int, RetrievedChunk] = {}
    for rows, rank_name, score_name in (
        (vector_results, "vector_rank", "vector_score"),
        (keyword_results, "keyword_rank", "keyword_score"),
    ):
        for result in rows:
            previous = fused.get(result.chunk_id)
            score = 1.0 / (rrf_k + getattr(result, rank_name))
            if previous is None:
                fused[result.chunk_id] = RetrievedChunk(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    heading=result.heading,
                    source=result.source,
                    page=result.page,
                    vector_rank=result.vector_rank,
                    vector_score=result.vector_score,
                    keyword_rank=result.keyword_rank,
                    keyword_score=result.keyword_score,
                    rrf_score=score,
                )
            else:
                fused[result.chunk_id] = RetrievedChunk(
                    chunk_id=previous.chunk_id,
                    text=previous.text,
                    heading=previous.heading,
                    source=previous.source,
                    page=previous.page,
                    vector_rank=result.vector_rank if score_name == "vector_score" else previous.vector_rank,
                    vector_score=result.vector_score if score_name == "vector_score" else previous.vector_score,
                    keyword_rank=result.keyword_rank if score_name == "keyword_score" else previous.keyword_rank,
                    keyword_score=result.keyword_score if score_name == "keyword_score" else previous.keyword_score,
                    rrf_score=previous.rrf_score + score,
                )
    return sorted(fused.values(), key=lambda item: (-item.rrf_score, item.chunk_id))[:top_k]


def _terms(text: str) -> set[str]:
    decomposed = unicodedata.normalize("NFD", text.lower())
    unaccented = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return set(re.findall(r"[a-z0-9]+", unaccented))


FRENCH_STOP_WORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en", "et", "est",
    "eux", "il", "je", "la", "le", "les", "leur", "lui", "ma", "mais", "me", "meme", "mes",
    "moi", "mon", "ne", "nos", "notre", "nous", "on", "ou", "par", "pas", "pour", "qu", "que",
    "quel", "quelle", "quelles", "quels", "qui", "sa", "se", "ses", "son", "sur", "ta", "te", "tes",
    "toi", "ton", "tu", "un", "une", "vos", "votre", "vous", "y",
}


def _term_coverage(query: str, result_text: str) -> float:
    query_terms = _terms(query) - FRENCH_STOP_WORDS
    if not query_terms:
        return 0.0
    return len(query_terms & _terms(result_text)) / len(query_terms)


def relevance_gate(
    results: list[RetrievedChunk],
    query: str,
    *,
    vector_threshold: float | None = None,
    keyword_threshold: float | None = None,
    min_term_coverage: float | None = None,
) -> bool:
    """Pass on strong vector similarity or strong, well-covered keyword match."""
    if not results or not query.strip():
        return False
    settings = get_settings()
    vector_floor = vector_threshold if vector_threshold is not None else settings.retrieval_vector_threshold
    keyword_floor = keyword_threshold if keyword_threshold is not None else settings.retrieval_keyword_threshold
    coverage_floor = min_term_coverage if min_term_coverage is not None else settings.retrieval_min_term_coverage

    for result in results:
        vector_pass = result.vector_score is not None and result.vector_score >= vector_floor
        keyword_pass = (
            result.keyword_score is not None
            and result.keyword_score >= keyword_floor
            and _term_coverage(query, result.text) >= coverage_floor
        )
        if vector_pass or keyword_pass:
            return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Retrieve relevant chunks from the local FAQ corpus")
    parser.add_argument("question", help="question to search for")
    parser.add_argument("--mode", choices=("vector", "keyword", "hybrid"), default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    results = retrieve(args.question, mode=args.mode, top_k=args.top_k)
    print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
