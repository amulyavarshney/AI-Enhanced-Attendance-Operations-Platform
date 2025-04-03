from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class AttendanceType(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    WFH = "wfh"
    LEAVE = "leave"
    HOLIDAY = "holiday"

class Role(enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR = "hr"
    ADMIN = "admin"

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    role = Column(Enum(Role), default=Role.EMPLOYEE)
    hire_date = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", back_populates="employees")
    attendance_records = relationship("Attendance", back_populates="employee")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    employees = relationship("Employee", back_populates="team")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(AttendanceType))
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)
    
    employee = relationship("Employee", back_populates="attendance_records") 