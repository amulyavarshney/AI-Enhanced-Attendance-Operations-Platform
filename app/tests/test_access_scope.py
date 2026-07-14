"""Unit tests for role-based data scoping helpers."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.access import (
    can_view_attendance,
    can_view_employee,
    ensure_can_view_employee,
    ensure_can_view_team,
    resolve_scope,
)
from app.models import Role


def _user(*, employee_id=1, role=Role.employee, team_id=10):
    return SimpleNamespace(id=employee_id, role=role, team_id=team_id)


def test_admin_scope_is_unrestricted():
    scope = resolve_scope(_user(role=Role.admin, team_id=None))
    assert scope.is_admin
    assert scope.employee_id is None
    assert scope.team_id is None


def test_manager_scope_uses_team():
    scope = resolve_scope(_user(role=Role.manager, team_id=7))
    assert scope.is_manager
    assert scope.team_id == 7
    assert scope.employee_id is None


def test_manager_without_team_falls_back_to_self():
    scope = resolve_scope(_user(role=Role.manager, team_id=None, employee_id=42))
    assert scope.employee_id == 42
    assert scope.team_id is None


def test_employee_scope_is_self_only():
    scope = resolve_scope(_user(role=Role.employee, employee_id=9, team_id=3))
    assert scope.is_employee
    assert scope.employee_id == 9


def test_can_view_employee_rules():
    admin = resolve_scope(_user(role=Role.admin))
    manager = resolve_scope(_user(role=Role.manager, team_id=2))
    employee = resolve_scope(_user(role=Role.employee, employee_id=5, team_id=2))

    teammate = _user(employee_id=8, team_id=2)
    outsider = _user(employee_id=9, team_id=99)
    self_user = _user(employee_id=5, team_id=2)

    assert can_view_employee(admin, outsider)
    assert can_view_employee(manager, teammate)
    assert not can_view_employee(manager, outsider)
    assert can_view_employee(employee, self_user)
    assert not can_view_employee(employee, teammate)


def test_ensure_can_view_employee_forbidden():
    scope = resolve_scope(_user(role=Role.employee, employee_id=1, team_id=1))
    with pytest.raises(HTTPException) as exc:
        ensure_can_view_employee(scope, _user(employee_id=2, team_id=1))
    assert exc.value.status_code == 403


def test_ensure_can_view_team_for_employee():
    user = _user(role=Role.employee, employee_id=1, team_id=4)
    scope = resolve_scope(user)
    ensure_can_view_team(scope, 4, user)
    with pytest.raises(HTTPException) as exc:
        ensure_can_view_team(scope, 9, user)
    assert exc.value.status_code == 403


def test_can_view_attendance_for_manager_team():
    scope = resolve_scope(_user(role=Role.manager, team_id=2))
    record = SimpleNamespace(employee_id=8)
    assert can_view_attendance(scope, record, _user(employee_id=8, team_id=2))
    assert not can_view_attendance(scope, record, _user(employee_id=8, team_id=3))
