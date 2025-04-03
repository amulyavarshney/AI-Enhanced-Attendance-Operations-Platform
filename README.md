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

4. Run the application locally:
```bash
uvicorn app.main:app --reload
```

## Testing

Run the test suite:
```bash
pytest app/tests/
```

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