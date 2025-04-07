from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Date, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class AttendanceType(enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half_day"
    wfh = "wfh"
    leave = "leave"

class Role(enum.Enum):
    employee = "employee"
    manager = "manager"
    admin = "admin"

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    employees = relationship("Employee", back_populates="team")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    role = Column(Enum(Role), default=Role.employee)
    team_id = Column(Integer, ForeignKey("teams.id"))
    hire_date = Column(Date, default=datetime.utcnow().date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", back_populates="employees")
    attendance_records = relationship("Attendance", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date, default=datetime.utcnow().date)
    status = Column(Enum(AttendanceType))
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    employee = relationship("Employee", back_populates="attendance_records")

class TeamTrends(Base):
    __tablename__ = "team_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    date = Column(Date, nullable=False)
    total_employees = Column(Integer, nullable=False)
    present_count = Column(Integer, nullable=False)
    absent_count = Column(Integer, nullable=False)
    wfh_count = Column(Integer, nullable=False)
    half_day_count = Column(Integer, nullable=False)
    leave_count = Column(Integer, nullable=False)
    
    team = relationship("Team")

class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    details = Column(JSONB)
    generated_at = Column(DateTime, default=datetime.utcnow)

