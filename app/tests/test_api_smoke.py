"""API smoke tests using FastAPI TestClient (no database required for these cases)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_live():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_root_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_protected_route_requires_auth():
    response = client.get("/teams")
    assert response.status_code == 401


def test_login_validation_requires_body():
    response = client.post("/auth/login", json={})
    assert response.status_code == 422


def test_notifications_require_auth():
    response = client.get("/notifications")
    assert response.status_code == 401


def test_refresh_requires_body():
    response = client.post("/auth/refresh", json={})
    assert response.status_code == 422


def test_logout_requires_body():
    response = client.post("/auth/logout", json={})
    assert response.status_code == 422


def test_audit_logs_require_auth():
    response = client.get("/audit-logs")
    assert response.status_code == 401


def test_self_check_in_requires_auth():
    response = client.post("/attendance/check-in")
    assert response.status_code == 401


def test_self_check_out_requires_auth():
    response = client.post("/attendance/check-out")
    assert response.status_code == 401


def test_attendance_today_requires_auth():
    response = client.get("/attendance/today")
    assert response.status_code == 401
