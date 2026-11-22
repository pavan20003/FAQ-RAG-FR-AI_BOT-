"""Public API routes for FAQ answers, ingestion, and customer handoff."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import AskRequest, AskResponse, HandoffRequest, HandoffResponse, IngestRequest, IngestResponse
from app.handoff import recent_conversation_messages, send_handoff
from app.ingest.pipeline import ingest_directory
from app.rag.answer import answer_question

router = APIRouter()


@contextmanager
def _connection(request: Request):
    provider = request.app.state.connection_provider
    resource = provider()
    if hasattr(resource, "__enter__"):
        with resource as connection:
            yield connection
    else:
        connection = next(resource)
        try:
            yield connection
        finally:
            resource.close()


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request) -> AskResponse:
    answerer = request.app.state.answerer or answer_question
    with _connection(request) as connection:
        result = answerer(payload.question, session_id=payload.session_id, connection=connection)
    return AskResponse(answer=result.answer, sources=[asdict(source) for source in result.sources],
                        abstained=result.abstained, session_id=result.session_id)


@router.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, request: Request) -> IngestResponse:
    token = request.app.state.settings.admin_token
    if not token:
        raise HTTPException(status_code=503, detail="L'ingestion administrateur n'est pas configurée.")
    if request.headers.get("X-Admin-Token") != token:
        raise HTTPException(status_code=401, detail="Authentification administrateur requise.")
    target = (request.app.state.project_root / payload.folder).resolve()
    try:
        target.relative_to(request.app.state.project_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Le dossier doit rester dans le projet.") from exc
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Le dossier d'ingestion est introuvable.")
    try:
        result = (request.app.state.ingest_fn or ingest_directory)(target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(**result.__dict__)


@router.post("/handoff", response_model=HandoffResponse)
def handoff(payload: HandoffRequest, request: Request) -> HandoffResponse:
    with _connection(request) as connection:
        history = recent_conversation_messages(connection, payload.session_id)
    sender = request.app.state.handoff_fn or send_handoff
    try:
        status = sender(session_id=payload.session_id, email=payload.email, message=payload.message,
                        history=history, settings=request.app.state.settings)
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail="Le transfert au support est temporairement indisponible.") from exc
    return HandoffResponse(status=status)
