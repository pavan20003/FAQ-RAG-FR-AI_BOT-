from __future__ import annotations

import os
import uuid

import psycopg
import pytest
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.rag.retrieve import RetrievedChunk, keyword_search, relevance_gate, retrieve, vector_search
from app.rag.answer import answer_question
from app.rag.llm import FakeLLM


class FakeEncoder:
    """Return a known direction so retrieval tests never load a model."""

    def encode(self, texts, *, kind="query", batch_size=32):
        return [[0.0, 1.0] for _ in texts]


@pytest.fixture
def fixture_db():
    url = os.getenv("TEST_DATABASE_URL", "postgresql://faqrag:faqrag@localhost:5432/faqrag")
    try:
        connection = psycopg.connect(url, row_factory=dict_row, autocommit=True)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Local PostgreSQL fixture is unavailable: {exc}")

    schema = f"retrieval_test_{uuid.uuid4().hex}"
    connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    connection.execute(f'CREATE SCHEMA "{schema}"')
    connection.execute(f'SET search_path TO "{schema}", public')
    connection.execute(
        "CREATE TABLE documents ("
        "id BIGSERIAL PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL, doc_type TEXT NOT NULL, "
        "content_hash TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE chunks ("
        "id BIGSERIAL PRIMARY KEY, document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, "
        "chunk_index INTEGER NOT NULL, heading TEXT NOT NULL, text TEXT NOT NULL, embedding vector(2) NOT NULL, "
        "tsv tsvector GENERATED ALWAYS AS (to_tsvector('french', text)) STORED, page INTEGER NULL)"
    )
    connection.execute(
        "CREATE TABLE conversations ("
        "id BIGSERIAL PRIMARY KEY, session_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    connection.execute(
        "CREATE TABLE messages ("
        "id BIGSERIAL PRIMARY KEY, conversation_id BIGINT NOT NULL REFERENCES conversations(id), "
        "role TEXT NOT NULL, content TEXT NOT NULL, sources JSONB NOT NULL DEFAULT '[]'::jsonb, "
        "abstained BOOLEAN NOT NULL DEFAULT FALSE, latency_ms INTEGER NOT NULL DEFAULT 0, "
        "created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    register_vector(connection)
    documents = []
    for source, title in (("breads.md", "Pains"), ("hours.md", "Horaires")):
        documents.append(
            connection.execute(
                "INSERT INTO documents(source, title, doc_type, content_hash) VALUES (%s, %s, 'text', 'fixture') RETURNING id",
                (source, title),
            ).fetchone()["id"]
        )
    connection.execute(
        "INSERT INTO chunks(document_id, chunk_index, heading, text, embedding, page) "
        "VALUES (%s, 0, 'Baguette tradition', "
        "'La baguette tradition pèse 250 grammes et coûte 1,30 euro.', %s, NULL)",
        (documents[0], [1.0, 0.0]),
    )
    connection.execute(
        "INSERT INTO chunks(document_id, chunk_index, heading, text, embedding, page) "
        "VALUES (%s, 0, 'Horaires', "
        "'La boutique ouvre du mardi au vendredi de 7 h à 19 h.', %s, NULL)",
        (documents[1], [0.0, 1.0]),
    )
    try:
        yield connection
    finally:
        connection.execute("SET search_path TO public")
        connection.execute(f'DROP SCHEMA "{schema}" CASCADE')
        connection.close()


def test_keyword_exact_match_finds_the_right_chunk(fixture_db):
    results = keyword_search("baguette tradition", connection=fixture_db, top_k=5)

    assert results
    assert results[0].source == "breads.md"
    assert results[0].keyword_rank == 1
    assert results[0].keyword_score > 0


def test_vector_search_finds_a_paraphrased_question(fixture_db):
    results = vector_search(
        "Quand puis-je venir ce matin ?",
        connection=fixture_db,
        encoder=FakeEncoder(),
        top_k=5,
    )

    assert results
    assert results[0].source == "hours.md"
    assert results[0].vector_rank == 1


def test_hybrid_fuses_vector_and_keyword_candidates(fixture_db):
    results = retrieve(
        "baguette tradition",
        mode="hybrid",
        connection=fixture_db,
        encoder=FakeEncoder(),
        candidate_k=20,
        top_k=5,
    )

    assert {result.source for result in results} == {"breads.md", "hours.md"}
    bread = next(result for result in results if result.source == "breads.md")
    hours = next(result for result in results if result.source == "hours.md")
    assert bread.keyword_rank == 1
    assert hours.vector_rank == 1
    assert bread.rrf_score > 0 and hours.rrf_score > 0


def test_empty_database_and_empty_query_return_no_results(fixture_db):
    fixture_db.execute("DELETE FROM documents")

    assert retrieve("pain", mode="vector", connection=fixture_db, encoder=FakeEncoder()) == []
    assert retrieve("pain", mode="keyword", connection=fixture_db) == []
    assert retrieve("", mode="hybrid", connection=fixture_db, encoder=FakeEncoder()) == []


def test_relevance_gate_uses_vector_or_keyword_with_term_coverage():
    strong_vector = RetrievedChunk(1, "Horaires de la boutique", "Horaires", "hours.md", None, vector_score=0.7)
    weak_keyword = RetrievedChunk(2, "Horaires de la boutique", "Horaires", "hours.md", None, keyword_score=0.2)
    strong_keyword = RetrievedChunk(3, "Le croissant coûte 1,20 euro", "Viennoiseries", "prices.md", None, keyword_score=0.2)

    assert relevance_gate([strong_vector], "Quand ouvrez-vous ?", vector_threshold=0.6)
    assert not relevance_gate([weak_keyword], "Quel est le prix du croissant ?", keyword_threshold=0.1, min_term_coverage=0.6)
    assert relevance_gate([strong_keyword], "Quel est le prix du croissant ?", keyword_threshold=0.1, min_term_coverage=0.4)
    assert not relevance_gate([], "Quel est le prix ?")


def test_answer_flow_logs_question_and_assistant_sources(fixture_db):
    llm = FakeLLM()
    result = answer_question(
        "Quel est le prix de la baguette ?",
        session_id="answer-fixture",
        retriever=lambda query, mode, connection: retrieve(
            query, mode=mode, connection=connection, encoder=FakeEncoder()
        ),
        llm=llm,
        connection=fixture_db,
    )

    messages = fixture_db.execute(
        "SELECT role, content, sources, abstained FROM messages ORDER BY id"
    ).fetchall()
    assert result.abstained is False
    assert llm.calls == 1
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["sources"]
    assert messages[1]["abstained"] is False
