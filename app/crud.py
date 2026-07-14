from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from datetime import date
from typing import List, Optional, Dict, Any, Tuple
from . import models, schemas
import logging

logger = logging.getLogger(__name__)

# Employee CRUD
def get_employees(
    db: Session,
    *,
    employee_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> List[models.Employee]:
    """Get employees, optionally scoped to one employee or one team."""
    query = db.query(models.Employee)
    if employee_id is not None:
        query = query.filter(models.Employee.id == employee_id)
    elif team_id is not None:
        query = query.filter(models.Employee.team_id == team_id)
    return query.all()

def get_employee(db: Session, employee_id: int) -> Optional[models.Employee]:
    """Get an employee by ID"""
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def create_employee(db: Session, employee: schemas.EmployeeCreate) -> models.Employee:
    """Create a new employee"""
    from .auth import hash_password

    existing = db.query(models.Employee).filter(models.Employee.email == employee.email).first()
    if existing:
        raise ValueError("Employee with this email already exists")

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
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating employee: {str(e)}")
        raise ValueError("Employee with this email already exists")
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
def get_teams(db: Session, *, team_id: Optional[int] = None) -> List[models.Team]:
    """Get teams, optionally scoped to a single team."""
    query = db.query(models.Team)
    if team_id is not None:
        query = query.filter(models.Team.id == team_id)
    return query.all()

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

def get_attendance_by_date(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    *,
    employee_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> List[models.Attendance]:
    """Get attendance records by date, optionally scoped to employee or team."""
    query = db.query(models.Attendance)
    if start_date:
        query = query.filter(models.Attendance.date >= start_date)
    if end_date:
        query = query.filter(models.Attendance.date <= end_date)
    if employee_id is not None:
        query = query.filter(models.Attendance.employee_id == employee_id)
    elif team_id is not None:
        query = query.join(models.Employee).filter(models.Employee.team_id == team_id)
    return query.all()

def get_attendance_by_id(db: Session, attendance_id: int) -> Optional[models.Attendance]:
    """Get an attendance record by ID"""
    return db.query(models.Attendance).filter(models.Attendance.id == attendance_id).first()

def get_employee_attendance_for_date(
    db: Session, employee_id: int, target_date: date
) -> Optional[models.Attendance]:
    return (
        db.query(models.Attendance)
        .filter(
            models.Attendance.employee_id == employee_id,
            models.Attendance.date == target_date,
        )
        .first()
    )

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


def get_employees_paginated(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    team_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    search: Optional[str] = None,
) -> tuple[List[models.Employee], int]:
    query = db.query(models.Employee)
    if employee_id is not None:
        query = query.filter(models.Employee.id == employee_id)
    elif team_id is not None:
        query = query.filter(models.Employee.team_id == team_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                models.Employee.first_name.ilike(pattern),
                models.Employee.last_name.ilike(pattern),
                models.Employee.email.ilike(pattern),
            )
        )
    total = query.count()
    items = query.order_by(models.Employee.id).offset(skip).limit(limit).all()
    return items, total


def get_teams_paginated(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    team_id: Optional[int] = None,
) -> tuple[List[models.Team], int]:
    query = db.query(models.Team)
    if team_id is not None:
        query = query.filter(models.Team.id == team_id)
    if search:
        query = query.filter(models.Team.name.ilike(f"%{search}%"))
    total = query.count()
    items = query.order_by(models.Team.id).offset(skip).limit(limit).all()
    return items, total


def get_attendance_paginated(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[int] = None,
    team_id: Optional[int] = None,
    status: Optional[models.AttendanceType] = None,
) -> tuple[List[models.Attendance], int]:
    query = db.query(models.Attendance)
    if start_date:
        query = query.filter(models.Attendance.date >= start_date)
    if end_date:
        query = query.filter(models.Attendance.date <= end_date)
    if employee_id is not None:
        query = query.filter(models.Attendance.employee_id == employee_id)
    elif team_id is not None:
        query = query.join(models.Employee).filter(models.Employee.team_id == team_id)
    if status is not None:
        query = query.filter(models.Attendance.status == status)
    total = query.count()
    items = (
        query.order_by(models.Attendance.date.desc(), models.Attendance.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def get_all_team_trends(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    team_id: Optional[int] = None,
) -> List[models.TeamTrends]:
    query = db.query(models.TeamTrends)
    if team_id is not None:
        query = query.filter(models.TeamTrends.team_id == team_id)
    if start_date:
        query = query.filter(models.TeamTrends.date >= start_date)
    if end_date:
        query = query.filter(models.TeamTrends.date <= end_date)
    return query.order_by(models.TeamTrends.date.asc()).all()


def get_dashboard_stats(
    db: Session,
    *,
    employee_id: Optional[int] = None,
    team_id: Optional[int] = None,
) -> Dict[str, Any]:
    today = date.today()
    employee_query = db.query(func.count(models.Employee.id))
    if employee_id is not None:
        employee_query = employee_query.filter(models.Employee.id == employee_id)
    elif team_id is not None:
        employee_query = employee_query.filter(models.Employee.team_id == team_id)
    total_employees = employee_query.scalar() or 0

    if employee_id is not None:
        total_teams = 1 if db.query(models.Employee.team_id).filter(models.Employee.id == employee_id).scalar() else 0
    elif team_id is not None:
        total_teams = 1
    else:
        total_teams = db.query(func.count(models.Team.id)).scalar() or 0

    attendance_query = db.query(models.Attendance.status, func.count(models.Attendance.id)).filter(
        models.Attendance.date == today
    )
    if employee_id is not None:
        attendance_query = attendance_query.filter(models.Attendance.employee_id == employee_id)
    elif team_id is not None:
        attendance_query = attendance_query.join(models.Employee).filter(models.Employee.team_id == team_id)
    status_rows = attendance_query.group_by(models.Attendance.status).all()

    counts = {
        models.AttendanceType.present: 0,
        models.AttendanceType.absent: 0,
        models.AttendanceType.wfh: 0,
        models.AttendanceType.half_day: 0,
        models.AttendanceType.leave: 0,
    }
    for status, count in status_rows:
        counts[status] = count

    present_count = counts[models.AttendanceType.present]
    wfh_count = counts[models.AttendanceType.wfh]
    absent_count = counts[models.AttendanceType.absent]
    half_day_count = counts[models.AttendanceType.half_day]
    leave_count = counts[models.AttendanceType.leave]
    recorded = present_count + wfh_count + absent_count + half_day_count + leave_count

    return {
        "date": today,
        "total_employees": total_employees,
        "total_teams": total_teams,
        "present_count": present_count,
        "absent_count": absent_count,
        "wfh_count": wfh_count,
        "half_day_count": half_day_count,
        "leave_count": leave_count,
        "present_percentage": round((present_count / total_employees) * 100) if total_employees else 0,
        "wfh_percentage": round((wfh_count / total_employees) * 100) if total_employees else 0,
        "absent_percentage": round(((absent_count + leave_count) / total_employees) * 100) if total_employees else 0,
        "records_today": recorded,
    }


def create_audit_log(
    db: Session,
    *,
    method: str,
    path: str,
    status_code: int,
    action: str,
    actor_id: Optional[int] = None,
    actor_email: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> models.AuditLog:
    entry = models.AuditLog(
        actor_id=actor_id,
        actor_email=actor_email,
        method=method,
        path=path,
        status_code=status_code,
        action=action,
        details=details or {},
    )
    db.add(entry)
    try:
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving audit log: {e}")
        raise


def get_audit_logs(db: Session, limit: int = 50, skip: int = 0) -> List[models.AuditLog]:
    return (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_audit_logs_for_actor(
    db: Session,
    *,
    actor_id: Optional[int] = None,
    limit: int = 20,
) -> List[models.AuditLog]:
    query = db.query(models.AuditLog)
    if actor_id is not None:
        query = query.filter(models.AuditLog.actor_id == actor_id)
    return query.order_by(models.AuditLog.created_at.desc()).limit(limit).all()


def get_audit_logs_for_team(
    db: Session,
    *,
    team_id: int,
    limit: int = 20,
) -> List[models.AuditLog]:
    return (
        db.query(models.AuditLog)
        .join(models.Employee, models.AuditLog.actor_id == models.Employee.id)
        .filter(models.Employee.team_id == team_id)
        .order_by(models.AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
