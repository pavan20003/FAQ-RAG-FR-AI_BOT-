"""Small in-memory rate limit and safe request ID helpers."""

from __future__ import annotations

import re
import threading
import time
import uuid
from collections import defaultdict, deque


class RateLimiter:
    """Per-process sliding-window rate limiter; not shared across workers."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60) -> None:
        if max_requests < 1 or window_seconds < 1:
            raise ValueError("Rate limit settings must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, identity: str, *, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        cutoff = current - self.window_seconds
        with self.lock:
            events = self.requests[identity]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.max_requests:
                return False
            events.append(current)
            return True


def request_id_from_header(value: str | None) -> str:
    """Accept a short printable request ID or create an opaque UUID."""
    if value and len(value) <= 64 and re.fullmatch(r"[A-Za-z0-9._:-]+", value):
        return value
    return str(uuid.uuid4())
