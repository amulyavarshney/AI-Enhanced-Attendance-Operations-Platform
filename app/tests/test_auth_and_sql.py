"""Unit tests that do not require a live database."""

import pytest
from fastapi import HTTPException

from app.ai_service import AIService
from app.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.models import AttendanceType
from app.rate_limit import SlidingWindowRateLimiter
from app.circuit_breaker import CircuitBreaker
from app import auth as auth_module


def test_password_hash_roundtrip():
    hashed = hash_password("Admin123!")
    assert verify_password("Admin123!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_roundtrip():
    token = create_access_token(employee_id=12, email="admin@example.com", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "12"
    assert payload["email"] == "admin@example.com"
    assert payload["role"] == "admin"


def test_ai_sql_rejects_mutations():
    service = AIService.__new__(AIService)
    with pytest.raises(ValueError, match="forbidden|Only SELECT|Multiple"):
        service._validate_readonly_sql("DELETE FROM employees WHERE id = 1")


def test_ai_sql_allows_select_and_adds_limit():
    service = AIService.__new__(AIService)
    safe = service._validate_readonly_sql("SELECT id, email FROM employees")
    assert safe.upper().startswith("SELECT")
    assert "LIMIT" in safe.upper()


def test_ai_sql_blocks_unknown_tables():
    service = AIService.__new__(AIService)
    with pytest.raises(ValueError, match="disallowed relation"):
        service._validate_readonly_sql("SELECT * FROM pg_user LIMIT 10")


def test_attendance_type_enum_members_are_lowercase():
    assert AttendanceType.present.value == "present"
    assert not hasattr(AttendanceType, "PRESENT")


def test_rate_limiter_blocks_after_max():
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
    limiter.check("client-a")
    limiter.check("client-a")
    with pytest.raises(HTTPException) as exc:
        limiter.check("client-a")
    assert exc.value.status_code == 429


def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60)
    assert breaker.allow_request()
    breaker.record_failure()
    assert breaker.allow_request()
    breaker.record_failure()
    assert breaker.is_open
    assert not breaker.allow_request()
    breaker.record_success()
    assert breaker.allow_request()


def test_production_rejects_insecure_jwt_secret(monkeypatch):
    monkeypatch.setattr(auth_module, "APP_ENV", "production")
    monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "dev-only-change-me-in-production")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth_module.warn_if_insecure_defaults()


def test_production_rejects_missing_cors(monkeypatch):
    monkeypatch.setattr(auth_module, "APP_ENV", "production")
    monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "a" * 40)
    monkeypatch.setenv("CORS_ORIGINS", "")
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        auth_module.warn_if_insecure_defaults()


def test_development_allows_default_secret(monkeypatch):
    monkeypatch.setattr(auth_module, "APP_ENV", "development")
    monkeypatch.setattr(auth_module, "JWT_SECRET_KEY", "dev-only-change-me-in-production")
    auth_module.warn_if_insecure_defaults()
