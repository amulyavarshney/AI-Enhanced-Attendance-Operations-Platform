# AI-Enhanced Attendance Operations Platform

A modern attendance management system with AI-powered insights and analytics, built with FastAPI and PostgreSQL.

## Features

- 🔐 REST APIs for attendance management
- 📊 PostgreSQL database with SQLAlchemy ORM
- 🤖 AI-powered insights using OpenAI
- 👥 Team-based attendance tracking
- 📈 Attendance trends and analytics
- 🐳 Docker containerization
- 📝 Comprehensive API documentation
- 🔄 Database migrations with Alembic
- 🧪 Test suite with pytest

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **AI**: OpenAI GPT-4
- **Container**: Docker & Docker Compose
- **Testing**: pytest, FastAPI TestClient
- **Load Testing**: Locust
- **Documentation**: OpenAPI (Swagger UI)

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL
- OpenAI API key

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-attendance-platform.git
cd ai-attendance-platform
```

2. Create a `.env` file in the root directory:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/attendance_db
OPENAI_API_KEY=your_openai_api_key_here
```

3. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

- `GET /attendance/{employee_id}` - Get attendance records for an employee
- `POST /attendance` - Create a new attendance record
- `PUT /attendance/{attendance_id}` - Update an attendance record
- `GET /attendance/team/{team_id}/trends` - Get attendance trends for a team
- `GET /ai/insights` - Get AI-generated insights about attendance
- `POST /admin/reset-database` - Reset the database (admin/dev only)

## Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Run the application:
```bash
# Basic run
uvicorn app.main:app --reload

# Run with the helper script (supports database reset)
python run_app.py

# Run with database reset and mock data
python run_app.py --reset-db --with-mock-data
```

## Testing

### Run Tests

Using the test runner script (recommended):
```bash
# Create test databases and run all tests
python prepare_test_env.py --create-dbs --run-tests

# Just create test databases
python prepare_test_env.py --create-dbs

# Run tests with the simplified test runner
python run_tests.py
```

Run tests manually:
```bash
pytest app/tests/
```

### Load Testing

Run load tests using Locust:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

## Database Schema

### Teams
- `id`: Primary key
- `name`: Team name

### Employees
- `id`: Primary key
- `name`: Employee name
- `email`: Unique email address
- `team_id`: Foreign key to Teams
- `role`: Enum (EMPLOYEE, MANAGER, HR, ADMIN)
- `hire_date`: Date when employee was hired

### Attendance
- `id`: Primary key
- `employee_id`: Foreign key to Employees
- `date`: Date of attendance
- `status`: Enum (PRESENT, ABSENT, HALF_DAY, WFH, LEAVE, HOLIDAY)
- `check_in`: Check-in time (nullable)
- `check_out`: Check-out time (nullable)
- `notes`: Additional notes (nullable)

## Database Management

### Setup and Migrations

Run database migrations:
```bash
alembic upgrade head
```

### Reset Database (Development/Testing)

The platform provides an endpoint to reset the database in development or testing environments:

```bash
# Reset with no test data (asynchronous)
curl -X POST "http://localhost:8000/admin/reset-database?api_key=dev_reset_key"

# Reset with mock test data (asynchronous)
curl -X POST "http://localhost:8000/admin/reset-database?api_key=dev_reset_key&include_mock_data=true"

# Synchronous reset (wait for completion)
curl -X POST "http://localhost:8000/admin/reset-database?api_key=dev_reset_key&synchronous=true"

# Synchronous reset with mock data
curl -X POST "http://localhost:8000/admin/reset-database?api_key=dev_reset_key&synchronous=true&include_mock_data=true"
```

You can also reset the database when starting the application:

```bash
# Start app with database reset
python run_app.py --reset-db

# Start app with database reset and mock data
python run_app.py --reset-db --with-mock-data

# Start app with synchronous database reset
python run_app.py --reset-db --sync-reset
```

⚠️ **Warning**: This endpoint drops all tables and data. Use only in development/testing environments.

The API key can be configured through the `ADMIN_API_KEY` environment variable. The default key is `dev_reset_key` and should be changed in production.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FastAPI team for the amazing framework
- OpenAI for the GPT-4 API
- SQLAlchemy team for the ORM
- Docker team for containerization 