from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional
from . import models, schemas
import logging

logger = logging.getLogger(__name__)

# Employee CRUD
def get_employees(db: Session) -> List[models.Employee]:
    """Get all employees"""
    return db.query(models.Employee).all()

def get_employee(db: Session, employee_id: int) -> Optional[models.Employee]:
    """Get an employee by ID"""
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def create_employee(db: Session, employee: schemas.EmployeeCreate) -> models.Employee:
    """Create a new employee"""
    from .auth import hash_password

    employee_data = employee.model_dump(exclude={"password"})
    password = employee.password
    db_employee = models.Employee(**employee_data)
    if password:
        db_employee.hashed_password = hash_password(password)
    db.add(db_employee)
    
    try:
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating employee: {str(e)}")
        raise ValueError(f"Failed to create employee: {str(e)}")

def update_employee(db: Session, employee_id: int, employee: schemas.EmployeeUpdate) -> models.Employee:
    """Update an employee by ID"""
    from .auth import hash_password

    db_employee = get_employee(db, employee_id)
    if not db_employee:
        raise ValueError("Employee not found")
    
    employee_data = {k: v for k, v in employee.model_dump().items() if v is not None and k != "password"}
    for key, value in employee_data.items():
        setattr(db_employee, key, value)

    if employee.password:
        db_employee.hashed_password = hash_password(employee.password)
    
    try:
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating employee: {str(e)}")
        raise ValueError(f"Failed to update employee: {str(e)}")

def delete_employee(db: Session, employee_id: int) -> None:
    """Delete an employee by ID"""
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        raise ValueError("Employee not found")
    
    try:
        db.delete(db_employee)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting employee: {str(e)}")
        raise ValueError(f"Failed to delete employee: {str(e)}")

# Team CRUD
def get_teams(db: Session) -> List[models.Team]:
    """Get all teams"""
    return db.query(models.Team).all()

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

def update_team(db: Session, team_id: int, team: schemas.TeamUpdate) -> models.Team:
    """Update a team by ID"""
    db_team = get_team(db, team_id)
    if not db_team:
        raise ValueError("Team not found")

    team_data = {k: v for k, v in team.model_dump().items() if v is not None}
    for key, value in team_data.items():
        setattr(db_team, key, value)
    
    try:
        db.commit()
        db.refresh(db_team)
        return db_team 
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating team: {str(e)}")
        raise ValueError(f"Failed to update team: {str(e)}")

def delete_team(db: Session, team_id: int) -> None:
    """Delete a team by ID"""
    db_team = get_team(db, team_id)
    if not db_team:
        raise ValueError("Team not found")
    
    try:
        db.delete(db_team)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting team: {str(e)}")
        raise ValueError(f"Failed to delete team: {str(e)}")

def get_employees_by_team(db: Session, team_id: int) -> List[models.Employee]:
    """Get employees by team ID"""
    return db.query(models.Employee).filter(models.Employee.team_id == team_id).all()

def get_attendance_by_team(db: Session, team_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Attendance]:
    """Get attendance by team ID"""
    employees = get_employees_by_team(db, team_id)
    employee_ids = [emp.id for emp in employees]
    query = db.query(models.Attendance).filter(models.Attendance.employee_id.in_(employee_ids))
    if start_date:
        query = query.filter(models.Attendance.date >= start_date)
    if end_date:
        query = query.filter(models.Attendance.date <= end_date)
    return query.all()

def get_attendance_trends_by_team(db: Session, team_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.TeamTrends]:
    """Get attendance trends by team ID"""
    attendance = get_attendance_by_team(db, team_id, start_date, end_date)
    trends = []
    # get datewise trends
    date_trends = {}
    for attendance in attendance:
        date = attendance.date
        if date not in date_trends:
            date_trends[date] = models.TeamTrends(
                team_id=team_id,
                date=date,
                total_employees=0,
                present_count=0,
                absent_count=0,
                wfh_count=0,
                half_day_count=0,
                leave_count=0
            )
        date_trends[date].total_employees += 1
        if attendance.status == models.AttendanceType.present:
            date_trends[date].present_count += 1
        elif attendance.status == models.AttendanceType.absent:
            date_trends[date].absent_count += 1
        elif attendance.status == models.AttendanceType.wfh:
            date_trends[date].wfh_count += 1
        elif attendance.status == models.AttendanceType.half_day:
            date_trends[date].half_day_count += 1
        elif attendance.status == models.AttendanceType.leave:
            date_trends[date].leave_count += 1
    for date, trend in date_trends.items():
        trends.append(trend)
    return trends

# Attendance CRUD
def get_attendance(db: Session, attendance_id: int) -> Optional[models.Attendance]:
    """Get an attendance record by ID"""
    return db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

def get_employee_attendance(db: Session, employee_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Attendance]:
    """Get attendance records for an employee"""
    query = db.query(models.Attendance).filter(
        models.Attendance.employee_id == employee_id
    )
    if start_date:
        query = query.filter(models.Attendance.date >= start_date)
    if end_date:
        query = query.filter(models.Attendance.date <= end_date)
    return query.order_by(models.Attendance.date.desc()).all()

def create_attendance(db: Session, attendance: schemas.AttendanceCreate) -> models.Attendance:
    """Create a new attendance record with validation"""
    employee = get_employee(db, attendance.employee_id)
    if not employee:
        raise ValueError("Employee not found")

    target_date = attendance.date or date.today()

    existing = db.query(models.Attendance).filter(
        models.Attendance.employee_id == attendance.employee_id,
        models.Attendance.date == target_date
    ).first()

    if existing:
        attendance_data = {k: v for k, v in attendance.model_dump().items() if v is not None}
        for key, value in attendance_data.items():
            setattr(existing, key, value)

        try:
            db.commit()
            db.refresh(existing)
            update_team_trends(db, employee.team_id, target_date)
            return existing
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating existing attendance: {str(e)}")
            raise ValueError(f"Failed to update existing attendance: {str(e)}")

    attendance_data = attendance.model_dump(exclude_unset=True)
    attendance_data["date"] = target_date

    db_attendance = models.Attendance(**attendance_data)
    db.add(db_attendance)

    try:
        db.commit()
        db.refresh(db_attendance)
        update_team_trends(db, employee.team_id, target_date)
        return db_attendance
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attendance: {str(e)}")
        raise ValueError(f"Failed to create attendance: {str(e)}")

def get_attendance_by_date(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[models.Attendance]:
    """Get attendance records by date"""
    query = db.query(models.Attendance)
    if start_date:
        query = query.filter(models.Attendance.date >= start_date)
    if end_date:
        query = query.filter(models.Attendance.date <= end_date)
    return query.all()

def get_attendance_by_id(db: Session, attendance_id: int) -> Optional[models.Attendance]:
    """Get an attendance record by ID"""
    return db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

def update_attendance(db: Session, attendance_id: int, attendance: schemas.AttendanceUpdate) -> models.Attendance:
    """Update an existing attendance record with validation"""
    db_attendance = get_attendance(db, attendance_id)
    if not db_attendance:
        raise ValueError("Attendance record not found")

    employee = get_employee(db, db_attendance.employee_id)
    if not employee:
        raise ValueError("Employee not found")

    attendance_data = {k: v for k, v in attendance.model_dump().items() if v is not None}
    for key, value in attendance_data.items():
        setattr(db_attendance, key, value)

    try:
        db.commit()
        db.refresh(db_attendance)
        update_team_trends(db, employee.team_id, db_attendance.date)
        return db_attendance
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating attendance: {str(e)}")
        raise ValueError(f"Failed to update attendance: {str(e)}")

def delete_attendance(db: Session, attendance_id: int) -> None:
    """Delete an attendance record by ID"""
    db_attendance = get_attendance(db, attendance_id)
    if not db_attendance:
        raise ValueError("Attendance record not found")

    employee = get_employee(db, db_attendance.employee_id)
    team_id = employee.team_id if employee else None
    attendance_date = db_attendance.date

    try:
        db.delete(db_attendance)
        db.commit()
        if team_id is not None:
            update_team_trends(db, team_id, attendance_date)
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting attendance: {str(e)}")
        raise ValueError(f"Failed to delete attendance: {str(e)}")

# Team Trends
def update_team_trends(db: Session, team_id: int, target_date: Optional[date] = None) -> None:
    """Update team attendance trends for a given date (defaults to today)"""
    try:
        team = get_team(db, team_id)
        if not team:
            logger.error(f"Team not found: {team_id}")
            return

        trend_date = target_date or date.today()

        team_employees = db.query(models.Employee).filter(
            models.Employee.team_id == team_id
        ).all()

        total_employees = len(team_employees)
        if total_employees == 0:
            return

        employee_ids = [emp.id for emp in team_employees]

        attendance_counts = db.query(
            models.Attendance.status,
            func.count(models.Attendance.id).label('count')
        ).filter(
            models.Attendance.employee_id.in_(employee_ids),
            models.Attendance.date == trend_date
        ).group_by(models.Attendance.status).all()

        counts = {
            models.AttendanceType.present: 0,
            models.AttendanceType.absent: 0,
            models.AttendanceType.wfh: 0,
            models.AttendanceType.half_day: 0,
            models.AttendanceType.leave: 0
        }

        for status, count in attendance_counts:
            counts[status] = count

        existing_trend = db.query(models.TeamTrends).filter(
            models.TeamTrends.team_id == team_id,
            models.TeamTrends.date == trend_date
        ).first()

        if existing_trend:
            existing_trend.total_employees = total_employees
            existing_trend.present_count = counts[models.AttendanceType.present]
            existing_trend.absent_count = counts[models.AttendanceType.absent]
            existing_trend.wfh_count = counts[models.AttendanceType.wfh]
            existing_trend.half_day_count = counts[models.AttendanceType.half_day]
            existing_trend.leave_count = counts[models.AttendanceType.leave]
        else:
            new_trend = models.TeamTrends(
                team_id=team_id,
                date=trend_date,
                total_employees=total_employees,
                present_count=counts[models.AttendanceType.present],
                absent_count=counts[models.AttendanceType.absent],
                wfh_count=counts[models.AttendanceType.wfh],
                half_day_count=counts[models.AttendanceType.half_day],
                leave_count=counts[models.AttendanceType.leave]
            )
            db.add(new_trend)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating team trends: {str(e)}")

def get_team_attendance_trends(db: Session, team_id: int) -> List[schemas.TeamTrends]:
    """Get attendance trends for a team"""
    team = get_team(db, team_id)
    if not team:
        raise ValueError("Team not found")

    today = date.today()

    trends = db.query(models.TeamTrends).filter(
        models.TeamTrends.team_id == team_id
    ).order_by(models.TeamTrends.date.desc()).all()

    if not trends or trends[0].date != today:
        update_team_trends(db, team_id, today)

        trends = db.query(models.TeamTrends).filter(
            models.TeamTrends.team_id == team_id
        ).order_by(models.TeamTrends.date.desc()).all()

    return trends

def save_ai_insight(db: Session, insight: schemas.AIInsightCreate) -> models.AIInsight:
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
