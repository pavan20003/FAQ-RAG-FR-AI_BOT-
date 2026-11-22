"""FastAPI application factory and HTTP endpoints."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import json
import logging
import time
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.api.security import RateLimiter, request_id_from_header
from app.config import Settings, get_settings
from app.db import get_connection, init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize the database once the service starts."""
    init_db()
    yield


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(getattr(record, "event", {"message": record.getMessage()}), ensure_ascii=False)


def create_app(*, settings: Settings | None = None, initialize_database: bool = True,
               answerer: Callable | None = None, connection_provider: Callable | None = None,
               ingest_fn: Callable | None = None, handoff_fn: Callable | None = None,
               rate_limiter: RateLimiter | None = None) -> FastAPI:
    settings = settings or get_settings()
    @asynccontextmanager
    async def app_lifespan(_: FastAPI) -> AsyncIterator[None]:
        if initialize_database:
            init_db()
        yield

    app = FastAPI(title="FAQ RAG FR", lifespan=app_lifespan)
    origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                           allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Admin-Token", "X-Request-ID"])
    app.state.settings = settings
    app.state.answerer = answerer
    app.state.connection_provider = connection_provider or get_connection
    app.state.ingest_fn = ingest_fn
    app.state.handoff_fn = handoff_fn
    app.state.rate_limiter = rate_limiter or RateLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)
    app.state.project_root = Path(__file__).resolve().parent.parent
    logger = logging.getLogger("faq_rag.http")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    @app.middleware("http")
    async def request_controls(request: Request, call_next):
        request_id = request_id_from_header(request.headers.get("X-Request-ID"))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = None
        try:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_request_bytes:
                response = JSONResponse({"detail": "Requête trop volumineuse."}, status_code=413)
            elif request.method == "POST" and request.url.path in {"/ask", "/handoff"} and not app.state.rate_limiter.allow(request.client.host if request.client else "unknown"):
                response = JSONResponse({"detail": "Trop de requêtes. Réessayez plus tard."}, status_code=429)
            else:
                response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            status = response.status_code if response is not None else 500
            logger.info("request", extra={"event": {"timestamp": time.time(), "request_id": request_id,
                "method": request.method, "path": request.url.path, "status": status,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "client_ip": request.client.host if request.client else None}})

    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
