from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List
from . import models, schemas

def get_employee_attendance(db: Session, employee_id: int) -> List[models.Attendance]:
    return db.query(models.Attendance).filter(models.Attendance.employee_id == employee_id).all()

def create_attendance(db: Session, attendance: schemas.AttendanceCreate) -> models.Attendance:
    db_attendance = models.Attendance(**attendance.model_dump())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def update_attendance(db: Session, attendance_id: int, attendance: schemas.AttendanceUpdate) -> models.Attendance:
    db_attendance = db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()
    if not db_attendance:
        raise ValueError("Attendance record not found")
    
    for key, value in attendance.model_dump().items():
        setattr(db_attendance, key, value)
    
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

def get_team_attendance_trends(db: Session, team_id: int) -> List[schemas.TeamTrends]:
    today = datetime.utcnow().date()
    
    # Get all employees in the team
    team_employees = db.query(models.Employee).filter(models.Employee.team_id == team_id).all()
    employee_ids = [emp.id for emp in team_employees]
    
    # Get attendance counts for today
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
    
    return [schemas.TeamTrends(
        team_id=team_id,
        total_employees=total_employees,
        present_count=counts[models.AttendanceType.PRESENT],
        absent_count=absent_count,
        wfh_count=counts[models.AttendanceType.WFH],
        half_day_count=counts[models.AttendanceType.HALF_DAY],
        date=today
    )] 