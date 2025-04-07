-- Database Schema for Attendance Management System

-- Create Enum Types
CREATE TYPE attendance_type AS ENUM ('present', 'absent', 'half_day', 'wfh', 'leave');
CREATE TYPE role_type AS ENUM ('employee', 'manager', 'admin');

-- Teams Table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on team name for quick lookup
CREATE INDEX idx_team_name ON teams(name);

-- Employees Table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role role_type DEFAULT 'employee',
    team_id INTEGER REFERENCES teams(id),
    hire_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX idx_employee_email ON employees(email);
CREATE INDEX idx_employee_team ON employees(team_id);
CREATE INDEX idx_employee_role ON employees(role);

-- Attendance Table
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    date DATE DEFAULT CURRENT_DATE,
    status attendance_type NOT NULL,
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_employee_date UNIQUE (employee_id, date)
);

-- Create indexes for faster lookups and reporting
CREATE INDEX idx_attendance_employee ON attendance(employee_id);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_attendance_status ON attendance(status);
CREATE INDEX idx_attendance_employee_date ON attendance(employee_id, date);

-- Team Trends Table for analytics
CREATE TABLE team_trends (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    date DATE NOT NULL,
    total_employees INTEGER NOT NULL,
    present_count INTEGER NOT NULL,
    absent_count INTEGER NOT NULL,
    wfh_count INTEGER NOT NULL,
    half_day_count INTEGER NOT NULL,
    leave_count INTEGER NOT NULL,
    CONSTRAINT unique_team_date UNIQUE (team_id, date)
);

-- Create indexes for team trends
CREATE INDEX idx_team_trends_team ON team_trends(team_id);
CREATE INDEX idx_team_trends_date ON team_trends(date);
CREATE INDEX idx_team_trends_team_date ON team_trends(team_id, date);

-- AI Insights Table
CREATE TABLE ai_insights (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    summary TEXT NOT NULL,
    details JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on generated_at for chronological queries
CREATE INDEX idx_insights_generated_at ON ai_insights(generated_at);

-- Trigger to update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to all tables with updated_at column
CREATE TRIGGER update_teams_updated_at
BEFORE UPDATE ON teams
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employees_updated_at
BEFORE UPDATE ON employees
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attendance_updated_at
BEFORE UPDATE ON attendance
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update team_trends when attendance changes
CREATE OR REPLACE FUNCTION update_team_trends()
RETURNS TRIGGER AS $$
DECLARE
    v_team_id INTEGER;
BEGIN
    -- Get the team_id for the employee
    SELECT team_id INTO v_team_id FROM employees WHERE id = NEW.employee_id;
    
    -- Update or insert the team trends for this date
    INSERT INTO team_trends (
        team_id, 
        date, 
        total_employees,
        present_count,
        absent_count,
        wfh_count,
        half_day_count,
        leave_count
    )
    SELECT 
        e.team_id,
        NEW.date,
        COUNT(DISTINCT e.id),
        COUNT(DISTINCT CASE WHEN a.status = 'present' THEN e.id ELSE NULL END),
        COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN e.id ELSE NULL END),
        COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN e.id ELSE NULL END),
        COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN e.id ELSE NULL END),
        COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN e.id ELSE NULL END)
    FROM 
        employees e
    LEFT JOIN 
        attendance a ON e.id = a.employee_id AND a.date = NEW.date
    WHERE 
        e.team_id = v_team_id
    GROUP BY 
        e.team_id
    ON CONFLICT (team_id, date) 
    DO UPDATE SET
        total_employees = EXCLUDED.total_employees,
        present_count = EXCLUDED.present_count,
        absent_count = EXCLUDED.absent_count,
        wfh_count = EXCLUDED.wfh_count,
        half_day_count = EXCLUDED.half_day_count,
        leave_count = EXCLUDED.leave_count,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER attendance_update_team_trends
AFTER INSERT OR UPDATE ON attendance
FOR EACH ROW EXECUTE FUNCTION update_team_trends();

-- Insert sample data
-- Teams
INSERT INTO teams (name) VALUES 
('Engineering'),
('Marketing'),
('Sales'),
('Human Resources'),
('Finance');

-- Employees
INSERT INTO employees (first_name, last_name, email, phone, role, team_id, hire_date) VALUES
('John', 'Doe', 'john.doe@example.com', '555-1234', 'employee', 1, '2022-01-15'),
('Jane', 'Smith', 'jane.smith@example.com', '555-2345', 'manager', 1, '2021-05-10'),
('Michael', 'Johnson', 'michael.johnson@example.com', '555-3456', 'employee', 2, '2022-03-20'),
('Emily', 'Davis', 'emily.davis@example.com', '555-4567', 'manager', 2, '2020-11-05'),
('David', 'Wilson', 'david.wilson@example.com', '555-5678', 'employee', 3, '2022-06-12'),
('Sarah', 'Brown', 'sarah.brown@example.com', '555-6789', 'manager', 3, '2021-02-18'),
('Robert', 'Taylor', 'robert.taylor@example.com', '555-7890', 'employee', 4, '2022-09-01'),
('Lisa', 'Anderson', 'lisa.anderson@example.com', '555-8901', 'manager', 4, '2020-07-22'),
('James', 'Thomas', 'james.thomas@example.com', '555-9012', 'employee', 5, '2022-04-30'),
('Jennifer', 'Jackson', 'jennifer.jackson@example.com', '555-0123', 'admin', 5, '2019-11-15');

-- Attendance (last 7 days of data)
INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes) VALUES
-- Today
(1, CURRENT_DATE, 'present', CURRENT_DATE + '09:00:00'::interval, CURRENT_DATE + '17:00:00'::interval, NULL),
(2, CURRENT_DATE, 'present', CURRENT_DATE + '08:30:00'::interval, CURRENT_DATE + '17:30:00'::interval, NULL),
(3, CURRENT_DATE, 'wfh', CURRENT_DATE + '09:15:00'::interval, CURRENT_DATE + '16:45:00'::interval, 'Working remotely today'),
(4, CURRENT_DATE, 'present', CURRENT_DATE + '08:45:00'::interval, CURRENT_DATE + '18:00:00'::interval, NULL),
(5, CURRENT_DATE, 'absent', NULL, NULL, 'Called in sick'),
-- Yesterday
(1, CURRENT_DATE - 1, 'present', (CURRENT_DATE - 1) + '09:00:00'::interval, (CURRENT_DATE - 1) + '17:00:00'::interval, NULL),
(2, CURRENT_DATE - 1, 'present', (CURRENT_DATE - 1) + '08:30:00'::interval, (CURRENT_DATE - 1) + '17:30:00'::interval, NULL),
(3, CURRENT_DATE - 1, 'present', (CURRENT_DATE - 1) + '09:15:00'::interval, (CURRENT_DATE - 1) + '16:45:00'::interval, NULL),
(4, CURRENT_DATE - 1, 'half_day', (CURRENT_DATE - 1) + '08:45:00'::interval, (CURRENT_DATE - 1) + '12:30:00'::interval, 'Doctor appointment'),
(5, CURRENT_DATE - 1, 'present', (CURRENT_DATE - 1) + '09:30:00'::interval, (CURRENT_DATE - 1) + '17:30:00'::interval, NULL),
-- 2 days ago
(1, CURRENT_DATE - 2, 'present', (CURRENT_DATE - 2) + '09:00:00'::interval, (CURRENT_DATE - 2) + '17:00:00'::interval, NULL),
(2, CURRENT_DATE - 2, 'wfh', (CURRENT_DATE - 2) + '08:30:00'::interval, (CURRENT_DATE - 2) + '17:30:00'::interval, 'Working from home'),
(3, CURRENT_DATE - 2, 'present', (CURRENT_DATE - 2) + '09:15:00'::interval, (CURRENT_DATE - 2) + '16:45:00'::interval, NULL),
(4, CURRENT_DATE - 2, 'present', (CURRENT_DATE - 2) + '08:45:00'::interval, (CURRENT_DATE - 2) + '17:30:00'::interval, NULL),
(5, CURRENT_DATE - 2, 'present', (CURRENT_DATE - 2) + '09:30:00'::interval, (CURRENT_DATE - 2) + '17:30:00'::interval, NULL);

-- Insert some AI insights
INSERT INTO ai_insights (query, summary, details, generated_at) VALUES
('What is the attendance trend for the Engineering team?', 
 'The Engineering team has consistently high attendance with 80% present rate over the last month.',
 '{"present_rate": 0.8, "absent_rate": 0.05, "wfh_rate": 0.1, "half_day_rate": 0.05, "leave_rate": 0.0, "time_period": "last_month"}',
 CURRENT_TIMESTAMP - '7 days'::interval),
('Which team has the highest WFH rate?', 
 'Marketing team has the highest work-from-home rate at 30% over the last two weeks.',
 '{"team_wfh_rates": {"Marketing": 0.3, "Engineering": 0.15, "Sales": 0.1, "Human Resources": 0.2, "Finance": 0.05}, "time_period": "last_two_weeks"}',
 CURRENT_TIMESTAMP - '3 days'::interval),
('Who has been absent the most in the last month?', 
 'David Wilson from the Sales team has been absent 3 times in the last month.',
 '{"employee_id": 5, "name": "David Wilson", "team": "Sales", "absent_count": 3, "time_period": "last_month"}',
 CURRENT_TIMESTAMP - '1 day'::interval);

-- Create views for common queries

-- View for daily attendance summary
CREATE VIEW daily_attendance_summary AS
SELECT 
    a.date,
    COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id ELSE NULL END) AS present_count,
    COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id ELSE NULL END) AS absent_count,
    COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id ELSE NULL END) AS wfh_count,
    COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.employee_id ELSE NULL END) AS half_day_count,
    COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.employee_id ELSE NULL END) AS leave_count,
    COUNT(DISTINCT a.employee_id) AS total_recorded,
    (SELECT COUNT(*) FROM employees) AS total_employees
FROM 
    attendance a
GROUP BY 
    a.date
ORDER BY 
    a.date DESC;

-- View for team attendance summary
CREATE VIEW team_attendance_summary AS
SELECT 
    t.id AS team_id,
    t.name AS team_name,
    a.date,
    COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id ELSE NULL END) AS present_count,
    COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id ELSE NULL END) AS absent_count,
    COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id ELSE NULL END) AS wfh_count,
    COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.employee_id ELSE NULL END) AS half_day_count,
    COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.employee_id ELSE NULL END) AS leave_count,
    COUNT(DISTINCT e.id) AS team_size
FROM 
    teams t
JOIN 
    employees e ON t.id = e.team_id
LEFT JOIN 
    attendance a ON e.id = a.employee_id
GROUP BY 
    t.id, t.name, a.date
ORDER BY 
    a.date DESC, t.name;

-- View for employee attendance history
CREATE VIEW employee_attendance_history AS
SELECT 
    e.id AS employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    t.name AS team_name,
    a.date,
    a.status,
    a.check_in,
    a.check_out,
    CASE 
        WHEN a.check_out IS NOT NULL AND a.check_in IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600 
        ELSE NULL 
    END AS hours_worked,
    a.notes
FROM 
    employees e
JOIN 
    teams t ON e.team_id = t.id
LEFT JOIN 
    attendance a ON e.id = a.employee_id
ORDER BY 
    e.id, a.date DESC;
