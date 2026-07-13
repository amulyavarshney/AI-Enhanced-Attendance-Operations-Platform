"""HTTP middleware helpers."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

access_logger = logging.getLogger("attendance.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            access_logger.info(
                "method=%s path=%s status=%s duration_ms=%s request_id=%s client=%s",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                request_id,
                request.client.host if request.client else "-",
            )
