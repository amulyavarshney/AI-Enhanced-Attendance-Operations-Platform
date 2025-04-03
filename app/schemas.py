from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from .models import AttendanceType, Role

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: int

    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    name: str
    email: str
    team_id: int
    role: Role = Role.EMPLOYEE
    hire_date: datetime = datetime.utcnow()

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    team: Team

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

class AttendanceUpdate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    date: datetime
    employee: Employee

    class Config:
        from_attributes = True

class TeamTrends(BaseModel):
    team_id: int
    total_employees: int
    present_count: int
    absent_count: int
    wfh_count: int
    half_day_count: int
    date: datetime

    class Config:
        from_attributes = True

class AIInsight(BaseModel):
    query: str
    summary: str
    details: Dict[str, Any]
    generated_at: datetime = datetime.utcnow()

    class Config:
        from_attributes = True 