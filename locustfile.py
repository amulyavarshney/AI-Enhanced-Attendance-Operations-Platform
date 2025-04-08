import os
import time
import random
import json
import string
import logging
import warnings
from typing import Dict, List, Optional, Union
from locust import HttpUser, task, between, events, constant_pacing, TaskSet
from datetime import datetime, date, timedelta
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("locust")

# Suppress SSL warnings when verification is disabled
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# TEST CONFIGURATION
# These settings control the test behavior
TEST_DURATION_SECONDS = 60  # 1 minute test
TARGET_RPS_MIN = 10
TARGET_RPS_MAX = 50
MAX_USERS = 20  # Maximum number of simulated users
VERIFY_SSL = False  # Set to False to disable SSL certificate verification for deployed endpoints

# Define enums matching the application models
class AttendanceType(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    WFH = "wfh"
    LEAVE = "leave"

class Role(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"

# Global tracking of created resources for cleanup
created_teams = []
created_employees = []
created_attendance_records = []

# Admin API key for database reset
ADMIN_API_KEY = "dev_reset_key"

# Cleanup event handler - runs at test end
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up all test data after the load test is complete"""
    logger.info("🧹 Starting test data cleanup...")
    
    # Get a client for cleanup
    cleanup_client = None
    try:
        if environment.runner and hasattr(environment.runner, "user_classes") and environment.runner.user_classes:
            # Create a new client for cleanup
            user_class = environment.runner.user_classes[0]
            cleanup_client = user_class(environment)
            cleanup_client.client.timeout = 30.0
            cleanup_client.client.verify = VERIFY_SSL
        else:
            logger.warning("Could not create cleanup client - runner or user classes not available")
            return
    except Exception as e:
        logger.error(f"Failed to create cleanup client: {str(e)}")
        return
    
    # Delete attendance records first (child records)
    cleanup_successful = True
    for attendance_id in created_attendance_records[:]:
        try:
            response = cleanup_client.client.delete(
                f"/attendance/{attendance_id}", 
                name="/attendance/{id} [cleanup]",
                timeout=10.0,
                verify=VERIFY_SSL
            )
            if response.status_code in [200, 204, 404]:
                created_attendance_records.remove(attendance_id)
                logger.info(f"✅ Deleted attendance record: {attendance_id}")
            else:
                logger.warning(f"❌ Failed to delete attendance record {attendance_id}: HTTP {response.status_code}")
                cleanup_successful = False
        except Exception as e:
            logger.error(f"❌ Error deleting attendance record {attendance_id}: {str(e)}")
            cleanup_successful = False
    
    # Delete employees next
    for employee_id in created_employees[:]:
        try:
            response = cleanup_client.client.delete(
                f"/employees/{employee_id}", 
                name="/employees/{id} [cleanup]",
                timeout=10.0,
                verify=VERIFY_SSL
            )
            if response.status_code in [200, 204, 404]:
                created_employees.remove(employee_id)
                logger.info(f"✅ Deleted employee: {employee_id}")
            else:
                logger.warning(f"❌ Failed to delete employee {employee_id}: HTTP {response.status_code}")
                cleanup_successful = False
        except Exception as e:
            logger.error(f"❌ Error deleting employee {employee_id}: {str(e)}")
            cleanup_successful = False
    
    # Delete teams last (parent records)
    for team_id in created_teams[:]:
        try:
            response = cleanup_client.client.delete(
                f"/teams/{team_id}", 
                name="/teams/{id} [cleanup]",
                timeout=10.0,
                verify=VERIFY_SSL
            )
            if response.status_code in [200, 204, 404]:
                created_teams.remove(team_id)
                logger.info(f"✅ Deleted team: {team_id}")
            else:
                logger.warning(f"❌ Failed to delete team {team_id}: HTTP {response.status_code}")
                cleanup_successful = False
        except Exception as e:
            logger.error(f"❌ Error deleting team {team_id}: {str(e)}")
            cleanup_successful = False
    
    # Reset database if necessary
    if not cleanup_successful or created_teams or created_employees or created_attendance_records:
        try:
            logger.warning(f"⚠️ Some resources could not be deleted, resetting database...")
            
            response = cleanup_client.client.post(
                "/admin/reset-database", 
                json={"api_key": ADMIN_API_KEY, "synchronous": True},
                name="/admin/reset-database [cleanup]",
                timeout=30.0,
                verify=VERIFY_SSL
            )
            if response.status_code in [200, 202, 204]:
                logger.info("✅ Database reset")
            else:
                logger.error(f"❌ Error resetting database: HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error during database reset: {str(e)}")
    
    # Clean up the temporary client
    try:
        if cleanup_client and hasattr(cleanup_client, "on_stop"):
            cleanup_client.on_stop()
    except Exception as e:
        logger.error(f"Error during cleanup client shutdown: {str(e)}")
    
    logger.info("🏁 Cleanup complete")

class TeamOperations(TaskSet):
    """Team-related API operations"""
    
    def make_request(self, method, url, **kwargs):
        """Helper method to ensure consistent request settings"""
        if 'verify' not in kwargs:
            kwargs['verify'] = VERIFY_SSL
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30.0
            
        return getattr(self.client, method)(url, **kwargs)
    
    def random_string(self, length=10):
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    @task(3)
    def create_team(self):
        """Create a new team"""
        team_name = f"Team-{self.random_string(5)}"
        
        try:
            response = self.make_request(
                'post',
                "/teams",
                json={"name": team_name},
                name="Create Team"
            )
            
            # Track the team for cleanup
            if response.status_code == 200:
                team_data = response.json()
                team_id = team_data["id"]
                created_teams.append(team_id)
                logger.info(f"👥 Created team: {team_id}")
        except Exception as e:
            logger.error(f"❌ Create team error: {str(e)}")
    
    @task(2)
    def get_teams(self):
        """Get list of teams"""
        try:
            self.make_request(
                'get',
                "/teams",
                name="Get All Teams"
            )
        except Exception as e:
            logger.error(f"❌ Get teams error: {str(e)}")
    
    @task(2)
    def get_team_by_id(self):
        """Get a specific team by ID"""
        if not created_teams:
            return
            
        team_id = random.choice(created_teams)
        try:
            self.make_request(
                'get',
                f"/teams/{team_id}",
                name="Get Team by ID"
            )
        except Exception as e:
            logger.error(f"❌ Get team error: {str(e)}")
    
    @task(1)
    def update_team(self):
        """Update a team"""
        if not created_teams:
            return
            
        team_id = random.choice(created_teams)
        new_name = f"Updated-Team-{self.random_string(5)}"
        
        try:
            self.make_request(
                'put',
                f"/teams/{team_id}",
                json={"name": new_name},
                name="Update Team"
            )
        except Exception as e:
            logger.error(f"❌ Update team error: {str(e)}")
    
    @task(1)
    def get_team_employees(self):
        """Get employees for a team"""
        if not created_teams:
            return
            
        team_id = random.choice(created_teams)
        try:
            self.make_request(
                'get',
                f"/teams/{team_id}/employees",
                name="Get Team Employees"
            )
        except Exception as e:
            logger.error(f"❌ Get team employees error: {str(e)}")
    
    @task(1)
    def get_team_attendance(self):
        """Get attendance records for a team"""
        if not created_teams:
            return
            
        team_id = random.choice(created_teams)
        # Optional date filtering
        use_dates = random.choice([True, False])
        
        if use_dates:
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = date.today().strftime("%Y-%m-%d")
            try:
                self.make_request(
                    'get',
                    f"/teams/{team_id}/attendance?start_date={start_date}&end_date={end_date}",
                    name="Get Team Attendance (with dates)"
                )
            except Exception as e:
                logger.error(f"❌ Get team attendance error: {str(e)}")
        else:
            try:
                self.make_request(
                    'get',
                    f"/teams/{team_id}/attendance",
                    name="Get Team Attendance"
                )
            except Exception as e:
                logger.error(f"❌ Get team attendance error: {str(e)}")
    
    @task(1)
    def get_team_attendance_trends(self):
        """Get attendance trends for a team"""
        if not created_teams:
            return
            
        team_id = random.choice(created_teams)
        try:
            self.make_request(
                'get',
                f"/teams/{team_id}/attendance/trends",
                name="Get Team Attendance Trends"
            )
        except Exception as e:
            logger.error(f"❌ Get team attendance trends error: {str(e)}")

class EmployeeOperations(TaskSet):
    """Employee-related API operations"""
    
    def make_request(self, method, url, **kwargs):
        """Helper method to ensure consistent request settings"""
        if 'verify' not in kwargs:
            kwargs['verify'] = VERIFY_SSL
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30.0
            
        return getattr(self.client, method)(url, **kwargs)
    
    def random_string(self, length=10):
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    def random_email(self):
        """Generate a random email address"""
        name = self.random_string(8).lower()
        domain = self.random_string(6).lower()
        return f"{name}@{domain}.com"
    
    def random_phone(self):
        """Generate a random phone number"""
        return f"+1{random.randint(1000000000, 9999999999)}"
    
    def format_date(self, dt):
        """Format a date for API requests"""
        return dt.strftime("%Y-%m-%d")
    
    @task(3)
    def create_employee(self):
        """Create a new employee"""
        if not created_teams:
            # We need a team first
            return
            
        team_id = random.choice(created_teams)
        
        employee_data = {
            "first_name": f"First-{self.random_string(5)}",
            "last_name": f"Last-{self.random_string(5)}",
            "email": self.random_email(),
            "phone": self.random_phone(),
            "role": random.choice(list(Role)).value,
            "team_id": team_id,
            "hire_date": self.format_date(date.today() - timedelta(days=random.randint(1, 365)))
        }
        
        try:
            response = self.make_request(
                'post',
                "/employees",
                json=employee_data,
                name="Create Employee"
            )
            
            # Track the employee for cleanup
            if response.status_code == 200:
                employee_data = response.json()
                employee_id = employee_data["id"]
                created_employees.append(employee_id)
                logger.info(f"👤 Created employee: {employee_id}")
        except Exception as e:
            logger.error(f"❌ Create employee error: {str(e)}")
    
    @task(2)
    def get_employees(self):
        """Get list of employees"""
        try:
            self.make_request(
                'get',
                "/employees",
                name="Get All Employees"
            )
        except Exception as e:
            logger.error(f"❌ Get employees error: {str(e)}")
    
    @task(2)
    def get_employee_by_id(self):
        """Get a specific employee by ID"""
        if not created_employees:
            return
            
        employee_id = random.choice(created_employees)
        try:
            self.make_request(
                'get',
                f"/employees/{employee_id}",
                name="Get Employee by ID"
            )
        except Exception as e:
            logger.error(f"❌ Get employee error: {str(e)}")
    
    @task(1)
    def update_employee(self):
        """Update an employee"""
        if not created_employees:
            return
            
        employee_id = random.choice(created_employees)
        
        # Get current employee data first to maintain team_id
        try:
            employee_response = self.make_request(
                'get',
                f"/employees/{employee_id}",
                name="Get Employee for Update"
            )
            
            if employee_response.status_code == 200:
                current_data = employee_response.json()
                
                update_data = {
                    "first_name": f"Updated-{self.random_string(5)}",
                    "last_name": current_data["last_name"],
                    "email": current_data["email"],
                    "phone": current_data["phone"],
                    "role": current_data["role"],
                    "team_id": current_data["team_id"]
                }
                
                self.make_request(
                    'put',
                    f"/employees/{employee_id}",
                    json=update_data,
                    name="Update Employee"
                )
        except Exception as e:
            logger.error(f"❌ Update employee error: {str(e)}")
    
    @task(1)
    def get_employee_attendance(self):
        """Get attendance records for an employee"""
        if not created_employees:
            return
            
        employee_id = random.choice(created_employees)
        # Optional date filtering
        use_dates = random.choice([True, False])
        
        if use_dates:
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = date.today().strftime("%Y-%m-%d")
            try:
                self.make_request(
                    'get',
                    f"/employees/{employee_id}/attendance?start_date={start_date}&end_date={end_date}",
                    name="Get Employee Attendance (with dates)"
                )
            except Exception as e:
                logger.error(f"❌ Get employee attendance error: {str(e)}")
        else:
            try:
                self.make_request(
                    'get',
                    f"/employees/{employee_id}/attendance",
                    name="Get Employee Attendance"
                )
            except Exception as e:
                logger.error(f"❌ Get employee attendance error: {str(e)}")

class AttendanceOperations(TaskSet):
    """Attendance-related API operations"""
    
    def make_request(self, method, url, **kwargs):
        """Helper method to ensure consistent request settings"""
        if 'verify' not in kwargs:
            kwargs['verify'] = VERIFY_SSL
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30.0
            
        return getattr(self.client, method)(url, **kwargs)
    
    def random_string(self, length=10):
        """Generate a random string of specified length"""
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    def format_date(self, dt):
        """Format a date for API requests"""
        return dt.strftime("%Y-%m-%d")
    
    def format_datetime(self, dt):
        """Format a datetime for API requests"""
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    @task(4)
    def create_attendance(self):
        """Create an attendance record"""
        if not created_employees:
            # We need employees first
            return
            
        employee_id = random.choice(created_employees)
        
        # Create attendance data
        now = datetime.now()
        check_in = now - timedelta(hours=random.randint(1, 8))
        check_out = now if random.random() > 0.3 else None  # 30% chance for no check-out
        
        attendance_data = {
            "employee_id": employee_id,
            "status": random.choice(list(AttendanceType)).value,
            "date": self.format_date(date.today() - timedelta(days=random.randint(0, 7))),
            "check_in": self.format_datetime(check_in) if check_in else None,
            "check_out": self.format_datetime(check_out) if check_out else None,
            "notes": f"Test note {self.random_string(20)}" if random.random() > 0.7 else None
        }
        
        try:
            response = self.make_request(
                'post',
                "/attendance",
                json=attendance_data,
                name="Create Attendance"
            )
            
            # Track the attendance record for cleanup
            if response.status_code == 200:
                attendance_data = response.json()
                attendance_id = attendance_data["id"]
                created_attendance_records.append(attendance_id)
                logger.info(f"📅 Created attendance record: {attendance_id}")
        except Exception as e:
            logger.error(f"❌ Create attendance error: {str(e)}")
    
    @task(2)
    def get_all_attendance(self):
        """Get all attendance records"""
        # Optional date filtering
        use_dates = random.choice([True, False])
        
        if use_dates:
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = date.today().strftime("%Y-%m-%d")
            try:
                self.make_request(
                    'get',
                    f"/attendance?start_date={start_date}&end_date={end_date}",
                    name="Get All Attendance (with dates)"
                )
            except Exception as e:
                logger.error(f"❌ Get all attendance error: {str(e)}")
        else:
            try:
                self.make_request(
                    'get',
                    "/attendance",
                    name="Get All Attendance"
                )
            except Exception as e:
                logger.error(f"❌ Get all attendance error: {str(e)}")
    
    @task(2)
    def get_attendance_by_id(self):
        """Get a specific attendance record"""
        if not created_attendance_records:
            return
            
        attendance_id = random.choice(created_attendance_records)
        try:
            self.make_request(
                'get',
                f"/attendance/{attendance_id}",
                name="Get Attendance by ID"
            )
        except Exception as e:
            logger.error(f"❌ Get attendance error: {str(e)}")
    
    @task(2)
    def update_attendance(self):
        """Update an attendance record"""
        if not created_attendance_records:
            return
            
        attendance_id = random.choice(created_attendance_records)
        
        update_data = {
            "status": random.choice(list(AttendanceType)).value,
            "notes": f"Updated note {self.random_string(15)}"
        }
        
        try:
            self.make_request(
                'put',
                f"/attendance/{attendance_id}",
                json=update_data,
                name="Update Attendance"
            )
        except Exception as e:
            logger.error(f"❌ Update attendance error: {str(e)}")

class AIInsightsOperations(TaskSet):
    """AI Insights API operations"""
    
    def make_request(self, method, url, **kwargs):
        """Helper method to ensure consistent request settings"""
        if 'verify' not in kwargs:
            kwargs['verify'] = VERIFY_SSL
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 60.0  # Longer timeout for AI endpoints
            
        return getattr(self.client, method)(url, **kwargs)
    
    @task(1)
    def get_ai_insights(self):
        """Get AI-generated insights"""
        queries = [
            "Who was absent the most this month?",
            "How many employees worked from home last week?",
            "Give me a summary of attendance patterns",
            "Which team has the best attendance record?",
            "What's the average check-in time?",
            "Show attendance trends for the past month"
        ]
        
        query = random.choice(queries)
        try:
            self.make_request(
                'get',
                f"/ai/insights?query={query}",
                name="Get AI Insights"
            )
        except Exception as e:
            logger.error(f"❌ AI insights error: {str(e)}")
    
    @task(1)
    def get_sql_insights(self):
        """Get SQL-based AI insights"""
        sql_queries = [
            "Show me attendance trends for the engineering team last month",
            "Which employees have the highest WFH percentage?",
            "Compare attendance rates between teams",
            "What days of the week have the highest absence rate?"
        ]
        
        query = random.choice(sql_queries)
        try:
            self.make_request(
                'get',
                f"/ai/sql-insights?query={query}",
                name="Get SQL-based AI Insights"
            )
        except Exception as e:
            logger.error(f"❌ SQL insights error: {str(e)}")
    
    @task(1)
    def get_insights_history(self):
        """Get AI insights history"""
        try:
            self.make_request(
                'get',
                "/ai/insights/history",
                name="Get AI Insights History"
            )
        except Exception as e:
            logger.error(f"❌ Insights history error: {str(e)}")

class SystemOperations(TaskSet):
    """System API operations"""
    
    def make_request(self, method, url, **kwargs):
        """Helper method to ensure consistent request settings"""
        if 'verify' not in kwargs:
            kwargs['verify'] = VERIFY_SSL
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30.0
            
        return getattr(self.client, method)(url, **kwargs)
    
    @task(1)
    def health_check(self):
        """Test the API health check endpoint"""
        try:
            self.make_request(
                'get',
                "/",
                name="Health Check"
            )
        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")

class AttendanceSystemUser(HttpUser):
    """
    Main user class that simulates realistic user behavior
    with all API endpoints for the attendance system
    """
    # Set pacing to control request rate to achieve 10-50 RPS
    # Starting with a conservative wait time, the runner will adjust based on metrics
    wait_time = constant_pacing(0.5)  # Start with 2 RPS per user
    
    # TaskSets with weights
    tasks = {
        TeamOperations: 3,
        EmployeeOperations: 4,
        AttendanceOperations: 5,
        AIInsightsOperations: 2,
        SystemOperations: 1
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client.timeout = 30.0  # Set a reasonable timeout
        self.client.verify = VERIFY_SSL  # Apply SSL verification setting
        self.start_time = None
    
    def on_start(self):
        """Initialize user session"""
        self.start_time = time.time()
        self.client.headers.update({
            "Accept": "application/json",
            "User-Agent": "AttendanceSystemLoadTest/1.0",
            "Connection": "close"  # Prevent connection pooling issues
        })
        logger.info(f"👤 User started at {self.start_time} (SSL verification: {VERIFY_SSL})")
    
    def on_stop(self):
        """Clean up user session"""
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info(f"👤 User stopped after {duration:.2f}s")

# If running locally for development
if __name__ == "__main__":
    print("Attendance System Load Test")
    print("==========================")
    print(f"Target: {TARGET_RPS_MIN}-{TARGET_RPS_MAX} RPS for {TEST_DURATION_SECONDS} seconds")
    print(f"SSL verification: {'Enabled' if VERIFY_SSL else 'Disabled'}")
    print("\nTo run the load test against a local endpoint:")
    print("locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 1m --headless")
    print("\nTo run against a deployed HTTPS endpoint with SSL verification disabled:")
    print("locust -f locustfile.py --host=https://your-deployed-endpoint.com --users 10 --spawn-rate 2 --run-time 1m --headless")