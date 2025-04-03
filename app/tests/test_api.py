from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.tests.test_data import create_test_data
import pytest

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/attendance_test_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    create_test_data(db)
    yield
    Base.metadata.drop_all(bind=engine)

def test_get_employee_attendance():
    response = client.get("/attendance/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["employee"]["name"] == "John Doe"

def test_create_attendance():
    attendance_data = {
        "employee_id": 1,
        "status": "present",
        "check_in": "2024-02-20T09:00:00",
        "check_out": "2024-02-20T17:00:00",
        "notes": "Test attendance"
    }
    response = client.post("/attendance", json=attendance_data)
    assert response.status_code == 200
    data = response.json()
    assert data["employee"]["name"] == "John Doe"
    assert data["status"] == "present"

def test_get_team_trends():
    response = client.get("/attendance/team/1/trends")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["team_id"] == 1
    assert "present_count" in data[0]

def test_get_ai_insights():
    queries = [
        "Who was absent the most this month?",
        "How many WFH days last week?",
        "Give me a summary of attendance patterns"
    ]
    
    for query in queries:
        response = client.get(f"/ai/insights?query={query}")
        # The response will be shown in the test output when running pytest
        # You can see it in:
        # 1. Terminal/console where you run the tests
        # 2. pytest output with -v flag for verbose mode
        # 3. pytest output with -s flag to see print statements
        print(response.json())
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "details" in data
        assert data["query"] == query 