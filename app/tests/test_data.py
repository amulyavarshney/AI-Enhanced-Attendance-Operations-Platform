from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models import Team, Employee, Role, AttendanceType, Attendance

def create_test_data(db: Session):
    # Create teams
    teams = [
        Team(name="Engineering"),
        Team(name="HR"),
        Team(name="Finance")
    ]
    for team in teams:
        db.add(team)
    db.commit()

    # Create employees
    employees = [
        Employee(
            name="John Doe",
            email="john@example.com",
            team_id=1,
            role=Role.EMPLOYEE,
            hire_date=datetime.utcnow() - timedelta(days=365)
        ),
        Employee(
            name="Jane Smith",
            email="jane@example.com",
            team_id=1,
            role=Role.MANAGER,
            hire_date=datetime.utcnow() - timedelta(days=730)
        ),
        Employee(
            name="Bob Wilson",
            email="bob@example.com",
            team_id=2,
            role=Role.HR,
            hire_date=datetime.utcnow() - timedelta(days=180)
        )
    ]
    for employee in employees:
        db.add(employee)
    db.commit()

    # Create attendance records
    today = datetime.utcnow()
    attendance_records = [
        Attendance(
            employee_id=1,
            date=today,
            status=AttendanceType.PRESENT,
            check_in=today - timedelta(hours=9),
            check_out=today - timedelta(hours=1)
        ),
        Attendance(
            employee_id=2,
            date=today,
            status=AttendanceType.WFH,
            check_in=today - timedelta(hours=9),
            check_out=today - timedelta(hours=1)
        ),
        Attendance(
            employee_id=3,
            date=today,
            status=AttendanceType.ABSENT,
            notes="On leave"
        ),
        # Add some historical records
        Attendance(
            employee_id=1,
            date=today - timedelta(days=1),
            status=AttendanceType.PRESENT,
            check_in=today - timedelta(days=1, hours=9),
            check_out=today - timedelta(days=1, hours=1)
        ),
        Attendance(
            employee_id=2,
            date=today - timedelta(days=1),
            status=AttendanceType.HALF_DAY,
            check_in=today - timedelta(days=1, hours=9),
            check_out=today - timedelta(days=1, hours=5)
        )
    ]
    for record in attendance_records:
        db.add(record)
    db.commit() 