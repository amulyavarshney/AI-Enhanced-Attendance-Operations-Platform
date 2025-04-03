from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from .database import get_db
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
    * 🔐 Secure REST APIs for attendance management
    * 📊 PostgreSQL database with SQLAlchemy ORM
    * 🤖 AI-powered insights using OpenAI
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
    try:
        return crud.get_employee_attendance(db, employee_id)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        - status: Attendance status (present/absent/wfh/half_day)
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
    except Exception as e:
        logger.error(f"Error creating attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    except Exception as e:
        logger.error(f"Error updating attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    
    Raises:
    - 404: If team not found
    - 500: For server errors
    """
    try:
        return crud.get_team_attendance_trends(db, team_id)
    except Exception as e:
        logger.error(f"Error fetching team trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error") 