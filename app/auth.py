"""JWT authentication and role-based access control."""

from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Tuple

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "14"))
APP_ENV = os.getenv("APP_ENV", "development").lower()

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: Optional[str]) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def _hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(*, employee_id: int, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(employee_id),
        "email": email,
        "role": role,
        "typ": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("typ", "access") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def issue_refresh_token(
    db: Session,
    *,
    employee_id: int,
    family_id: Optional[str] = None,
) -> str:
    raw = secrets.token_urlsafe(48)
    token_hash = _hash_refresh_token(raw)
    family = family_id or str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=JWT_REFRESH_DAYS)
    row = models.RefreshToken(
        employee_id=employee_id,
        token_hash=token_hash,
        family_id=family,
        expires_at=expires_at,
        revoked=0,
    )
    db.add(row)
    db.commit()
    return raw


def revoke_refresh_family(db: Session, family_id: str) -> None:
    db.query(models.RefreshToken).filter(models.RefreshToken.family_id == family_id).update(
        {"revoked": 1},
        synchronize_session=False,
    )
    db.commit()


def rotate_refresh_token(db: Session, raw_token: str) -> Tuple[str, str, models.Employee]:
    token_hash = _hash_refresh_token(raw_token)
    row = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == token_hash)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if row.revoked:
        revoke_refresh_family(db, row.family_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected — session revoked",
        )
    if row.expires_at < now:
        row.revoked = 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    employee = db.query(models.Employee).filter(models.Employee.id == row.employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    row.revoked = 1
    db.commit()

    role = employee.role.value if hasattr(employee.role, "value") else str(employee.role)
    access = create_access_token(employee_id=employee.id, email=employee.email, role=role)
    refresh = issue_refresh_token(db, employee_id=employee.id, family_id=row.family_id)
    return access, refresh, employee


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = _hash_refresh_token(raw_token)
    row = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == token_hash)
        .first()
    )
    if row is None:
        return
    revoke_refresh_family(db, row.family_id)


def authenticate_employee(db: Session, email: str, password: str) -> Optional[models.Employee]:
    employee = db.query(models.Employee).filter(models.Employee.email == email).first()
    if not employee or not verify_password(password, employee.hashed_password):
        return None
    return employee


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> models.Employee:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    employee_id = payload.get("sub")
    if not employee_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    employee = db.query(models.Employee).filter(models.Employee.id == int(employee_id)).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return employee


def require_roles(*roles: str) -> Callable:
    allowed = {role.lower() for role in roles}

    def dependency(current_user: models.Employee = Depends(get_current_user)) -> models.Employee:
        user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(sorted(allowed))}",
            )
        return current_user

    return dependency


INSECURE_JWT_SECRETS = {
    "dev-only-change-me-in-production",
    "change-me",
    "secret",
    "password",
}

INSECURE_ADMIN_KEYS = {
    "dev_reset_key",
    "change-me-dev-reset-key",
    "change-me",
    "admin",
}


def warn_if_insecure_defaults() -> None:
    """Refuse to start in production with weak or missing security settings."""
    if APP_ENV != "production":
        return

    if not JWT_SECRET_KEY or JWT_SECRET_KEY in INSECURE_JWT_SECRETS or len(JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a strong secret (at least 32 characters) in production"
        )

    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if not cors_origins:
        raise RuntimeError("CORS_ORIGINS must be set to an explicit allowlist in production")

    admin_key = os.getenv("ADMIN_API_KEY")
    if admin_key is not None and admin_key in INSECURE_ADMIN_KEYS:
        raise RuntimeError("ADMIN_API_KEY must not use a known insecure default in production")
