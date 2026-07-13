# AI-Enhanced Attendance Operations Platform Documentation

## 1. Executive Summary

The AI-Enhanced Attendance Operations Platform is a full-stack attendance system with JWT auth, RBAC, live dashboard/analytics, AI insights (Azure OpenAI), audit logging, and Docker-based deployment.

This document describes the current production-oriented architecture and operating model. Prefer [README.md](README.md) for quick start and endpoint lists.

### Production readiness highlights

- JWT authentication + role-based access (`employee` / `manager` / `admin`)
- AI SQL allowlisting, rate limits, and circuit breaker
- Request logging (`X-Request-ID`) and mutating-API audit trail
- Health probes: `/health/live`, `/health/ready`
- Alembic migrations (`0001_initial`, `0002_audit_logs`)
- CSV export, notifications feed, admin audit UI
- GitHub Actions CI (pytest + frontend build)

## 2. System Architecture

### 2.1 High-Level Architecture

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

### 2.2 Component Overview

1. **Frontend Client (React/TypeScript)**
   - Vite + React Router + TanStack Query
   - Auth context with bearer token storage
   - Pages: Login, Dashboard, Employees, Attendance, Teams, Analytics, AI Insights, Audit Logs
   - shadcn/ui + Tailwind CSS

2. **Backend API (FastAPI)**
   - CRUD + dashboard/analytics endpoints
   - JWT auth (`/auth/login`, `/auth/me`) and RBAC dependencies
   - AI insights with SQL safety + circuit breaker
   - Audit middleware for successful mutating requests
   - Notifications derived from audit events
   - OpenAPI docs at `/docs`

3. **Database (PostgreSQL)**
   - Tables: teams, employees, attendance, team_trends, ai_insights, audit_logs
   - Seed SQL in `scripts/schema.sql` (Docker first boot)
   - Alembic for schema evolution

4. **AI Service (Azure OpenAI)**
   - NL → SQL → summarize path with pattern fallback
   - SELECT-only validation, row limits, statement timeout
   - Circuit breaker on provider failures

5. **Containerization (Docker)**
   - Compose services: `api`, `frontend`, `db`
   - Frontend CSP injected from `VITE_API_URL` at build time

## 3. Authentication & Authorization

1. Obtain token: `POST /auth/login`
2. Send `Authorization: Bearer <token>`
3. Roles:
   - **admin**: deletes, audit logs page/API
   - **manager**: team/employee mutations + AI
   - **employee**: read + attendance create/update

Seeded password for demo users: `Admin123!`  
Admin: `admin@example.com`

## 4. Security Controls

- CORS restricted via `CORS_ORIGINS` (stricter in production)
- Admin DB reset disabled when `APP_ENV=production`
- AI endpoints rate-limited (`AI_RATE_LIMIT_*`)
- Duplicate employee email returns HTTP 409
- Nginx CSP includes build-time API origin

## 5. Operations

### Health

- `GET /health/live` — process liveness
- `GET /health/ready` — DB connectivity + AI circuit status

### Migrations

```bash
alembic upgrade head
```

### Tests / CI

```bash
pytest app/tests -q
```

GitHub Actions workflow: `.github/workflows/ci.yml`

### Useful endpoints

- `GET /dashboard/stats`, `GET /dashboard/trends`
- `GET /attendance/export`
- `GET /notifications`
- `GET /audit-logs` (admin)

---

The remainder of this file retains historical deep-dive notes. Where it conflicts with the sections above or README.md, treat the newer sections as source of truth.

## 3. Database Schema

### 3.1 Entity Relationship Diagram

```
┌─────────────────────────────┐
│             Team            │
├─────────────────────────────┤
│ id: Integer (PK)            │
│ name: String                │
│ created_at: DateTime        │
│ updated_at: DateTime        │
└───────────┬─────────────────┘
            │
            │ 1:N
            ▼
┌─────────────────────────────┐        ┌─────────────────────────────┐
│           Employee          │        │          Attendance         │
├─────────────────────────────┤        ├─────────────────────────────┤
│ id: Integer (PK)            │        │ id: Integer (PK)            │
│ first_name: String          │        │ employee_id: Integer (FK)   │
│ last_name: String           │        │ date: Date                  │
│ email: String (Unique)      │1      N│ status: Enum                │
│ phone: String (Nullable)    │◄───────┤ check_in: DateTime          │
│ role: Enum                  │        │ check_out: DateTime         │
│ team_id: Integer (FK)       │        │ notes: Text                 │
│ hire_date: Date             │        │ created_at: DateTime        │
│ created_at: DateTime        │        │ updated_at: DateTime        │
│ updated_at: DateTime        │        │                             │
└─────────────────────────────┘        └─────────────────────────────┘
            ▲
            │ N:1
            │
┌───────────┴─────────────────┐        ┌─────────────────────────────┐
│         TeamTrends          │        │          AIInsight          │
├─────────────────────────────┤        ├─────────────────────────────┤
│ id: Integer (PK)            │        │ id: Integer (PK)            │
│ team_id: Integer (FK)       │        │ query: Text                 │
│ date: Date                  │        │ summary: Text               │
│ total_employees: Integer    │        │ details: JSONB              │
│ present_count: Integer      │        │                             │
│ absent_count: Integer       │        │                             │
│ wfh_count: Integer          │        │                             │
│ half_day_count: Integer     │        │                             │
│ leave_count: Integer        │        │                             │
└─────────────────────────────┘        └─────────────────────────────┘
```

### 3.2 Table Definitions

#### 3.2.1 Teams Table
- **id**: Primary key
- **name**: Team name
- **created_at**: Creation timestamp
- **updated_at**: Update timestamp

#### 3.2.2 Employees Table
- **id**: Primary key
- **first_name**: Employee's first name
- **last_name**: Employee's last name
- **email**: Unique email address
- **phone**: Contact number (optional)
- **role**: Enum (employee, manager, admin)
- **team_id**: Foreign key to Teams
- **hire_date**: Employee hire date
- **created_at**: Creation timestamp
- **updated_at**: Update timestamp

#### 3.2.3 Attendance Table
- **id**: Primary key
- **employee_id**: Foreign key to Employees
- **date**: Date of attendance
- **status**: Enum (present, absent, half_day, wfh, leave)
- **check_in**: Check-in time (nullable)
- **check_out**: Check-out time (nullable)
- **notes**: Additional notes (nullable)
- **created_at**: Creation timestamp
- **updated_at**: Update timestamp

#### 3.2.4 Team Trends Table
- **id**: Primary key
- **team_id**: Foreign key to Teams
- **date**: Date of trend data
- **total_employees**: Total employee count
- **present_count**: Present employees count
- **absent_count**: Absent employees count
- **wfh_count**: Work from home employees count
- **half_day_count**: Half day employees count
- **leave_count**: Employees on leave count

#### 3.2.5 AI Insights Table
- **id**: Primary key
- **query**: Original user query
- **summary**: AI-generated summary
- **details**: Detailed insights (JSON)
- **generated_at**: Generation timestamp

### 3.3 Database Setup and Management

#### 3.3.1 Initial Setup
```bash
# Load the schema from SQL file
psql -U postgres -d attendance_db -f scripts/schema.sql

# Connect to the database
psql -U postgres -d attendance_db

# List the tables
\dt

# Query sample data
SELECT * FROM teams;
SELECT * FROM employees;
SELECT * FROM attendance LIMIT 10;
```

#### 3.3.2 Migrations with Alembic
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

#### 3.3.3 Database Reset (Development Only)
```bash
# Via API
curl -X POST "http://localhost:8000/admin/reset-database?api_key=dev_reset_key&include_mock_data=true"

# Via application start
python run_app.py --reset-db --with-mock-data
```

## 4. API Reference

### 4.1 Swagger UI

The API documentation is available through Swagger UI at `http://localhost:8000/docs` when the application is running. Swagger UI provides an interactive interface to:

- View all available endpoints
- Read endpoint descriptions and parameters
- Test endpoints directly from the browser
- View request and response schemas

### 4.2 API Endpoints

#### 4.2.1 Health Check
- `GET /`: Basic health check and welcome message

#### 4.2.2 Teams
- `POST /teams`: Create a new team
- `GET /teams`: Get all teams
- `GET /teams/{team_id}`: Get a specific team
- `PUT /teams/{team_id}`: Update a team
- `DELETE /teams/{team_id}`: Delete a team
- `GET /teams/{team_id}/employees`: Get employees in a team
- `GET /teams/{team_id}/attendance`: Get attendance for a team
- `GET /teams/{team_id}/attendance/trends`: Get attendance trends for a team

#### 4.2.3 Employees
- `POST /employees`: Create a new employee
- `GET /employees`: Get all employees
- `GET /employees/{employee_id}`: Get a specific employee
- `PUT /employees/{employee_id}`: Update an employee
- `DELETE /employees/{employee_id}`: Delete an employee
- `GET /employees/{employee_id}/attendance`: Get attendance for an employee

#### 4.2.4 Attendance
- `POST /attendance`: Create a new attendance record
- `GET /attendance`: Get all attendance records
- `GET /attendance/{attendance_id}`: Get a specific attendance record
- `PUT /attendance/{attendance_id}`: Update an attendance record

#### 4.2.5 AI Insights
- `GET /ai/insights`: Get AI-generated insights
- `GET /ai/sql-insights`: Get SQL-based AI insights
- `GET /ai/insights/history`: Get past AI insights

#### 4.2.6 Admin
- `POST /admin/reset-database`: Reset the database (development/testing only)

### 4.3 Authentication

The API currently uses API key authentication for admin endpoints. In production, this should be replaced with a more secure authentication method like JWT tokens.

### 4.4 Error Handling

All API endpoints include comprehensive error handling with appropriate HTTP status codes:
- 400: Bad Request (invalid input)
- 404: Not Found (resource doesn't exist)
- 422: Unprocessable Entity (validation error)
- 500: Internal Server Error (server-side error)

Error responses include detailed messages to help debugging:

```json
{
  "detail": "Error message describing the issue"
}
```

## 5. AI Integration

### 5.1 AI Service Architecture

The AI service is implemented as a separate module within the backend that leverages Azure OpenAI to provide insights and analytics.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───►│    API      │───►│  AIService  │───►│ AzureOpenAI │
└─────────────┘    └─────────────┘    └────┬────────┘    └─────────────┘
                                          │
                                          ▼
                                     ┌─────────────┐
                                     │  Database   │
                                     └─────────────┘
```

### 5.2 Natural Language Processing Features

1. **SQL Translation**
   - Converts natural language queries into SQL
   - Handles complex queries about attendance data
   - Example: "Who has the most absences this month?" → SQL query

2. **Pattern Recognition**
   - Identifies patterns in attendance data
   - Detects anomalies and trends
   - Generates human-readable insights

3. **Fallback Mechanisms**
   - Pattern-based approach if SQL translation fails
   - Predefined templates for common query types
   - Graceful degradation for error handling

### 5.3 AI Implementation Details

The AI service uses a tiered approach:
1. First tries to convert natural language to SQL and analyze results
2. Falls back to pattern-based analysis if SQL approach fails
3. Saves insights to the database for future reference

#### 5.3.1 Example Prompts

SQL Generation Prompt:
```
You are a SQL query generator for an attendance management system. Convert the following natural language query to a PostgreSQL SQL query.

Database schema:
- teams: id, name, created_at, updated_at
- employees: id, first_name, last_name, email, phone, role (enum), team_id, hire_date, created_at, updated_at
- attendance: id, employee_id, date, status (enum), check_in, check_out, notes, created_at, updated_at
- team_trends: id, team_id, date, total_employees, present_count, absent_count, wfh_count, half_day_count, leave_count
- ai_insights: id, query, summary, details, generated_at

User query: {query}
```

Analysis Prompt:
```
Based on the following data, provide insights and analysis.

User query: {query}
SQL query used: {sql}
Query results: {data}

Analyze the data and provide valuable insights related to:
1. Key patterns, trends, or anomalies in the data
2. Notable employee or team behaviors
3. Attendance patterns (if relevant)
4. Any actionable recommendations
```

## 6. Frontend Application

### 6.1 Frontend Architecture

The frontend is built with React and TypeScript, utilizing modern web development practices:

```
App
├── Router
│   └── Layout
│       ├── Sidebar
│       ├── Header
│       └── Pages
│           ├── Dashboard
│           ├── Teams
│           ├── Employees
│           ├── Attendance
│           ├── Analytics
│           └── AI Insights
└── Services
    ├── API Client
    ├── Authentication
    └── Data Fetching
```

### 6.2 Page Descriptions

#### 6.2.1 Dashboard
- **Purpose**: Overview of key metrics and recent activities
- **Components**: 
  - Summary cards for present/absent counts
  - Recent activity feed
  - Quick access to common actions
  - Team attendance summary

#### 6.2.2 Teams
- **Purpose**: Team management and team-level analytics
- **Components**:
  - Team creation and editing
  - Team list view
  - Team detail view
  - Team attendance trends

#### 6.2.3 Employees
- **Purpose**: Employee management and individual analytics
- **Components**:
  - Employee directory with search/filter
  - Employee creation and editing
  - Employee detail view
  - Individual attendance history

#### 6.2.4 Attendance
- **Purpose**: Daily attendance tracking and management
- **Components**:
  - Daily attendance grid
  - Attendance status selector
  - Check-in/check-out recording
  - Bulk actions for attendance

#### 6.2.5 Analytics
- **Purpose**: Detailed attendance analytics and trends
- **Components**:
  - Attendance trend charts
  - Team comparison visualizations
  - Absence rate analysis
  - Custom date range selector

#### 6.2.6 AI Insights
- **Purpose**: Natural language query interface for insights
- **Components**:
  - Query input field
  - Results display
  - Insight history
  - Suggested queries

### 6.3 State Management

The application uses React Context API for state management:
- Authentication context for user state
- Teams context for team data
- Employees context for employee data
- Attendance context for attendance records
- Theme context for UI theming

### 6.4 API Integration

Services defined in the `services` directory handle all API communication:
- `apiClient.ts`: Core API client with Axios
- Type-safe request and response handling
- Centralized error handling and retry logic

## 7. Load Testing

### 7.1 Load Testing Architecture

Load testing is performed using Locust, an open-source load testing tool:

```
┌─────────────┐
│   Locust    │
│   Master    │
└───┬─────┬───┘
    │     │
┌───▼───┐ │ ┌───▼───┐
│ Worker │ │ │ Worker │
└───┬───┘ │ └───┬───┘
    │     │     │
    │     │     │
┌───▼─────▼─────▼───┐
│                   │
│    API Server     │
│                   │
└───────────────────┘
```

### 7.2 Locust Setup

The Locust test configuration is defined in `attendance_locustfile.py`, which specifies:
- User behavior simulations
- Task distributions
- Request patterns
- Wait times between requests

### 7.3 Load Test Scenarios

1. **Team Operations**
   - Create, retrieve, update, and delete teams
   - Retrieve team attendance and trends

2. **Employee Operations**
   - Create, retrieve, update, and delete employees
   - Retrieve employee attendance records

3. **Attendance Operations**
   - Create and update attendance records
   - Retrieve daily and trend reports

4. **AI Insights**
   - Generate natural language insights
   - Execute custom queries
   - Retrieve insight history

### 7.4 Running Load Tests

To run load tests:

```bash
locust -f attendance_locustfile.py --host=http://localhost:8000
```

This starts the Locust web interface at http://localhost:8089, where you can:
- Configure the number of users
- Set the spawn rate
- Start and stop tests
- View real-time metrics and charts

### 7.5 Performance Metrics

Load tests capture key performance metrics:
- Response times (min, max, average, median, 95th percentile)
- Requests per second
- Failure rates
- Number of users

## 8. Containerization

### 8.1 Docker Architecture

The application is containerized using Docker with a multi-container setup:

```
┌─────────────────┐
│ Docker Compose  │
└──┬───────┬──────┘
   │       │
┌──▼───┐ ┌─▼────┐ ┌─────┐
│ API  │ │ Web  │ │ DB  │
└──────┘ └──────┘ └─────┘
```

### 8.2 Container Details

#### 8.2.1 API Container
- Base image: Python 3.11 slim
- Multi-stage build for optimized size
- Non-root user for security
- Health checks
- Volume mounts for development

#### 8.2.2 Frontend Container
- Build stage: Node.js 20
- Production stage: Nginx Alpine
- SPA routing configuration
- Security headers
- Gzip compression
- Static asset caching

#### 8.2.3 Database Container
- PostgreSQL 15 Alpine
- Persistent volume for data
- Health checks
- Configuration via environment variables

### 8.3 Docker Compose Configuration

The `docker-compose.yml` file defines the services, networks, and volumes:
- Service dependencies
- Port mappings
- Environment variables
- Health checks
- Volume mounts
- Restart policies

## 9. Deployment

### 9.1 Development Deployment

1. Clone the repository
2. Configure environment variables
3. Start containers with Docker Compose
4. Access the application at the defined ports

```bash
# Clone repository
git clone https://github.com/username/ai-attendance-platform.git
cd ai-attendance-platform

# Configure environment
cp .env.example .env

# Start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

### 9.2 Production Deployment

For production deployment, additional considerations include:
- Securing environment variables
- Setting up SSL/TLS
- Configuring a production-ready database
- Implementing proper authentication
- Setting up monitoring and logging
- Configuring a reverse proxy

## 10. Development Environment

### 10.1 Backend Development

1. Create a virtual environment
2. Install dependencies
3. Run database migrations
4. Start the FastAPI server

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### 10.2 Frontend Development

1. Navigate to the frontend directory
2. Install dependencies
3. Start the development server

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 11. Testing

### 11.1 Backend Testing

Backend tests are implemented using pytest:

```bash
# Run all tests
pytest app/tests/

# Run with coverage
pytest --cov=app app/tests/
```

### 11.2 Load Testing with Locust

Locust is used for load testing the API:

```bash
# Run Locust server
locust -f attendance_locustfile.py --host=http://localhost:8000

# Access Locust web interface
# http://localhost:8089
```

Key test scenarios include:
- Employee management operations
- Attendance recording
- Team analytics
- AI insight generation

### 11.3 Performance Benchmarks

Baseline performance expectations:
- API response time < 200ms for most endpoints
- Support for 100+ concurrent users
- < 1% error rate under normal load
- AI insights generation < 1s

## 12. Security Considerations

1. **API Security**
   - API key authentication for admin endpoints
   - Input validation with Pydantic
   - Parameter validation
   - SQL injection prevention

2. **Frontend Security**
   - Content Security Policy headers
   - XSS protection
   - Clickjacking prevention
   - CSRF protection

3. **Docker Security**
   - Non-root user in containers
   - Minimal base images
   - Multi-stage builds
   - No secrets in images

## 13. Future Enhancements

1. **Authentication & Authorization**
   - JWT token-based authentication
   - Role-based access control
   - Single Sign-On (SSO) integration

2. **Advanced AI Features**
   - Predictive analytics for absence patterns
   - Anomaly detection for unusual attendance
   - Personalized insights for managers

3. **Mobile Application**
   - Native mobile apps for iOS and Android
   - Push notifications
   - Geolocation-based check-in

4. **Integration Capabilities**
   - Integration with HR systems
   - Calendar integrations
   - Slack/Teams notifications

## Appendix A: Environment Variables

### Backend Environment Variables
```
# PostgreSQL Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/attendance_db

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_API_VERSION=2023-07-01-preview
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_MODEL=gpt-4o

# API Configuration
API_PORT=8000
ADMIN_API_KEY=dev_reset_key
```

### Frontend Environment Variables
```
# API URL for development
VITE_API_URL=http://localhost:8000

# API URL for production
# VITE_API_URL=https://attendance-api-7b8h.onrender.com
```

## Appendix B: Troubleshooting

### Common Issues

1. **Database connection errors**
   - Verify PostgreSQL is running
   - Check DATABASE_URL environment variable
   - Ensure database exists and is accessible

2. **AI service errors**
   - Verify Azure OpenAI API key
   - Check API version compatibility
   - Test endpoint accessibility

3. **Docker issues**
   - Verify Docker and Docker Compose are installed
   - Check for port conflicts
   - Ensure sufficient disk space for containers

4. **Frontend API connection issues**
   - Verify VITE_API_URL is correctly set
   - Check CORS configuration in backend
   - Verify network connectivity between services 