from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging

from .database import get_db
from . import models, schemas, crud
from .ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI-Enhanced Attendance Operations Platform")

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

@app.get("/")
async def root():
    return {"message": "Welcome to AI-Enhanced Attendance Operations Platform"}

@app.get("/attendance/{employee_id}", response_model=List[schemas.Attendance])
async def get_employee_attendance(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """Fetch attendance records for a specific employee"""
    try:
        return crud.get_employee_attendance(db, employee_id)
    except Exception as e:
        logger.error(f"Error fetching attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/attendance", response_model=schemas.Attendance)
async def create_attendance(
    attendance: schemas.AttendanceCreate,
    db: Session = Depends(get_db)
):
    """Create a new attendance entry"""
    try:
        return crud.create_attendance(db, attendance)
    except Exception as e:
        logger.error(f"Error creating attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/attendance/{attendance_id}", response_model=schemas.Attendance)
async def update_attendance(
    attendance_id: int,
    attendance: schemas.AttendanceUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing attendance entry"""
    try:
        return crud.update_attendance(db, attendance_id, attendance)
    except Exception as e:
        logger.error(f"Error updating attendance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/attendance/team/{team_id}/trends")
async def get_team_attendance_trends(
    team_id: int,
    db: Session = Depends(get_db)
):
    """Get attendance trends for a team"""
    try:
        return crud.get_team_attendance_trends(db, team_id)
    except Exception as e:
        logger.error(f"Error fetching team trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/ai/insights")
async def get_ai_insights(
    query: str,
    db: Session = Depends(get_db)
):
    """Get AI-generated insights about attendance"""
    try:
        return await ai_service.generate_insights(query, db)
    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 