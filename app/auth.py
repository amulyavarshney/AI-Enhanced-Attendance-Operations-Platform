"""JWT authentication and role-based access control."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
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


def create_access_token(*, employee_id: int, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(employee_id),
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
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


def warn_if_insecure_defaults() -> None:
    if APP_ENV == "production" and JWT_SECRET_KEY == "dev-only-change-me-in-production":
        raise RuntimeError("JWT_SECRET_KEY must be set to a strong secret in production")
