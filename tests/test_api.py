from __future__ import annotations

import contextlib
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.security import RateLimiter
from app.config import Settings
from app.handoff import send_handoff
from app.main import create_app
from app.rag.answer import answer_question
from app.rag.llm import FakeLLM
from app.rag.retrieve import RetrievedChunk


class _Result:
    def __init__(self, row=None, rows=None):
        self.row, self.rows = row, rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class _Database:
    def __init__(self):
        self.conversations = {}
        self.messages = []
        self.next_id = 1

    @contextlib.contextmanager
    def transaction(self):
        yield

    def execute(self, query, params=()):
        if query.startswith("SELECT id FROM conversations"):
            conversation_id = self.conversations.get(params[0])
            return _Result({"id": conversation_id} if conversation_id else None)
        if query.startswith("INSERT INTO conversations"):
            conversation_id = self.next_id
            self.next_id += 1
            self.conversations[params[0]] = conversation_id
            return _Result({"id": conversation_id})
        if query.startswith("INSERT INTO messages"):
            self.messages.append({"conversation_id": params[0], "role": "assistant" if "'assistant'" in query else "user", "content": params[1]})
            return _Result()
        if query.startswith("SELECT role, content FROM messages"):
            rows = [m for m in self.messages if m["conversation_id"] == params[0]][-params[1]:]
            return _Result(rows=list(reversed(rows)))
        raise AssertionError(query)


def _client(tmp_path, *, limit=20):
    database = _Database()

    @contextlib.contextmanager
    def connection_provider():
        yield database

    chunk = RetrievedChunk(1, "La baguette coûte 1,30 euro.", "Tarifs", "prix.md", 1, "Tarifs", 0.8)

    def answerer(question, *, session_id=None, connection=None):
        return answer_question(question, session_id=session_id, connection=connection, llm=FakeLLM(),
                               retriever=lambda *_args, **_kwargs: [chunk], gate=lambda *_args, **_kwargs: True)

    settings = Settings(admin_token="secret", outbox_path=str(tmp_path / "outbox.jsonl"), rate_limit_requests=limit)
    app = create_app(settings=settings, initialize_database=False, answerer=answerer,
                     connection_provider=connection_provider, rate_limiter=RateLimiter(limit, 60))
    app.state.project_root = tmp_path
    return TestClient(app), database


def test_ask_returns_grounded_french_answer_and_request_id(tmp_path):
    client, _database = _client(tmp_path)
    response = client.post("/ask", json={"question": "Quel est le prix ?"}, headers={"X-Request-ID": "test-123"})
    assert response.status_code == 200
    assert response.json()["abstained"] is False
    assert response.json()["sources"][0]["path"] == "prix.md"
    assert response.headers["X-Request-ID"] == "test-123"


def test_ask_abstains_without_evidence(tmp_path):
    client, _database = _client(tmp_path)
    client.app.state.answerer = lambda question, **kwargs: answer_question(
        question, connection=kwargs["connection"], retriever=lambda *_a, **_k: [], gate=lambda *_a, **_k: False
    )
    response = client.post("/ask", json={"question": "Une information inconnue ?"})
    assert response.status_code == 200
    assert response.json()["abstained"] is True
    assert response.json()["sources"] == []


def test_validation_rate_limit_admin_auth_and_request_size(tmp_path):
    client, _database = _client(tmp_path, limit=2)
    assert client.post("/ask", json={"question": "  "}).status_code == 422
    assert client.post("/ingest", json={"folder": "data"}).status_code == 401
    assert client.post("/ingest", json={"folder": "../"}, headers={"X-Admin-Token": "secret"}).status_code == 400
    assert client.post("/ask", content="{}", headers={"Content-Length": "999999"}).status_code == 413
    rate_client, _ = _client(tmp_path / "rate", limit=2)
    assert rate_client.post("/ask", json={"question": "ok"}).status_code == 200
    assert rate_client.post("/ask", json={"question": "ok"}).status_code == 200
    assert rate_client.post("/ask", json={"question": "ok"}).status_code == 429


def test_handoff_writes_private_details_to_local_outbox(tmp_path):
    client, _database = _client(tmp_path)
    asked = client.post("/ask", json={"question": "Quel est le prix ?"})
    response = client.post("/handoff", json={"session_id": asked.json()["session_id"],
        "email": "client@example.fr", "message": "Pouvez-vous confirmer ?"})
    assert response.status_code == 200
    record = json.loads((tmp_path / "outbox.jsonl").read_text(encoding="utf-8"))
    assert record["customer_email"] == "client@example.fr"
    assert record["history"]


def test_ingest_calls_configured_function_after_authentication(tmp_path):
    calls = []
    client, _database = _client(tmp_path)
    client.app.state.ingest_fn = lambda directory: calls.append(directory) or SimpleNamespace(added=1, updated=0, skipped=0, deleted=0, chunks=3)
    (tmp_path / "docs").mkdir()
    response = client.post("/ingest", json={"folder": "docs"}, headers={"X-Admin-Token": "secret"})
    assert response.status_code == 200
    assert response.json()["added"] == 1
    assert calls == [tmp_path / "docs"]
