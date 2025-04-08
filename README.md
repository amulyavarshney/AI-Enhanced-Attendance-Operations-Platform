# AI-Enhanced Attendance Operations Platform

A modern attendance management system with AI-powered insights and analytics, built with FastAPI and React.

## Overview

This platform provides a complete solution for managing employee attendance with intelligent insights. It combines a robust backend API with a modern frontend interface to offer an intuitive attendance tracking experience enhanced by AI-powered analytics.

For detailed technical information, please refer to the [comprehensive documentation](DOCUMENTATION.md).

## Key Features

- 📱 **Complete Attendance Management**: Track employee check-ins, check-outs, and attendance statuses
- 👥 **Team Management**: Organize employees into teams with dedicated views
- 📊 **Comprehensive Analytics**: View attendance trends, patterns, and statistics
- 🧠 **AI-Powered Insights**: Generate natural language insights about attendance data
- 💬 **Natural Language Queries**: Ask questions about attendance in plain English
- 🔄 **SQL Translation**: Natural language to SQL translation for custom queries
- 📱 **Responsive UI**: Modern React frontend with responsive design
- 📊 **Robust API**: FastAPI backend with proper documentation
- 🐳 **Containerized Deployment**: Docker and Docker Compose setup

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  React Frontend │◄────►│   FastAPI API   │◄────►│   PostgreSQL    │
│                 │      │                 │      │                 │
└─────────────────┘      └────────┬────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐      
                         │                 │      
                         │   Azure OpenAI  │      
                         │                 │      
                         └─────────────────┘      
```

### Key Components

1. **React Frontend**: TypeScript-based UI with components for teams, employees, attendance, and AI insights
2. **FastAPI Backend**: Python API with endpoints for all CRUD operations and AI features
3. **PostgreSQL Database**: Relational database with tables for teams, employees, attendance, and AI insights
4. **Azure OpenAI Integration**: AI services for natural language processing and insights generation

## Tech Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL
- **Migrations**: Alembic
- **AI**: Azure OpenAI (GPT-4)
- **Testing**: pytest, FastAPI TestClient
- **Load Testing**: Locust
- **API Documentation**: OpenAPI (Swagger UI)

### Frontend
- **Language**: TypeScript
- **Framework**: React
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **State Management**: React Context API
- **HTTP Client**: Axios

### DevOps
- **Containerization**: Docker, Docker Compose
- **Version Control**: Git
- **Development**: Hot reloading for both frontend and backend

## Database Schema

### Entity Relationship Diagram

```
┌──────────┐       ┌───────────┐       ┌─────────────┐
│          │       │           │       │             │
│   Team   │◄──────┤  Employee │◄──────┤  Attendance │
│          │1     *│           │1     *│             │
└────┬─────┘       └───────────┘       └─────────────┘
     │
     │1
     │
     │*
┌────▼─────┐       ┌────────────┐
│          │       │            │
│TeamTrends│       │ AIInsight  │
│          │       │            │
└──────────┘       └────────────┘
```

### Teams
- `id`: Primary key
- `name`: Team name
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

### Employees
- `id`: Primary key
- `first_name`: Employee first name
- `last_name`: Employee last name
- `email`: Unique email address
- `phone`: Contact number (optional)
- `role`: Enum (employee, manager, admin)
- `team_id`: Foreign key to Teams
- `hire_date`: Employee hire date
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

### Attendance
- `id`: Primary key
- `employee_id`: Foreign key to Employees
- `date`: Date of attendance
- `status`: Enum (present, absent, half_day, wfh, leave)
- `check_in`: Check-in time (nullable)
- `check_out`: Check-out time (nullable)
- `notes`: Additional notes (nullable)
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

### TeamTrends
- `id`: Primary key
- `team_id`: Foreign key to Teams
- `date`: Date of trend data
- `total_employees`: Total employee count
- `present_count`: Present employees count
- `absent_count`: Absent employees count
- `wfh_count`: Work from home employees count
- `half_day_count`: Half day employees count
- `leave_count`: Employees on leave count

### AIInsight
- `id`: Primary key
- `query`: Original user query
- `summary`: AI-generated summary
- `details`: Detailed insights (JSON)
- `generated_at`: Generation timestamp

## API Endpoints

### Health Check
- `GET /`: Basic health check and welcome message

### Teams
- `POST /teams`: Create a new team
- `GET /teams`: Get all teams
- `GET /teams/{team_id}`: Get a specific team
- `PUT /teams/{team_id}`: Update a team
- `DELETE /teams/{team_id}`: Delete a team
- `GET /teams/{team_id}/employees`: Get employees in a team
- `GET /teams/{team_id}/attendance`: Get attendance for a team
- `GET /teams/{team_id}/attendance/trends`: Get attendance trends for a team

### Employees
- `POST /employees`: Create a new employee
- `GET /employees`: Get all employees
- `GET /employees/{employee_id}`: Get a specific employee
- `PUT /employees/{employee_id}`: Update an employee
- `DELETE /employees/{employee_id}`: Delete an employee
- `GET /employees/{employee_id}/attendance`: Get attendance for an employee

### Attendance
- `POST /attendance`: Create a new attendance record
- `GET /attendance`: Get all attendance records
- `GET /attendance/{attendance_id}`: Get a specific attendance record
- `PUT /attendance/{attendance_id}`: Update an attendance record

### AI Insights
- `GET /ai/insights`: Get AI-generated insights
- `GET /ai/sql-insights`: Get SQL-based AI insights
- `GET /ai/insights/history`: Get past AI insights

### Admin
- `POST /admin/reset-database`: Reset the database (development/testing only)

## AI Capabilities

### SQL Translation
The platform can convert natural language queries to SQL using Azure OpenAI, allowing users to ask questions about attendance data in plain English.

### Pattern Recognition
The AI service identifies patterns in attendance data, such as:
- Employees with high absence rates
- Teams with above-average work from home days
- Unusual attendance patterns 
- Trends in attendance across teams and time periods

### Fallback Mechanisms
If SQL translation fails, the system falls back to pattern-based analysis using predefined templates.

## Frontend Pages

- **Dashboard**: Overview of key metrics and recent activities
- **Teams**: Team management and team-level analytics
- **Employees**: Employee management and individual stats
- **Attendance**: Daily attendance tracking and management
- **Analytics**: Detailed attendance analytics and trends
- **AI Insights**: Natural language query interface for attendance data

## Prerequisites

- Python 3.11+
- Node.js and npm/bun
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL (if running locally without Docker)
- Azure OpenAI API key (or OpenAI API key)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-attendance-platform.git
cd ai-attendance-platform
```

2. Create a `.env` file in the root directory (copy from .env.example):
```bash
cp .env.example .env
# Edit .env with your actual values
```

3. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at:
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- API Documentation: `http://localhost:8000/docs`

## Docker Configuration

The application is fully dockerized with the following services:

### API Service
- Multi-stage build for smaller image size
- Non-root user for improved security
- Health checks for reliability
- Environment variables from .env file
- Volume mounts for development (hot reloading)

### Frontend Service
- Multi-stage build with optimized production image
- Nginx for serving static files with proper caching
- SPA routing configuration
- Security headers
- Health checks

### Database Service
- PostgreSQL with persistent volume
- Health checks
- Secured with username and password

### Usage

#### Production Deployment
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

#### Development with Hot Reloading
The Docker setup includes volume mounts for development that enable hot reloading of code changes:
- Backend Python code changes are automatically detected
- Frontend changes require rebuilding (not real-time hot reloading)

## Development Setup

### Backend

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
uvicorn app.main:app --reload
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
# or
bun install
```

3. Run the development server:
```bash
npm run dev
# or
bun run dev
```

## Testing

### Backend Tests

```bash
# Run all tests
pytest app/tests/

# Run with coverage
pytest --cov=app app/tests/
```

### Load Testing

```bash
# Run Locust load tests
locust -f attendance_locustfile.py --host=http://localhost:8000
```

## Database Management

### Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Initialize Database Schema

```bash
# Load the schema from SQL file
psql -U postgres -d attendance_db -f scripts/schema.sql
```

### Database Queries

```bash
# Connect to the database
psql -U postgres -d attendance_db

# List the tables
\dt

# Query sample data
SELECT * FROM teams;
SELECT * FROM employees;
SELECT * FROM attendance LIMIT 10;
```

### Reset Database (Development Only)

```bash
# Reset with API call
curl -X POST "http://localhost:8000/admin/reset-database?api_key=dev_reset_key&include_mock_data=true"
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 