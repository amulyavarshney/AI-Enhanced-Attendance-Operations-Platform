"""Simple circuit breaker for external dependency calls."""

from __future__ import annotations

import threading
import time


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    @property
    def is_open(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return False
            if time.monotonic() - self._opened_at >= self.recovery_timeout_seconds:
                # Half-open: allow a probe request
                return False
            return True

    def allow_request(self) -> bool:
        return not self.is_open

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = time.monotonic()

    def status(self) -> str:
        if self.is_open:
            return "open"
        if self._failures > 0:
            return "degraded"
        return "closed"
