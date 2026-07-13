"""Unit tests that do not require a live database."""

import pytest

from app.ai_service import AIService
from app.auth import create_access_token, decode_access_token, hash_password, verify_password
from app.models import AttendanceType


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
