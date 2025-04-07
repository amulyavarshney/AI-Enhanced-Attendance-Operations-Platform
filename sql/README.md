# Attendance Management System SQL Scripts

This folder contains all the SQL scripts needed to set up and maintain the Attendance Management System database.

## Folder Structure

- **schema/** - Contains database schema definitions (tables, indexes, constraints, types, triggers)
- **data/** - Contains scripts for loading initial and mock data
- **reports/** - Contains reporting functions and views
- **maintenance/** - Contains maintenance procedures, archiving, and database optimization functions

## Setup Instructions

### Option 1: Full Setup

To set up the entire database at once, run:

```bash
psql -U postgres -d attendance_db -f setup_database.sql
```

This will execute all the scripts in the correct order.

### Option 2: Individual Components

If you prefer to run scripts individually:

1. First, create the schema:
   ```bash
   psql -U postgres -d attendance_db -f schema/schema.sql
   ```

2. Then set up maintenance functions:
   ```bash
   psql -U postgres -d attendance_db -f maintenance/db_maintenance.sql
   ```

3. Load the sample data:
   ```bash
   psql -U postgres -d attendance_db -f data/mock_data.sql
   ```

4. Create reporting functions:
   ```bash
   psql -U postgres -d attendance_db -f reports/reports.sql
   ```

## Script Details

### schema/schema.sql
- Creates all database tables
- Sets up enum types
- Creates indexes and constraints
- Defines triggers
- Adds basic views

### data/mock_data.sql
- Populates tables with sample data
- Creates random attendance records
- Establishes specific attendance patterns for testing
- Sets up materialized views

### reports/reports.sql
- Contains functions for generating attendance reports
- Creates analytics functions
- Defines common reporting views

### maintenance/db_maintenance.sql
- Creates archive tables
- Defines functions for data archiving
- Adds utilities for database optimization
- Sets up monitoring for database performance

## Maintenance

### Regular Maintenance

Schedule the monthly maintenance procedure:

```sql
SELECT run_and_log_maintenance('monthly');
```

### Database Optimization

Run when performance issues are detected:

```sql
SELECT run_and_log_maintenance('optimize');
```

### Health Check

Get recommendations for maintenance tasks:

```sql
SELECT * FROM get_maintenance_recommendations();
```

Check for performance issues:

```sql
SELECT * FROM check_performance_issues();
``` 