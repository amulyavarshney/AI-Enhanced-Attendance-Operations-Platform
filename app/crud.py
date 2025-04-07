from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, exists
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from . import models, schemas
import logging

logger = logging.getLogger(__name__)

# Employee CRUD
def get_employee(db: Session, employee_id: int) -> Optional[models.Employee]:
    """Get an employee by ID"""
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def create_employee(db: Session, employee: schemas.EmployeeCreate) -> models.Employee:
    """Create a new employee"""
    db_employee = models.Employee(**employee.model_dump())
    db.add(db_employee)
    
    try:
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating employee: {str(e)}")
        raise ValueError(f"Failed to create employee: {str(e)}")

# Team CRUD
def get_team(db: Session, team_id: int) -> Optional[models.Team]:
    """Get a team by ID"""
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def create_team(db: Session, team: schemas.TeamCreate) -> models.Team:
    """Create a new team"""
    db_team = models.Team(**team.model_dump())
    db.add(db_team)
    
    try:
        db.commit()
        db.refresh(db_team)
        return db_team
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating team: {str(e)}")
        raise ValueError(f"Failed to create team: {str(e)}")

# Attendance CRUD
def get_attendance(db: Session, attendance_id: int) -> Optional[models.Attendance]:
    """Get an attendance record by ID"""
    return db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

def get_employee_attendance(db: Session, employee_id: int) -> List[models.Attendance]:
    """Get attendance records for an employee"""
    return db.query(models.Attendance).filter(
        models.Attendance.employee_id == employee_id
    ).order_by(models.Attendance.date.desc()).all()

def create_attendance(db: Session, attendance: schemas.AttendanceCreate) -> models.Attendance:
    """Create a new attendance record with validation"""
    # Check if employee exists
    employee = get_employee(db, attendance.employee_id)
    if not employee:
        raise ValueError("Employee not found")
    
    # Check for existing attendance record for the same date
    today = date.today()
    existing = db.query(models.Attendance).filter(
        models.Attendance.employee_id == attendance.employee_id,
        models.Attendance.date == today
    ).first()
    
    if existing:
        # Update the existing record instead of creating a new one
        attendance_data = {k: v for k, v in attendance.model_dump().items() if v is not None}
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
    attendance_data = attendance.model_dump(exclude_unset=True)
    attendance_data["date"] = today
    
    db_attendance = models.Attendance(**attendance_data)
    db.add(db_attendance)
    
    try:
        db.commit()
        db.refresh(db_attendance)
        
        # Update team trends after adding attendance
        update_team_trends(db, employee.team_id)
        
        return db_attendance
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attendance: {str(e)}")
        raise ValueError(f"Failed to create attendance: {str(e)}")

def update_attendance(db: Session, attendance_id: int, attendance: schemas.AttendanceUpdate) -> models.Attendance:
    """Update an existing attendance record with validation"""
    # Get the attendance record
    db_attendance = get_attendance(db, attendance_id)
    if not db_attendance:
        raise ValueError("Attendance record not found")
    
    # Get the employee to verify team_id for trend updates
    employee = get_employee(db, db_attendance.employee_id)
    if not employee:
        raise ValueError("Employee not found")
    
    # Update the attendance record
    attendance_data = {k: v for k, v in attendance.model_dump().items() if v is not None}
    for key, value in attendance_data.items():
        setattr(db_attendance, key, value)
    
    try:
        db.commit()
        db.refresh(db_attendance)
        
        # Update team trends after updating attendance
        update_team_trends(db, employee.team_id)
        
        return db_attendance
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating attendance: {str(e)}")
        raise ValueError(f"Failed to update attendance: {str(e)}")

# Team Trends
def update_team_trends(db: Session, team_id: int) -> None:
    """Update team attendance trends for today"""
    try:
        team = get_team(db, team_id)
        if not team:
            logger.error(f"Team not found: {team_id}")
            return
        
        today = date.today()
        
        # Get all employees in the team
        team_employees = db.query(models.Employee).filter(
            models.Employee.team_id == team_id
        ).all()
        
        total_employees = len(team_employees)
        if total_employees == 0:
            return
        
        employee_ids = [emp.id for emp in team_employees]
        
        # Get attendance counts for today with a single optimized query
        attendance_counts = db.query(
            models.Attendance.status,
            func.count(models.Attendance.id).label('count')
        ).filter(
            models.Attendance.employee_id.in_(employee_ids),
            models.Attendance.date == today
        ).group_by(models.Attendance.status).all()
        
        # Create a dictionary of counts
        counts = {
            models.AttendanceType.PRESENT: 0,
            models.AttendanceType.ABSENT: 0,
            models.AttendanceType.WFH: 0,
            models.AttendanceType.HALF_DAY: 0,
            models.AttendanceType.LEAVE: 0
        }
        
        for status, count in attendance_counts:
            counts[status] = count
        
        # Check if trend record exists for today
        existing_trend = db.query(models.TeamTrends).filter(
            models.TeamTrends.team_id == team_id,
            models.TeamTrends.date == today
        ).first()
        
        if existing_trend:
            # Update existing record
            existing_trend.total_employees = total_employees
            existing_trend.present_count = counts[models.AttendanceType.PRESENT]
            existing_trend.absent_count = counts[models.AttendanceType.ABSENT]
            existing_trend.wfh_count = counts[models.AttendanceType.WFH]
            existing_trend.half_day_count = counts[models.AttendanceType.HALF_DAY]
            existing_trend.leave_count = counts[models.AttendanceType.LEAVE]
        else:
            # Create new record
            new_trend = models.TeamTrends(
                team_id=team_id,
                date=today,
                total_employees=total_employees,
                present_count=counts[models.AttendanceType.PRESENT],
                absent_count=counts[models.AttendanceType.ABSENT],
                wfh_count=counts[models.AttendanceType.WFH],
                half_day_count=counts[models.AttendanceType.HALF_DAY],
                leave_count=counts[models.AttendanceType.LEAVE]
            )
            db.add(new_trend)
        
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating team trends: {str(e)}")

def get_team_attendance_trends(db: Session, team_id: int) -> List[schemas.TeamTrends]:
    """Get attendance trends for a team"""
    # Check if team exists
    team = get_team(db, team_id)
    if not team:
        raise ValueError("Team not found")
    
    today = date.today()
    
    # Get existing trends from the database
    trends = db.query(models.TeamTrends).filter(
        models.TeamTrends.team_id == team_id
    ).order_by(models.TeamTrends.date.desc()).all()
    
    # If no trends exist for today, calculate and create one
    if not trends or trends[0].date != today:
        update_team_trends(db, team_id)
        
        # Fetch the newly created trend
        trends = db.query(models.TeamTrends).filter(
            models.TeamTrends.team_id == team_id
        ).order_by(models.TeamTrends.date.desc()).all()
    
    return trends

def save_ai_insight(db: Session, insight: schemas.AIInsight) -> models.AIInsight:
    """Save an AI insight to the database"""
    db_insight = models.AIInsight(
        query=insight.query,
        summary=insight.summary,
        details=insight.details,
        generated_at=insight.generated_at
    )
    
    db.add(db_insight)
    
    try:
        db.commit()
        db.refresh(db_insight)
        return db_insight
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving AI insight: {str(e)}")
        raise ValueError(f"Failed to save AI insight: {str(e)}")

def get_ai_insights(db: Session, limit: int = 10) -> List[models.AIInsight]:
    """Get saved AI insights from the database, ordered by most recent first"""
    return db.query(models.AIInsight).order_by(models.AIInsight.generated_at.desc()).limit(limit).all() 