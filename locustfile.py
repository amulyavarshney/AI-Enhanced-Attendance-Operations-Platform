from locust import HttpUser, task, between
import random
from datetime import datetime, timedelta

class AttendanceUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Simulate user login or setup
        self.employee_id = random.randint(1, 100)  # Assuming we have 100 employees
        self.team_id = random.randint(1, 10)  # Assuming we have 10 teams
    
    @task(3)
    def get_employee_attendance(self):
        self.client.get(f"/attendance/{self.employee_id}")
    
    @task(1)
    def create_attendance(self):
        data = {
            "employee_id": self.employee_id,
            "status": random.choice(["present", "absent", "wfh", "half_day"]),
            "check_in": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
            "check_out": datetime.utcnow().isoformat(),
            "notes": "Test attendance record"
        }
        self.client.post("/attendance", json=data)
    
    @task(2)
    def get_team_trends(self):
        self.client.get(f"/attendance/team/{self.team_id}/trends")
    
    @task(1)
    def get_ai_insights(self):
        queries = [
            "Who was absent the most this month?",
            "How many WFH days last week?",
            "Give me a summary of attendance patterns"
        ]
        self.client.get(f"/ai/insights?query={random.choice(queries)}") 