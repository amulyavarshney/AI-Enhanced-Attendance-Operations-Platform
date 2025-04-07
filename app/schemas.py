from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from .models import AttendanceType, Role

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
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
    hire_date: date = date.today()

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    employee_id: int
    status: AttendanceType
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    notes: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceType] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    notes: Optional[str] = None

class Attendance(AttendanceBase):
    id: int
    date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TeamTrends(BaseModel):
    team_id: int
    total_employees: int
    date: date
    present_count: int
    absent_count: int
    wfh_count: int
    half_day_count: int
    leave_count: int

    class Config:
        from_attributes = True

class AIInsight(BaseModel):
    query: str
    summary: str
    details: Dict[str, Any]
    generated_at: datetime = datetime.utcnow()

    class Config:
        from_attributes = True 