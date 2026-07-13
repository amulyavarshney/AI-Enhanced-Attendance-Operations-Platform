"""Simple in-memory rate limiter for expensive endpoints (e.g. AI)."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Rate limit exceeded: max {self.max_requests} requests "
                        f"per {self.window_seconds} seconds"
                    ),
                    headers={"Retry-After": str(self.window_seconds)},
                )
            bucket.append(now)


AI_RATE_LIMIT_MAX = int(os.getenv("AI_RATE_LIMIT_MAX", "20"))
AI_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AI_RATE_LIMIT_WINDOW_SECONDS", "60"))

ai_rate_limiter = SlidingWindowRateLimiter(
    max_requests=AI_RATE_LIMIT_MAX,
    window_seconds=AI_RATE_LIMIT_WINDOW_SECONDS,
)


def rate_limit_ai(request: Request) -> None:
    """Dependency: limit AI endpoints per client IP + auth subject when present."""
    client_host = request.client.host if request.client else "unknown"
    auth = request.headers.get("authorization", "")
    subject = auth[-24:] if auth else "anonymous"
    ai_rate_limiter.check(f"{client_host}:{subject}")
