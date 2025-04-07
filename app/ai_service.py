from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
import os
import logging
from openai import AzureOpenAI
from . import crud, models, schemas

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            logger.info("Azure OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI client: {str(e)}")
            self.client = None
        
    async def generate_insights(self, query: str, db: Session) -> schemas.AIInsight:
        if not self.client:
            logger.error("Azure OpenAI client not initialized.")
            return schemas.AIInsight(
                query=query,
                summary="AI insights are currently unavailable. Please try again later.",
                details={"error": "Azure OpenAI client not initialized"}
            )
            
        try:
            # Get relevant attendance data based on the query
            if "absent" in query.lower():
                # Get attendance data for the last 30 days
                start_date = date.today() - timedelta(days=30)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_absent_analysis_prompt(attendance_data)
                details = self._process_absent_data(attendance_data)
            elif "wfh" in query.lower():
                # Get WFH data for the last week
                start_date = date.today() - timedelta(days=7)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_wfh_analysis_prompt(attendance_data)
                details = self._process_wfh_data(attendance_data)
            elif "leave" in query.lower():
                # Get leave data for the last month
                start_date = date.today() - timedelta(days=30)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_leave_analysis_prompt(attendance_data)
                details = self._process_leave_data(attendance_data)
            else:
                # Default to general attendance summary
                start_date = date.today() - timedelta(days=7)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_general_summary_prompt(attendance_data)
                details = self._process_general_data(attendance_data)
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_MODEL"),
                messages=[
                    {"role": "system", "content": "You are an AI assistant that provides insights about employee attendance data."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return schemas.AIInsight(
                query=query,
                summary=response.choices[0].message.content.strip(),
                details=details
            )
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return schemas.AIInsight(
                query=query,
                summary="An error occurred while generating insights. Please try again later.",
                details={"error": str(e)}
            )
    
    def _get_attendance_data(self, db: Session, start_date: date):
        return db.query(models.Attendance).filter(
            models.Attendance.date >= start_date
        ).all()
    
    def _get_employee_name(self, employee):
        """Get the full name of an employee"""
        return f"{employee.first_name} {employee.last_name}"
    
    def _process_absent_data(self, attendance_data):
        employee_absences = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.ABSENT:
                employee_name = self._get_employee_name(record.employee)
                employee_absences[employee_name] = employee_absences.get(employee_name, 0) + 1
        
        return {
            "employee_absences": employee_absences,
            "total_absences": sum(employee_absences.values()),
            "most_absent_employee": max(employee_absences.items(), key=lambda x: x[1])[0] if employee_absences else None
        }
    
    def _process_wfh_data(self, attendance_data):
        wfh_count = sum(1 for record in attendance_data if record.status == models.AttendanceType.WFH)
        total_days = len(attendance_data)
        
        employee_wfh = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.WFH:
                employee_name = self._get_employee_name(record.employee)
                employee_wfh[employee_name] = employee_wfh.get(employee_name, 0) + 1
        
        return {
            "wfh_count": wfh_count,
            "total_days": total_days,
            "wfh_percentage": (wfh_count / total_days * 100) if total_days > 0 else 0,
            "employee_wfh": employee_wfh
        }
    
    def _process_leave_data(self, attendance_data):
        leave_count = sum(1 for record in attendance_data if record.status == models.AttendanceType.LEAVE)
        total_days = len(attendance_data)
        
        employee_leave = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.LEAVE:
                employee_name = self._get_employee_name(record.employee)
                employee_leave[employee_name] = employee_leave.get(employee_name, 0) + 1
        
        return {
            "leave_count": leave_count,
            "total_days": total_days,
            "leave_percentage": (leave_count / total_days * 100) if total_days > 0 else 0,
            "employee_leave": employee_leave,
            "most_leave_employee": max(employee_leave.items(), key=lambda x: x[1])[0] if employee_leave else None
        }
    
    def _process_general_data(self, attendance_data):
        status_counts = {
            models.AttendanceType.PRESENT: 0,
            models.AttendanceType.ABSENT: 0,
            models.AttendanceType.WFH: 0,
            models.AttendanceType.HALF_DAY: 0,
            models.AttendanceType.LEAVE: 0
        }
        
        for record in attendance_data:
            if record.status in status_counts:
                status_counts[record.status] += 1
        
        return {
            "status_counts": {status.value: count for status, count in status_counts.items()},
            "total_records": len(attendance_data)
        }
    
    def _create_absent_analysis_prompt(self, attendance_data):
        details = self._process_absent_data(attendance_data)
        
        prompt = "Based on the following attendance data, analyze who was absent the most:\n\n"
        for employee, count in details["employee_absences"].items():
            prompt += f"{employee}: {count} days absent\n"
        
        prompt += f"\nTotal absences: {details['total_absences']}"
        prompt += "\nPlease provide a natural language summary of the absenteeism patterns."
        return prompt
    
    def _create_wfh_analysis_prompt(self, attendance_data):
        details = self._process_wfh_data(attendance_data)
        
        prompt = f"Based on the attendance data for the past week:\n"
        prompt += f"Total WFH days: {details['wfh_count']}\n"
        prompt += f"Total attendance records: {details['total_days']}\n"
        prompt += f"WFH percentage: {details['wfh_percentage']:.1f}%\n\n"
        
        prompt += "WFH days by employee:\n"
        for employee, count in details["employee_wfh"].items():
            prompt += f"{employee}: {count} days\n"
            
        prompt += "\nPlease provide a natural language summary of the WFH patterns."
        return prompt
    
    def _create_leave_analysis_prompt(self, attendance_data):
        details = self._process_leave_data(attendance_data)
        
        prompt = f"Based on the attendance data for the past month:\n"
        prompt += f"Total leave days: {details['leave_count']}\n"
        prompt += f"Total attendance records: {details['total_days']}\n"
        prompt += f"Leave percentage: {details['leave_percentage']:.1f}%\n\n"
        
        prompt += "Leave days by employee:\n"
        for employee, count in details["employee_leave"].items():
            prompt += f"{employee}: {count} days\n"
            
        prompt += "\nPlease provide a natural language summary of the leave patterns."
        return prompt
    
    def _create_general_summary_prompt(self, attendance_data):
        details = self._process_general_data(attendance_data)
        
        prompt = "Based on the attendance data for the past week:\n\n"
        for status, count in details["status_counts"].items():
            prompt += f"{status}: {count} days\n"
        
        prompt += f"\nTotal records: {details['total_records']}"
        prompt += "\nPlease provide a natural language summary of the attendance patterns."
        return prompt 