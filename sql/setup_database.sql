-- Main setup script for Attendance Management System
-- This script will execute all necessary SQL scripts in the correct order

-- Schema first - create tables, indexes, constraints, types, and triggers
\echo 'Creating database schema...'
\i schema/schema.sql

-- Maintenance tables and functions - need these before data loading for logging
\echo 'Setting up maintenance functions...'
\i maintenance/db_maintenance.sql

-- Load initial and mock data
\echo 'Loading data...'
\i data/mock_data.sql

-- Create reports and analytics functions
\echo 'Setting up reporting functions...'
\i reports/reports.sql

-- Final database optimization
\echo 'Performing initial database optimization...'
SELECT run_and_log_maintenance('optimize');
SELECT run_and_log_maintenance('collect_stats');

\echo 'Database setup completed successfully!' 