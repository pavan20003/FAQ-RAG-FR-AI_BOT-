"""Email support handoff or append it to a local JSONL outbox in development."""

from __future__ import annotations

import json
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from app.config import Settings, get_settings


def recent_conversation_messages(connection, session_id: str, *, limit: int = 6) -> list[dict[str, str]]:
    """Return the latest messages for a session in chronological order."""
    conversation = connection.execute(
        "SELECT id FROM conversations WHERE session_id = %s ORDER BY created_at DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    if not conversation:
        return []
    rows = connection.execute(
        "SELECT role, content FROM messages WHERE conversation_id = %s "
        "ORDER BY created_at DESC LIMIT %s",
        (conversation["id"], limit),
    ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def _message_body(message: str, history: list[dict[str, str]]) -> str:
    lines = ["Nouveau message transmis depuis l'assistant FAQ.", "", f"Message :\n{message}"]
    if history:
        lines.extend(["", "Derniers échanges :"])
        lines.extend(f"{item['role']}: {item['content']}" for item in history)
    return "\n".join(lines)


def send_handoff(
    *,
    session_id: str,
    email: str,
    message: str,
    history: list[dict[str, str]],
    settings: Settings | None = None,
) -> str:
    """Send support email when SMTP is configured; otherwise save to outbox."""
    settings = settings or get_settings()
    body = _message_body(message, history)
    if settings.smtp_host:
        if not settings.smtp_from_address or not settings.support_email:
            raise RuntimeError("SMTP_FROM_ADDRESS and SUPPORT_EMAIL are required with SMTP_HOST")
        email_message = EmailMessage()
        email_message["Subject"] = "Demande de suivi — assistant FAQ"
        email_message["From"] = settings.smtp_from_address
        email_message["To"] = settings.support_email
        email_message["Reply-To"] = email
        email_message.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout_seconds) as client:
            client.starttls(context=ssl.create_default_context())
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password or "")
            client.send_message(email_message)
        return "sent"

    outbox_path = Path(settings.outbox_path)
    outbox_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "customer_email": email,
        "message": message,
        "history": history,
    }
    with outbox_path.open("a", encoding="utf-8") as outbox:
        outbox.write(json.dumps(record, ensure_ascii=False) + "\n")
    return "saved"
