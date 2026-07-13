"""HTTP middleware helpers."""

from __future__ import annotations

import logging
import time
import uuid

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

access_logger = logging.getLogger("attendance.access")
audit_logger = logging.getLogger("attendance.audit")

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_AUDIT_SKIP_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/admin/reset-database",
)


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
            if response is not None:
                _maybe_write_audit_log(request, response, request_id)


def _maybe_write_audit_log(request: Request, response: Response, request_id: str) -> None:
    if request.method not in _MUTATING_METHODS:
        return
    if not (200 <= response.status_code < 400):
        return
    path = request.url.path
    if any(path.startswith(prefix) for prefix in _AUDIT_SKIP_PREFIXES):
        return

    try:
        from .auth import JWT_ALGORITHM, JWT_SECRET_KEY
        from . import crud
        from .database import SessionLocal

        actor_id = None
        actor_email = None
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                payload = jwt.decode(
                    auth.split(" ", 1)[1],
                    JWT_SECRET_KEY,
                    algorithms=[JWT_ALGORITHM],
                )
                actor_id = int(payload["sub"]) if payload.get("sub") else None
                actor_email = payload.get("email")
            except Exception:
                pass

        db = SessionLocal()
        try:
            crud.create_audit_log(
                db,
                method=request.method,
                path=path,
                status_code=response.status_code,
                action=f"{request.method} {path}",
                actor_id=actor_id,
                actor_email=actor_email,
                details={"request_id": request_id, "query": str(request.url.query or "")},
            )
        finally:
            db.close()
    except Exception as exc:
        audit_logger.warning("Failed to persist audit log: %s", exc)
