"""Row-level visibility helpers for role-based data access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status

from . import models


def role_of(user: models.Employee) -> str:
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return role.lower()


@dataclass(frozen=True)
class DataScope:
    role: str
    employee_id: Optional[int] = None
    team_id: Optional[int] = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"

    @property
    def is_employee(self) -> bool:
        return self.role == "employee"


def resolve_scope(user: models.Employee) -> DataScope:
    role = role_of(user)
    if role == "admin":
        return DataScope(role=role)
    if role == "manager":
        if user.team_id is None:
            # Managers without a team only see themselves until assigned.
            return DataScope(role=role, employee_id=user.id)
        return DataScope(role=role, team_id=user.team_id)
    return DataScope(role=role, employee_id=user.id)


def can_view_employee(scope: DataScope, target: models.Employee) -> bool:
    if scope.is_admin:
        return True
    if scope.employee_id is not None:
        return target.id == scope.employee_id
    if scope.team_id is not None:
        return target.team_id == scope.team_id
    return False


def can_view_attendance(scope: DataScope, record: models.Attendance, employee: Optional[models.Employee]) -> bool:
    if scope.is_admin:
        return True
    if scope.employee_id is not None:
        return record.employee_id == scope.employee_id
    if scope.team_id is not None:
        if employee is None:
            return False
        return employee.team_id == scope.team_id
    return False


def ensure_can_view_employee(scope: DataScope, target: Optional[models.Employee]) -> models.Employee:
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not can_view_employee(scope, target):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this employee")
    return target


def ensure_can_view_attendance(
    scope: DataScope,
    record: Optional[models.Attendance],
    employee: Optional[models.Employee] = None,
) -> models.Attendance:
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    if not can_view_attendance(scope, record, employee):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this attendance record")
    return record


def ensure_can_view_team(scope: DataScope, team_id: int, user: models.Employee) -> None:
    if scope.is_admin:
        return
    if scope.team_id is not None:
        if scope.team_id != team_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view that team")
        return
    if scope.employee_id is not None:
        if user.team_id != team_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view that team")
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view that team")
