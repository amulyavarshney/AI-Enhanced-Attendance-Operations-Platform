-- Create the attendance database
CREATE DATABASE attendance_db;

-- Connect to the database
\c attendance_db;

-- Create enum types
CREATE TYPE attendance_type AS ENUM ('present', 'absent', 'half_day', 'wfh', 'leave');
CREATE TYPE role_type AS ENUM ('employee', 'manager', 'admin');

-- Create teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on team name for quick lookup
CREATE INDEX idx_team_name ON teams(name);

-- Create employees table
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
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employee_team ON employees(team_id);
CREATE INDEX idx_employee_role ON employees(role);

-- Create attendance table
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

-- Create indexes on attendance table for faster queries
CREATE INDEX idx_attendance_employee_id ON attendance(employee_id);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_attendance_status ON attendance(status);
CREATE INDEX idx_attendance_employee_date ON attendance(employee_id, date);

-- Create team_trends table
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

-- Create index on team_trends for faster lookups
CREATE INDEX idx_team_trends_team ON team_trends(team_id);
CREATE INDEX idx_team_trends_date ON team_trends(date);
CREATE INDEX idx_team_trends_team_date ON team_trends(team_id, date);

-- Create ai_insights table
CREATE TABLE ai_insights (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    summary TEXT NOT NULL,
    details JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on ai_insights for faster lookups
CREATE INDEX idx_ai_insights_generated_at ON ai_insights(generated_at);

-- Insert sample data for teams
INSERT INTO teams (name) VALUES 
('Engineering'),
('Product'),
('Marketing'),
('Sales'),
('Human Resources');

-- Insert sample data for employees
INSERT INTO employees (first_name, last_name, email, phone, role, team_id, hire_date) VALUES
-- Engineering team
('John', 'Doe', 'john.doe@example.com', '123-456-7890', 'manager', 1, '2022-01-15'),
('Jane', 'Smith', 'jane.smith@example.com', '123-456-7891', 'employee', 1, '2022-02-01'),
('Michael', 'Johnson', 'michael.johnson@example.com', '123-456-7892', 'employee', 1, '2022-03-10'),

-- Product team
('Emily', 'Williams', 'emily.williams@example.com', '123-456-7893', 'manager', 2, '2022-01-20'),
('David', 'Brown', 'david.brown@example.com', '123-456-7894', 'employee', 2, '2022-02-15'),

-- Marketing team
('Sarah', 'Jones', 'sarah.jones@example.com', '123-456-7895', 'manager', 3, '2022-01-25'),
('Robert', 'Miller', 'robert.miller@example.com', '123-456-7896', 'employee', 3, '2022-02-20'),

-- Sales team
('Jessica', 'Davis', 'jessica.davis@example.com', '123-456-7897', 'manager', 4, '2022-01-10'),
('Thomas', 'Wilson', 'thomas.wilson@example.com', '123-456-7898', 'employee', 4, '2022-03-01'),

-- HR team
('Lisa', 'Moore', 'lisa.moore@example.com', '123-456-7899', 'manager', 5, '2022-01-05'),
('James', 'Taylor', 'james.taylor@example.com', '123-456-7900', 'employee', 5, '2022-02-05');

-- Insert sample attendance data (last 7 days)
-- Day 1
INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes) VALUES
(1, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '09:00', CURRENT_DATE - 6 + TIME '17:30', NULL),
(2, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '08:45', CURRENT_DATE - 6 + TIME '17:15', NULL),
(3, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '09:15', CURRENT_DATE - 6 + TIME '18:00', NULL),
(4, CURRENT_DATE - 2, 'wfh', CURRENT_DATE - 6 + TIME '09:30', CURRENT_DATE - 6 + TIME '17:45', 'Working on product roadmap'),
(5, CURRENT_DATE - 2, 'absent', NULL, NULL, 'Sick leave'),
(6, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '08:30', CURRENT_DATE - 6 + TIME '16:30', NULL),
(7, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '09:00', CURRENT_DATE - 6 + TIME '17:00', NULL),
(8, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '08:45', CURRENT_DATE - 6 + TIME '17:30', NULL),
(9, CURRENT_DATE - 2, 'half_day', CURRENT_DATE - 6 + TIME '09:00', CURRENT_DATE - 6 + TIME '13:00', 'Doctor appointment'),
(10, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '08:30', CURRENT_DATE - 6 + TIME '17:00', NULL),
(11, CURRENT_DATE - 2, 'present', CURRENT_DATE - 6 + TIME '09:15', CURRENT_DATE - 6 + TIME '17:45', NULL);

-- Day 2
INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes) VALUES
(1, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '09:00', CURRENT_DATE - 5 + TIME '17:30', NULL),
(2, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '08:50', CURRENT_DATE - 5 + TIME '17:20', NULL),
(3, CURRENT_DATE - 1, 'wfh', CURRENT_DATE - 5 + TIME '09:10', CURRENT_DATE - 5 + TIME '18:15', 'Working on new feature'),
(4, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '09:00', CURRENT_DATE - 5 + TIME '17:30', NULL),
(5, CURRENT_DATE - 1, 'absent', NULL, NULL, 'Sick leave'),
(6, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '08:45', CURRENT_DATE - 5 + TIME '16:45', NULL),
(7, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '09:00', CURRENT_DATE - 5 + TIME '17:15', NULL),
(8, CURRENT_DATE - 1, 'leave', NULL, NULL, 'Vacation'),
(9, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '08:55', CURRENT_DATE - 5 + TIME '17:25', NULL),
(10, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '08:30', CURRENT_DATE - 5 + TIME '17:00', NULL),
(11, CURRENT_DATE - 1, 'present', CURRENT_DATE - 5 + TIME '09:05', CURRENT_DATE - 5 + TIME '17:35', NULL);

-- Day 3
INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes) VALUES
(1, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '09:00', CURRENT_DATE - 4 + TIME '17:30', NULL),
(2, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '08:45', CURRENT_DATE - 4 + TIME '17:15', NULL),
(3, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '09:15', CURRENT_DATE - 4 + TIME '18:00', NULL),
(4, CURRENT_DATE, 'wfh', CURRENT_DATE - 4 + TIME '09:30', CURRENT_DATE - 4 + TIME '17:45', 'Working on product roadmap'),
(5, CURRENT_DATE, 'absent', NULL, NULL, 'Sick leave'),
(6, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '08:30', CURRENT_DATE - 4 + TIME '16:30', NULL),
(7, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '09:00', CURRENT_DATE - 4 + TIME '17:00', NULL),
(8, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '08:45', CURRENT_DATE - 4 + TIME '17:30', NULL),
(9, CURRENT_DATE, 'half_day', CURRENT_DATE - 4 + TIME '09:00', CURRENT_DATE - 4 + TIME '13:00', 'Doctor appointment'),
(10, CURRENT_DATE, 'present', CURRENT_DATE - 4 + TIME '08:30', CURRENT_DATE - 4 + TIME '17:00', NULL),

-- Insert sample AI insights
INSERT INTO ai_insights (query, summary, details, generated_at) VALUES
('Attendance trends for Engineering team', 'The Engineering team has maintained a 90% attendance rate over the past month.', 
 '{"present_percentage": 90, "wfh_percentage": 5, "absent_percentage": 3, "half_day_percentage": 2}', 
 CURRENT_TIMESTAMP - INTERVAL '7 days'),
('Who has the most WFH days?', 'Michael Johnson has the highest number of work-from-home days in the past month.', 
 '{"top_wfh_employees": [{"name": "Michael Johnson", "wfh_days": 7}, {"name": "Emily Williams", "wfh_days": 5}]}', 
 CURRENT_TIMESTAMP - INTERVAL '5 days'),
('Department with highest absence rate', 'The Product team has the highest absence rate at 8% over the past quarter.', 
 '{"department_absence_rates": [{"name": "Product", "rate": 8}, {"name": "Sales", "rate": 6}, {"name": "Engineering", "rate": 4}]}', 
 CURRENT_TIMESTAMP - INTERVAL '3 days');

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