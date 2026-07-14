from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging
from datetime import datetime, date, timezone
import os
import csv
import io

from .database import get_db, engine, Base
from . import models, schemas, crud
from .ai_service import AIService
from .auth import (
    authenticate_employee,
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
    warn_if_insecure_defaults,
)
from .middleware import RequestLoggingMiddleware
from .rate_limit import rate_limit_ai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

APP_ENV = os.getenv("APP_ENV", "development").lower()
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    if origin.strip()
]

warn_if_insecure_defaults()

# Role dependency shortcuts
AuthRequired = Depends(get_current_user)
ManagerOrAdmin = Depends(require_roles("admin", "manager"))
AdminOnly = Depends(require_roles("admin"))
AnyAuthenticated = Depends(require_roles("admin", "manager", "employee"))


app = FastAPI(
    title="AI-Enhanced Attendance Operations Platform",
    description="""
    A modern attendance management system with AI-powered insights and analytics.
    
    ## Features
    * 🔐 REST APIs for attendance management
    * 📊 PostgreSQL database with SQLAlchemy ORM
    * 🤖 AI-powered insights using Azure OpenAI
    * 👥 Team-based attendance tracking
    * 📈 Attendance trends and analytics
    
    ## Authentication
    Use `POST /auth/login` to obtain a JWT bearer token. Protected endpoints require
    `Authorization: Bearer <token>`. Roles: employee, manager, admin.
    """,
    version="1.0.0",
    contact={
        "name": "Amulya Varshney",
        "email": "amulyavarshney7@gmail.com",
        "url": "https://github.com/amulyavarshney/AI-Enhanced-Attendance-Operations-Platform.git"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if APP_ENV == "production" else (CORS_ORIGINS or ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Initialize AI service
ai_service = AIService()

# Health Check Endpoint
@app.get("/", tags=["Health Check"])
async def root():
    """
    Health check endpoint.
    
    Returns a welcome message and basic information about the API.
    """
    try:
        return {
            "message": "Welcome to AI-Enhanced Attendance Operations Platform",
            "version": "1.0.0",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health/live", tags=["Health Check"], summary="Liveness probe")
async def health_live():
    return {"status": "alive"}

@app.get("/health/ready", tags=["Health Check"], summary="Readiness probe")
async def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        logger.error(f"Readiness DB check failed: {e}")
        raise HTTPException(status_code=503, detail={"status": "not_ready", "database": "error"})

    ai_status = "unavailable"
    if ai_service.client:
        ai_status = ai_service.circuit_breaker.status()

    return {
        "status": "ready",
        "database": db_status,
        "ai": ai_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

# Auth Endpoints
@app.post("/auth/login",
          response_model=schemas.TokenResponse,
          tags=["Auth"],
          summary="Login",
          description="Authenticate with email and password to receive a JWT access token.")
async def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    employee = authenticate_employee(db, credentials.email, credentials.password)
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    role = employee.role.value if hasattr(employee.role, "value") else str(employee.role)
    token = create_access_token(employee_id=employee.id, email=employee.email, role=role)
    return schemas.TokenResponse(
        access_token=token,
        employee=schemas.Employee.model_validate(employee),
    )

@app.get("/auth/me",
         response_model=schemas.AuthMeResponse,
         tags=["Auth"],
         summary="Current User",
         description="Return the authenticated employee profile.")
async def auth_me(current_user: models.Employee = AuthRequired):
    return schemas.AuthMeResponse(employee=schemas.Employee.model_validate(current_user))

@app.post("/auth/change-password",
          tags=["Auth"],
          summary="Change Password",
          description="Change the authenticated user's password.")
async def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.Employee = AuthRequired,
):
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must differ from the current password")

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"message": "Password updated successfully"}

# Team Endpoints
@app.post("/teams", 
          response_model=schemas.Team,
          tags=["Teams"],
          summary="Create Team",
          description="Create a new team.",
          dependencies=[Depends(require_roles("admin", "manager"))])
async def create_team(
    team: schemas.TeamCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new team.
    
    Parameters:
    - **team**: Team details including name
    
    Returns:
    - Created team

    Raises:
    - 500: Internal server error
    """
    try:
        return crud.create_team(db, team)
    except Exception as e:
        logger.error(f"Error creating team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams",
         response_model=List[schemas.Team],
         tags=["Teams"],
         summary="Get All Teams",
         description="Get all teams.",
         dependencies=[Depends(get_current_user)])
async def get_teams(
    db: Session = Depends(get_db)
):
    """
    Get all teams.

    Returns:
    - List of teams

    Raises:
    - 500: Internal server error
    """
    try:
        return crud.get_teams(db)
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams/page",
         response_model=schemas.PaginatedTeams,
         tags=["Teams"],
         summary="Get Teams (Paginated)",
         dependencies=[Depends(get_current_user)])
async def get_teams_page(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
):
    items, total = crud.get_teams_paginated(db, skip=skip, limit=limit, search=search)
    return schemas.PaginatedTeams(items=items, total=total, skip=skip, limit=limit)

@app.get("/teams/{team_id}", 
         response_model=schemas.Team,
         tags=["Teams"],
         summary="Get Team",
         description="Get a team by ID.",
         dependencies=[Depends(get_current_user)])
async def get_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a team by ID.
    
    Parameters:
    - **team_id**: Team ID
    
    Returns:
    - Team details
    
    Raises:
    - 404: Team not found
    """
    team = crud.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@app.put("/teams/{team_id}",
         response_model=schemas.Team,
         tags=["Teams"],
         summary="Update Team",
         description="Update a team by ID.",
         dependencies=[Depends(require_roles("admin", "manager"))])
async def update_team(
    team_id: int,
    team: schemas.TeamUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a team by ID.

    Parameters:
    - **team_id**: Team ID
    - **team**: Team details
    
    Returns:
    - Updated team

    Raises:
    - 404: Team not found
    - 400: Invalid team details
    - 500: Internal server error
    """
    try:
        return crud.update_team(db, team_id, team)
    except Exception as e:
        logger.error(f"Error updating team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/teams/{team_id}",
         tags=["Teams"],
         summary="Delete Team",
         description="Delete a team by ID.",
         dependencies=[Depends(require_roles("admin"))])
async def delete_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a team by ID.
    
    Parameters:
    - **team_id**: Team ID
    
    Returns:
    - Success message
    
    Raises:
    - 404: Team not found
    - 500: Internal server error
    """
    try:
        crud.delete_team(db, team_id)
        return {"message": "Team deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams/{team_id}/employees",
         response_model=List[schemas.Employee],
         tags=["Teams"],
         summary="Get Employees by Team",
         description="Get employees by team ID.",
         dependencies=[Depends(get_current_user)])
async def get_employees_by_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get employees by team ID.
    """
    return crud.get_employees_by_team(db, team_id)

@app.get("/teams/{team_id}/attendance",
         response_model=List[schemas.Attendance],
         tags=["Teams"],
         summary="Get Attendance by Team",
         description="Get attendance by team ID.",
         dependencies=[Depends(get_current_user)])
async def get_attendance_by_team(
    team_id: int,
    start_date: Optional[date] = Query(None, description="Start date for filtering attendance records, format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="End date for filtering attendance records, format: YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Get attendance by team ID.

    Parameters:
    - **team_id**: Team ID
    - **start_date**: Start date (optional)
    - **end_date**: End date (optional)
    
    Returns:
    - List of attendance records

    Raises:
    - 404: Team not found
    - 500: Internal server error
    """
    try:
        return crud.get_attendance_by_team(db, team_id, start_date, end_date)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams/{team_id}/attendance/trends",
         response_model=List[schemas.TeamTrends],
         tags=["Teams"],
         summary="Get Attendance Trends by Team",
         description="Get attendance trends by team ID.",
         dependencies=[Depends(get_current_user)])
async def get_attendance_trends_by_team(
    team_id: int,
    start_date: Optional[date] = Query(None, description="Start date for filtering attendance trends, format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="End date for filtering attendance trends, format: YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Get attendance trends by team ID.

    Parameters:
    - **team_id**: Team ID
    - **start_date**: Start date (optional)
    - **end_date**: End date (optional)
    
    Returns:
    - List of attendance trends

    Raises:
    - 404: Team not found
    - 500: Internal server error
    """
    try:
        return crud.get_attendance_trends_by_team(db, team_id, start_date, end_date)
    except Exception as e:
        logger.error(f"Error fetching attendance trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Employee Endpoints
@app.post("/employees", 
          response_model=schemas.Employee,
          tags=["Employees"],
          summary="Create Employee",
          description="Create a new employee.",
          dependencies=[Depends(require_roles("admin", "manager"))])
async def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new employee.
    
    Parameters:
    - **employee**: Employee details
    
    Returns:
    - Created employee
    """
    try:
        return crud.create_employee(db, employee)
    except ValueError as e:
        detail = str(e)
        if "already exists" in detail.lower():
            raise HTTPException(status_code=409, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/employees",
         response_model=List[schemas.Employee],
         tags=["Employees"],
         summary="Get All Employees",
         description="Get all employees.",
         dependencies=[Depends(get_current_user)])
async def get_employees(
    db: Session = Depends(get_db)
):
    """
    Get all employees.

    Returns:
    - List of employees
    """
    return crud.get_employees(db)

@app.get("/employees/page",
         response_model=schemas.PaginatedEmployees,
         tags=["Employees"],
         summary="Get Employees (Paginated)",
         dependencies=[Depends(get_current_user)])
async def get_employees_page(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    team_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    items, total = crud.get_employees_paginated(
        db, skip=skip, limit=limit, team_id=team_id, search=search
    )
    return schemas.PaginatedEmployees(items=items, total=total, skip=skip, limit=limit)

@app.get("/employees/{employee_id}", 
         response_model=schemas.Employee,
         tags=["Employees"],
         summary="Get Employee",
         description="Get an employee by ID.",
         dependencies=[Depends(get_current_user)])
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an employee by ID.
    
    Parameters:
    - **employee_id**: Employee ID
    
    Returns:
    - Employee details
    
    Raises:
    - 404: Employee not found
    """
    employee = crud.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@app.put("/employees/{employee_id}",
         response_model=schemas.Employee,
         tags=["Employees"],
         summary="Update Employee",
         description="Update an existing employee.",
         dependencies=[Depends(require_roles("admin", "manager"))])
async def update_employee(
    employee_id: int,
    employee: schemas.EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing employee.

    Parameters:
    - **employee_id**: Employee ID
    - **employee**: Updated employee details
    
    Returns:
    - Updated employee

    Raises:
    - 404: Employee not found
    - 400: Invalid employee details
    - 500: Internal server error
    """
    try:
        return crud.update_employee(db, employee_id, employee)
    except Exception as e:
        logger.error(f"Error updating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/employees/{employee_id}",
         tags=["Employees"],
         summary="Delete Employee",
         description="Delete an existing employee.",
         dependencies=[Depends(require_roles("admin"))])
async def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an existing employee.

    Parameters:
    - **employee_id**: Employee ID

    Returns:
    - Success message

    Raises:
    - 404: Employee not found
    - 500: Internal server error
    """
    try:
        return crud.delete_employee(db, employee_id)
    except Exception as e:
        logger.error(f"Error deleting employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/employees/{employee_id}/attendance",
         response_model=List[schemas.Attendance],
         tags=["Employees"],
         summary="Get Employee Attendance",
         description="Get attendance records for a specific employee.",
         dependencies=[Depends(get_current_user)])
async def get_employee_attendance(
    employee_id: int,
    start_date: Optional[date] = Query(None, description="Start date for filtering attendance records, format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="End date for filtering attendance records, format: YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Get attendance records for a specific employee.

    Parameters:
    - **employee_id**: Employee ID
    - **start_date**: Start date (optional)
    - **end_date**: End date (optional)
    
    Returns:
    - List of attendance records

    Raises:
    - 404: Employee not found
    - 500: Internal server error
    """
    try:
        return crud.get_employee_attendance(db, employee_id, start_date, end_date)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Attendance Endpoints
@app.post("/attendance", 
          response_model=schemas.Attendance,
          tags=["Attendance"],
          summary="Create Attendance Record",
          description="Create a new attendance record for an employee.",
          dependencies=[Depends(get_current_user)])
async def create_attendance(
    attendance: schemas.AttendanceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new attendance record.
    
    Parameters:
    - **attendance**: Attendance record details including:
        - employee_id: The ID of the employee
        - status: Attendance status (present/absent/wfh/half_day/leave)
        - check_in: Check-in time (optional)
        - check_out: Check-out time (optional)
        - notes: Additional notes (optional)
    
    Returns:
    - Created attendance record
    
    Raises:
    - 400: If employee_id is invalid
    - 500: For server errors
    """
    try:
        return crud.create_attendance(db, attendance)
    except ValueError as e:
        logger.error(f"Value error creating attendance: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/attendance",
         response_model=List[schemas.Attendance],
         tags=["Attendance"],
         summary="Get All Attendance Records",
         description="Get all attendance records.",
         dependencies=[Depends(get_current_user)])
async def get_all_attendance(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date for filtering attendance records, format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="End date for filtering attendance records, format: YYYY-MM-DD")
): 
    """
    Get all attendance records.

    Parameters:
    - **start_date**: Start date (optional)
    - **end_date**: End date (optional)

    Returns:
    - List of attendance records

    Raises:
    - 500: For server errors
    """
    try:
        return crud.get_attendance_by_date(db, start_date, end_date)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/attendance/page",
         response_model=schemas.PaginatedAttendance,
         tags=["Attendance"],
         summary="Get Attendance (Paginated)",
         dependencies=[Depends(get_current_user)])
async def get_attendance_page(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
    status: Optional[models.AttendanceType] = Query(None),
):
    items, total = crud.get_attendance_paginated(
        db,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
        status=status,
    )
    return schemas.PaginatedAttendance(items=items, total=total, skip=skip, limit=limit)

@app.get("/attendance/export",
         tags=["Attendance"],
         summary="Export Attendance CSV",
         description="Download attendance records as CSV for a date range.",
         dependencies=[Depends(get_current_user)])
async def export_attendance_csv(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
):
    records = crud.get_attendance_by_date(db, start_date, end_date)
    if employee_id is not None:
        records = [r for r in records if r.employee_id == employee_id]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "employee_id", "date", "status", "check_in", "check_out", "notes",
        "created_at", "updated_at",
    ])
    for record in records:
        status = record.status.value if hasattr(record.status, "value") else record.status
        writer.writerow([
            record.id,
            record.employee_id,
            record.date.isoformat() if record.date else "",
            status,
            record.check_in.isoformat() if record.check_in else "",
            record.check_out.isoformat() if record.check_out else "",
            record.notes or "",
            record.created_at.isoformat() if record.created_at else "",
            record.updated_at.isoformat() if record.updated_at else "",
        ])

    buffer.seek(0)
    filename = f"attendance_export_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@app.get("/dashboard/stats",
         response_model=schemas.DashboardStats,
         tags=["Dashboard"],
         summary="Get Dashboard Stats",
         description="Get today's attendance and org summary statistics.",
         dependencies=[Depends(get_current_user)])
async def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        return crud.get_dashboard_stats(db)
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/dashboard/trends",
         response_model=List[schemas.TeamTrends],
         tags=["Dashboard"],
         summary="Get Attendance Trends",
         description="Get team attendance trends across all teams for a date range.",
         dependencies=[Depends(get_current_user)])
async def get_dashboard_trends(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="End date YYYY-MM-DD"),
    team_id: Optional[int] = Query(None, description="Optional team filter"),
):
    try:
        return crud.get_all_team_trends(db, start_date=start_date, end_date=end_date, team_id=team_id)
    except Exception as e:
        logger.error(f"Error fetching dashboard trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/attendance/{attendance_id}",
         response_model=schemas.Attendance,
         tags=["Attendance"],
         summary="Get Attendance Record",
         description="Get an attendance record by ID.",
         dependencies=[Depends(get_current_user)])
async def get_attendance(
    attendance_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an attendance record by ID.

    Parameters:
    - **attendance_id**: The ID of the attendance record to get
    
    Returns:
    - Attendance record details

    Raises:
    - 404: If attendance record not found
    - 500: For server errors
    """
    try:
        record = crud.get_attendance_by_id(db, attendance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Attendance record not found")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/attendance/{attendance_id}", 
         response_model=schemas.Attendance,
         tags=["Attendance"],
         summary="Update Attendance Record",
         description="Update an existing attendance record.",
         dependencies=[Depends(get_current_user)])
async def update_attendance(
    attendance_id: int,
    attendance: schemas.AttendanceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing attendance record.
    
    Parameters:
    - **attendance_id**: The ID of the attendance record to update
    - **attendance**: Updated attendance details
    
    Returns:
    - Updated attendance record
    
    Raises:
    - 404: If attendance record not found
    - 500: For server errors
    """
    try:
        return crud.update_attendance(db, attendance_id, attendance)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.delete("/attendance/{attendance_id}",
            tags=["Attendance"],
            summary="Delete Attendance Record",
            description="Delete an attendance record by ID.",
            status_code=204,
            dependencies=[Depends(require_roles("admin", "manager"))])
async def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an attendance record by ID.

    Parameters:
    - **attendance_id**: The ID of the attendance record to delete

    Raises:
    - 404: If attendance record not found
    - 500: For server errors
    """
    try:
        crud.delete_attendance(db, attendance_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/ai/insights",
         response_model=schemas.AIInsight,
         tags=["AI Insights"],
         summary="Get AI-Generated Insights",
         description="Get AI-powered insights about attendance patterns and trends.",
         dependencies=[Depends(require_roles("admin", "manager")), Depends(rate_limit_ai)])
async def get_ai_insights(
    query: str,
    db: Session = Depends(get_db)
):
    """
    Get AI-generated insights about attendance.
    
    Parameters:
    - **query**: Natural language query about attendance patterns
    
    Returns:
    - AI-generated insights including:
        - summary: Natural language summary of the insights
        - details: Structured data about the insights
        - generated_at: Timestamp of when the insights were generated
    
    Example Queries:
    - "Who was absent the most this month?"
    - "How many WFH days last week?"
    - "Give me a summary of attendance patterns"
    
    Raises:
    - 500: For server errors or OpenAI API issues
    """
    try:
        return await ai_service.generate_insights(query, db)
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/ai/sql-insights",
         response_model=schemas.AIInsight,
         tags=["AI Insights"],
         summary="Get SQL-based AI Insights",
         description="Convert natural language to SQL and get data-driven insights.",
         dependencies=[Depends(require_roles("admin", "manager")), Depends(rate_limit_ai)])
async def get_sql_insights(
    query: str,
    db: Session = Depends(get_db)
):
    """
    Convert a natural language query to SQL, execute it, and provide AI-powered insights.
    
    Parameters:
    - **query**: Natural language query about attendance data
    
    Returns:
    - AI-generated insights including:
        - summary: Analysis of the data retrieved
        - details: Contains the generated SQL, data, and other metadata
        - generated_at: Timestamp of when the insights were generated
    
    Example Queries:
    - "Show me attendance trends for the engineering team last month"
    - "Which employees have the highest WFH percentage?"
    - "Compare attendance rates between teams"
    
    Raises:
    - 500: For server errors, SQL generation issues, or query execution problems
    """
    try:
        return await ai_service.analyze_custom_query(query, db)
    except Exception as e:
        logger.error(f"Error generating SQL insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/ai/insights/history",
         response_model=List[schemas.AIInsight],
         tags=["AI Insights"],
         summary="Get Past AI Insights",
         description="Retrieve previously generated AI insights.",
         dependencies=[Depends(require_roles("admin", "manager"))])
async def get_insights_history(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve past AI insights from the database.
    
    Parameters:
    - **limit**: Maximum number of insights to return (1-100, default 10)
    
    Returns:
    - List of AI insights ordered by most recent first
    
    Raises:
    - 500: For server errors
    """
    try:
        return crud.get_ai_insights(db, limit)
    except Exception as e:
        logger.error(f"Error retrieving AI insights: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/audit-logs",
         response_model=List[schemas.AuditLog],
         tags=["Audit"],
         summary="List Audit Logs",
         description="Return recent mutating API actions. Admin only.",
         dependencies=[Depends(require_roles("admin"))])
async def list_audit_logs(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    return crud.get_audit_logs(db, limit=limit, skip=skip)

@app.get("/notifications",
         response_model=List[schemas.NotificationItem],
         tags=["Notifications"],
         summary="List Notifications",
         description="Return recent activity notifications derived from audit events.")
async def list_notifications(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
):
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role in ("admin", "manager"):
        logs = crud.get_audit_logs_for_actor(db, actor_id=None, limit=limit)
    else:
        logs = crud.get_audit_logs_for_actor(db, actor_id=current_user.id, limit=limit)

    return [
        schemas.NotificationItem(
            id=log.id,
            title=log.action,
            message=f"{log.method} {log.path} completed with status {log.status_code}",
            created_at=log.created_at,
            source="audit",
        )
        for log in logs
    ]

# Admin/Developer Endpoints

@app.post("/admin/reset-database", 
         tags=["Admin"],
         summary="Reset Database",
         description="Reset the database by dropping all tables and recreating the schema. Disabled in production.")
async def reset_database(
    api_key: str,
    background_tasks: BackgroundTasks,
    include_mock_data: bool = False,
    synchronous: bool = False
):
    """
    Reset the database by dropping all tables and recreating them from schema.
    
    This endpoint requires an API key and is disabled when APP_ENV=production.
    """
    if APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Database reset is disabled in production")

    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_API_KEY is not configured. Set it in the environment to enable this endpoint."
        )

    if api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if synchronous:
        await _reset_database(include_mock_data)
        return {"message": "Database reset completed successfully."}
    else:
        background_tasks.add_task(_reset_database, include_mock_data)
        return {"message": "Database reset initiated. This process will take a few seconds to complete."}

def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _run_sql_file(relative_path: str) -> None:
    """Execute a multi-statement SQL file via the DBAPI connection."""
    sql_path = os.path.join(_project_root(), relative_path)
    if not os.path.isfile(sql_path):
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.execute(sql)
        raw_conn.commit()
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()

async def _reset_database(include_mock_data: bool):
    """Execute database reset using project SQL scripts."""
    try:
        logger.info("Dropping all tables and resetting database...")
        Base.metadata.drop_all(bind=engine)

        logger.info("Creating schema from scripts/schema.sql...")
        _run_sql_file(os.path.join("scripts", "schema.sql"))

        if include_mock_data:
            logger.info("Adding mock data from scripts/mock_data.sql...")
            _run_sql_file(os.path.join("scripts", "mock_data.sql"))

        logger.info("Database reset completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False