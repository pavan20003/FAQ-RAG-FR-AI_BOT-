"""Retrieve, gate, answer in French, validate citations, and log the exchange."""

from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass

from psycopg.types.json import Jsonb

from app.config import get_settings
from app.rag.llm import LLMClient, LLMResponse, get_llm
from app.rag.prompt import FRENCH_SYSTEM_PROMPT, build_user_prompt
from app.rag.retrieve import RetrievedChunk, relevance_gate, retrieve

ABSTENTION_MESSAGE = (
    "Je ne trouve pas cette information dans les documents disponibles. "
    "Veuillez contacter la boulangerie afin que son équipe puisse vous aider."
)
MAX_QUESTION_CHARS = 500
CITATION_RE = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True)
class AnswerSource:
    citation: str
    title: str
    path: str
    page: int | None


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[AnswerSource]
    abstained: bool
    session_id: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0


def validate_question(question: str) -> str:
    """Normalize basic input and enforce the Phase 4 request bound."""
    if not isinstance(question, str):
        raise ValueError("La question doit être du texte.")
    cleaned = " ".join(question.split())
    if not cleaned:
        raise ValueError("Veuillez saisir une question.")
    if len(cleaned) > MAX_QUESTION_CHARS:
        raise ValueError(f"La question ne doit pas dépasser {MAX_QUESTION_CHARS} caractères.")
    return cleaned


def sanitize_citations(answer: str, passage_count: int) -> tuple[str, list[int]]:
    """Remove out-of-range citations and return the valid passage numbers used."""
    valid_numbers: list[int] = []

    def replace(match: re.Match[str]) -> str:
        number = int(match.group(1))
        if not 1 <= number <= passage_count:
            return ""
        valid_numbers.append(number)
        return match.group(0)

    cleaned = CITATION_RE.sub(replace, answer)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned).strip()
    return cleaned, list(dict.fromkeys(valid_numbers))


def build_sources(chunks: list[RetrievedChunk], citations: list[int]) -> list[AnswerSource]:
    """Build source metadata only from the retrieved passage list."""
    sources: list[AnswerSource] = []
    seen: set[tuple[str, int | None]] = set()
    for number in citations:
        chunk = chunks[number - 1]
        key = (chunk.source, chunk.page)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            AnswerSource(
                citation=f"[{number}]",
                title=chunk.title or chunk.heading,
                path=chunk.source,
                page=chunk.page,
            )
        )
    return sources


def _log_exchange(
    *,
    connection,
    session_id: str,
    question: str,
    result: AnswerResult,
) -> None:
    """Persist the user and assistant messages in one transaction."""
    owns_connection = connection is None
    if owns_connection:
        from app.db import connect

        connection = connect()
    try:
        with connection.transaction():
            conversation = connection.execute(
                "SELECT id FROM conversations WHERE session_id = %s ORDER BY created_at DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            if conversation:
                conversation_id = conversation["id"]
            else:
                conversation_id = connection.execute(
                    "INSERT INTO conversations (session_id) VALUES (%s) RETURNING id",
                    (session_id,),
                ).fetchone()["id"]

            connection.execute(
                "INSERT INTO messages (conversation_id, role, content, sources, abstained, latency_ms) "
                "VALUES (%s, 'user', %s, %s, FALSE, %s)",
                (conversation_id, question, Jsonb([]), result.latency_ms),
            )
            connection.execute(
                "INSERT INTO messages (conversation_id, role, content, sources, abstained, latency_ms) "
                "VALUES (%s, 'assistant', %s, %s, %s, %s)",
                (
                    conversation_id,
                    result.answer,
                    Jsonb([asdict(source) for source in result.sources]),
                    result.abstained,
                    result.latency_ms,
                ),
            )
    finally:
        if owns_connection:
            connection.close()


def answer_question(
    question: str,
    *,
    session_id: str | None = None,
    llm: LLMClient | None = None,
    fake_llm: bool = False,
    retriever=retrieve,
    gate=relevance_gate,
    connection=None,
) -> AnswerResult:
    """Answer from retrieved evidence, or abstain before making any LLM call."""
    started = time.perf_counter()
    cleaned_question = validate_question(question)
    session_id = session_id or str(uuid.uuid4())

    chunks = retriever(cleaned_question, mode="hybrid", connection=connection)
    settings = get_settings()
    if not gate(
        chunks,
        cleaned_question,
        vector_threshold=settings.retrieval_vector_threshold,
        keyword_threshold=settings.retrieval_keyword_threshold,
        min_term_coverage=settings.retrieval_min_term_coverage,
    ):
        answer = AnswerResult(
            answer=ABSTENTION_MESSAGE,
            sources=[],
            abstained=True,
            session_id=session_id,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        _log_exchange(connection=connection, session_id=session_id, question=cleaned_question, result=answer)
        return answer

    if llm is None:
        llm = get_llm(fake=fake_llm)
    response: LLMResponse = llm.generate(
        FRENCH_SYSTEM_PROMPT,
        build_user_prompt(cleaned_question, chunks),
    )
    answer_text, citation_numbers = sanitize_citations(response.text, len(chunks))
    answer = AnswerResult(
        answer=answer_text,
        sources=build_sources(chunks, citation_numbers),
        abstained=False,
        session_id=session_id,
        latency_ms=int((time.perf_counter() - started) * 1000),
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
    )
    _log_exchange(connection=connection, session_id=session_id, question=cleaned_question, result=answer)
    return answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer a French FAQ question using local retrieval")
    parser.add_argument("question", help="question to answer")
    parser.add_argument("--fake-llm", action="store_true", help="use the deterministic offline FakeLLM")
    args = parser.parse_args()
    result = answer_question(args.question, fake_llm=args.fake_llm)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
