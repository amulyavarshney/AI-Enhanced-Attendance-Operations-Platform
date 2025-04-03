from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, exists
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from . import models, schemas
import logging

logger = logging.getLogger(__name__)

def get_employee_attendance(db: Session, employee_id: int) -> List[models.Attendance]:
    """Get attendance records for an employee"""
    return db.query(models.Attendance).filter(
        models.Attendance.employee_id == employee_id
    ).order_by(models.Attendance.date.desc()).all()

def create_attendance(db: Session, attendance: schemas.AttendanceCreate) -> models.Attendance:
    """Create a new attendance record with validation"""
    # Check if employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == attendance.employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    # Check for existing attendance record for the same date
    today = datetime.utcnow().date()
    existing = db.query(models.Attendance).filter(
        models.Attendance.employee_id == attendance.employee_id,
        func.date(models.Attendance.date) == today
    ).first()
    
    if existing:
        # Update the existing record instead of creating a new one
        attendance_data = attendance.model_dump()
        for key, value in attendance_data.items():
            setattr(existing, key, value)
        
        try:
            db.commit()
            db.refresh(existing)
            return existing
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating existing attendance: {str(e)}")
            raise ValueError(f"Failed to update existing attendance: {str(e)}")
    
    # Create new attendance record
    attendance_data = attendance.model_dump()
    attendance_data["date"] = datetime.utcnow()
    
    db_attendance = models.Attendance(**attendance_data)
    db.add(db_attendance)
    
    try:
        db.commit()
        db.refresh(db_attendance)
        return db_attendance
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attendance: {str(e)}")
        raise ValueError(f"Failed to create attendance: {str(e)}")

def update_attendance(db: Session, attendance_id: int, attendance: schemas.AttendanceUpdate) -> models.Attendance:
    """Update an existing attendance record with validation"""
    # Get the attendance record
    db_attendance = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not db_attendance:
        raise ValueError("Attendance record not found")
    
    # Check if employee exists
    employee = db.query(models.Employee).filter(models.Employee.id == attendance.employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    # Update the attendance record
    attendance_data = attendance.model_dump()
    for key, value in attendance_data.items():
        setattr(db_attendance, key, value)
    
    try:
        db.commit()
        db.refresh(db_attendance)
        return db_attendance
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating attendance: {str(e)}")
        raise ValueError(f"Failed to update attendance: {str(e)}")

def get_team_attendance_trends(db: Session, team_id: int) -> List[schemas.TeamTrends]:
    """Get attendance trends for a team with optimized query"""
    # Check if team exists
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise ValueError("Team not found")
    
    today = datetime.utcnow().date()
    
    # Get all employees in the team with a single query
    team_employees = db.query(models.Employee).filter(models.Employee.team_id == team_id).all()
    if not team_employees:
        # Return empty trends if no employees in team
        return [schemas.TeamTrends(
            team_id=team_id,
            total_employees=0,
            present_count=0,
            absent_count=0,
            wfh_count=0,
            half_day_count=0,
            date=today
        )]
    
    employee_ids = [emp.id for emp in team_employees]
    
    # Get attendance counts for today with a single optimized query
    attendance_counts = db.query(
        models.Attendance.status,
        func.count(models.Attendance.id).label('count')
    ).filter(
        models.Attendance.employee_id.in_(employee_ids),
        func.date(models.Attendance.date) == today
    ).group_by(models.Attendance.status).all()
    
    # Create a dictionary of counts
    counts = {
        models.AttendanceType.PRESENT: 0,
        models.AttendanceType.ABSENT: 0,
        models.AttendanceType.WFH: 0,
        models.AttendanceType.HALF_DAY: 0
    }
    
    for status, count in attendance_counts:
        counts[status] = count
    
    # Calculate absent count
    total_employees = len(employee_ids)
    present_count = sum(counts.values())
    absent_count = total_employees - present_count
    
    # Create and return the team trends
    return [schemas.TeamTrends(
        team_id=team_id,
        total_employees=total_employees,
        present_count=counts[models.AttendanceType.PRESENT],
        absent_count=absent_count,
        wfh_count=counts[models.AttendanceType.WFH],
        half_day_count=counts[models.AttendanceType.HALF_DAY],
        date=today
    )]

def get_employee(db: Session, employee_id: int) -> Optional[models.Employee]:
    """Get an employee by ID"""
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def get_team(db: Session, team_id: int) -> Optional[models.Team]:
    """Get a team by ID"""
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def get_attendance(db: Session, attendance_id: int) -> Optional[models.Attendance]:
    """Get an attendance record by ID"""
    return db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first() 