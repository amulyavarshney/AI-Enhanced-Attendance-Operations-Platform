from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime, date
import os
import subprocess
import sqlalchemy
import time

from .database import get_db, engine, Base
from . import models, schemas, crud
from .ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    Currently, the API is open for testing. In production, implement proper authentication.
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
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI service
ai_service = AIService()

# Health Check Endpoint
@app.get("/", tags=["Health Check"])
async def root():
    """
    Health check endpoint.
    
    Returns a welcome message and basic information about the API.
    """
    return {
        "message": "Welcome to AI-Enhanced Attendance Operations Platform",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Team Endpoints
@app.post("/teams", 
          response_model=schemas.Team,
          tags=["Teams"],
          summary="Create Team",
          description="Create a new team.")
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
    """
    try:
        return crud.create_team(db, team)
    except Exception as e:
        logger.error(f"Error creating team: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/teams/{team_id}", 
         response_model=schemas.Team,
         tags=["Teams"],
         summary="Get Team",
         description="Get a team by ID.")
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

# Employee Endpoints
@app.post("/employees", 
          response_model=schemas.Employee,
          tags=["Employees"],
          summary="Create Employee",
          description="Create a new employee.")
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
    except Exception as e:
        logger.error(f"Error creating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/employees/{employee_id}", 
         response_model=schemas.Employee,
         tags=["Employees"],
         summary="Get Employee",
         description="Get an employee by ID.")
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

# Attendance Endpoints
@app.get("/attendance/{employee_id}", 
         response_model=List[schemas.Attendance],
         tags=["Attendance"],
         summary="Get Employee Attendance",
         description="Retrieve all attendance records for a specific employee.")
async def get_employee_attendance(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attendance records for a specific employee.
    
    Parameters:
    - **employee_id**: The unique identifier of the employee
    
    Returns:
    - List of attendance records for the specified employee
    
    Raises:
    - 404: If employee not found
    - 500: For server errors
    """
    employee = crud.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    try:
        return crud.get_employee_attendance(db, employee_id)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/attendance", 
          response_model=schemas.Attendance,
          tags=["Attendance"],
          summary="Create Attendance Record",
          description="Create a new attendance record for an employee.")
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

@app.put("/attendance/{attendance_id}", 
         response_model=schemas.Attendance,
         tags=["Attendance"],
         summary="Update Attendance Record",
         description="Update an existing attendance record.")
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

@app.get("/attendance/team/{team_id}/trends",
         response_model=List[schemas.TeamTrends],
         tags=["Analytics"],
         summary="Get Team Attendance Trends",
         description="Retrieve attendance trends and statistics for a specific team.")
async def get_team_attendance_trends(
    team_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attendance trends for a team.
    
    Parameters:
    - **team_id**: The ID of the team
    
    Returns:
    - List of team attendance trends including:
        - total_employees: Total number of employees in the team
        - present_count: Number of present employees
        - absent_count: Number of absent employees
        - wfh_count: Number of employees working from home
        - half_day_count: Number of employees with half-day attendance
        - leave_count: Number of employees on leave
    
    Raises:
    - 404: If team not found
    - 500: For server errors
    """
    try:
        return crud.get_team_attendance_trends(db, team_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching team trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/ai/insights",
         response_model=schemas.AIInsight,
         tags=["AI Insights"],
         summary="Get AI-Generated Insights",
         description="Get AI-powered insights about attendance patterns and trends.")
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

# Admin/Developer Endpoints

@app.post("/admin/reset-database", 
         tags=["Admin"],
         summary="Reset Database",
         description="Reset the database by dropping all tables and recreating the schema")
async def reset_database(
    api_key: str,
    background_tasks: BackgroundTasks,
    include_mock_data: bool = False,
    synchronous: bool = False  # Add synchronous option for testing
):
    """
    Reset the database by dropping all tables and recreating them from schema.
    
    This endpoint requires an API key and should only be used in development/testing environments.
    
    Parameters:
    - **api_key**: Security API key to authorize database reset
    - **include_mock_data**: Whether to include mock data after reset (default: False)
    - **synchronous**: Run the reset synchronously instead of as a background task (default: False)
    
    Returns:
    - Success message
    
    Raises:
    - 401: Unauthorized if API key is invalid
    - 500: Internal server error if reset fails
    """
    # Validate API key - in production, use a more secure mechanism
    expected_api_key = os.getenv("ADMIN_API_KEY", "dev_reset_key")
    if api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if synchronous:
        # Run database reset synchronously (for testing)
        await _reset_database(include_mock_data)
        return {"message": "Database reset completed successfully."}
    else:
        # Run database reset as a background task to avoid timeout
        background_tasks.add_task(_reset_database, include_mock_data)
        return {"message": "Database reset initiated. This process will take a few seconds to complete."}

async def _reset_database(include_mock_data: bool):
    """Execute database reset"""
    from sqlalchemy.schema import DropTable, DropSchema
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy import text
    import subprocess
    import os

    # Define compiler for PostgreSQL's CASCADE option for DROP TABLE
    @compiles(DropTable, "postgresql")
    def _compile_drop_table(element, compiler, **kwargs):
        return compiler.visit_drop_table(element) + " CASCADE"
    
    try:
        # Get database connection
        db = SessionLocal()
        
        # Drop all tables
        logger.info("Dropping all tables and resetting database...")
        Base.metadata.drop_all(bind=engine)
        
        # Execute schema SQL to recreate tables, functions, triggers, etc.
        logger.info("Creating schema from SQL files...")
        _execute_schema_sql()
        
        # Add mock data if requested
        if include_mock_data:
            logger.info("Adding mock data...")
            _add_mock_data()
        
        logger.info("Database reset completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def _execute_schema_sql():
    """Execute schema.sql file to create triggers and functions"""
    import subprocess
    import os
    from urllib.parse import urlparse
    
    try:
        # Parse DATABASE_URL to get credentials for psql command
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/attendance_db")
        parsed_url = urlparse(db_url)
        
        username = parsed_url.username or "postgres"
        password = parsed_url.password or "postgres"
        hostname = parsed_url.hostname or "localhost"
        port = parsed_url.port or 5432
        database = parsed_url.path[1:] or "attendance_db"  # Remove leading slash
        
        # Path to the schema SQL file
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   "sql", "schema", "schema.sql")
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # Execute schema SQL using psql
        result = subprocess.run(
            [
                "psql",
                "-h", hostname,
                "-p", str(port),
                "-U", username,
                "-d", database,
                "-f", schema_path
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check for errors
        if result.returncode != 0:
            logger.error(f"Error executing schema SQL: {result.stderr}")
            raise Exception(f"Error executing schema SQL: {result.stderr}")
        
        logger.info("Schema SQL executed successfully")
        return True
    except Exception as e:
        logger.error(f"Error executing schema SQL: {e}")
        raise

def _add_mock_data():
    """Add mock data to the database"""
    import subprocess
    import os
    from urllib.parse import urlparse
    
    try:
        # Parse DATABASE_URL to get credentials for psql command
        db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/attendance_db")
        parsed_url = urlparse(db_url)
        
        username = parsed_url.username or "postgres"
        password = parsed_url.password or "postgres"
        hostname = parsed_url.hostname or "localhost"
        port = parsed_url.port or 5432
        database = parsed_url.path[1:] or "attendance_db"  # Remove leading slash
        
        # Path to the mock data SQL file
        mock_data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      "sql", "data", "mock_data.sql")
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # Execute mock data SQL using psql
        result = subprocess.run(
            [
                "psql",
                "-h", hostname,
                "-p", str(port),
                "-U", username,
                "-d", database,
                "-f", mock_data_path
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check for errors
        if result.returncode != 0:
            logger.error(f"Error adding mock data: {result.stderr}")
            raise Exception(f"Error adding mock data: {result.stderr}")
        
        logger.info("Mock data added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding mock data: {e}")
        raise