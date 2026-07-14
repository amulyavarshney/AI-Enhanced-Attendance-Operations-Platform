from pydantic import BaseModel, Field
from datetime import datetime, date as date_type, timezone
from typing import Optional, List, Dict, Any
from .models import AttendanceType, Role


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class TeamUpdate(TeamBase):
    pass

class Team(TeamBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role: Role = Role.employee
    team_id: int

class EmployeeCreate(EmployeeBase):
    hire_date: date_type = Field(default_factory=date_type.today)
    password: Optional[str] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Role] = None
    team_id: Optional[int] = None
    password: Optional[str] = None

class Employee(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    employee: Employee

class AuthMeResponse(BaseModel):
    employee: Employee

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    employee: Employee

class AttendanceBase(BaseModel):
    employee_id: int
    status: AttendanceType
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    date: date_type = Field(default_factory=date_type.today)

class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceType] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    notes: Optional[str] = None

class Attendance(AttendanceBase):
    id: int
    date: date_type
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamTrends(BaseModel):
    team_id: int
    total_employees: int
    date: date_type
    present_count: int
    absent_count: int
    wfh_count: int
    half_day_count: int
    leave_count: int

    class Config:
        from_attributes = True

class AIInsightCreate(BaseModel):
    query: str
    summary: str
    details: Dict[str, Any]
    generated_at: datetime = Field(default_factory=utc_now_naive)

class AIInsight(AIInsightCreate):
    id: int

    class Config:
        from_attributes = True

class PaginatedEmployees(BaseModel):
    items: List[Employee]
    total: int
    skip: int
    limit: int

class PaginatedTeams(BaseModel):
    items: List[Team]
    total: int
    skip: int
    limit: int

class PaginatedAttendance(BaseModel):
    items: List[Attendance]
    total: int
    skip: int
    limit: int

class DashboardStats(BaseModel):
    date: date_type
    total_employees: int
    total_teams: int
    present_count: int
    absent_count: int
    wfh_count: int
    half_day_count: int
    leave_count: int
    present_percentage: int
    wfh_percentage: int
    absent_percentage: int
    records_today: int

class AuditLog(BaseModel):
    id: int
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    method: str
    path: str
    status_code: int
    action: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationItem(BaseModel):
    id: int
    title: str
    message: str
    created_at: datetime
    source: str = "audit"
