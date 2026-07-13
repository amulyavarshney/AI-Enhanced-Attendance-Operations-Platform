-- First drop views to avoid dependency issues
DROP VIEW IF EXISTS daily_attendance_summary CASCADE;
DROP VIEW IF EXISTS team_attendance_trends CASCADE;

-- Drop triggers 
DROP TRIGGER IF EXISTS update_teams_timestamp ON teams;
DROP TRIGGER IF EXISTS update_employees_timestamp ON employees;
DROP TRIGGER IF EXISTS update_attendance_timestamp ON attendance;
DROP TRIGGER IF EXISTS update_team_trends_after_attendance_change ON attendance;

-- Drop functions
DROP FUNCTION IF EXISTS update_timestamp_column() CASCADE;
DROP FUNCTION IF EXISTS update_team_trends() CASCADE;

-- Drop tables with foreign key references first
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS team_trends CASCADE;
DROP TABLE IF EXISTS ai_insights CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- Finally drop enum types
DROP TYPE IF EXISTS attendancetype CASCADE;
DROP TYPE IF EXISTS role CASCADE;

-- Create enum types
CREATE TYPE attendancetype AS ENUM ('present', 'absent', 'half_day', 'wfh', 'leave');
CREATE TYPE role AS ENUM ('employee', 'manager', 'admin');

-- Create teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_teams_id ON teams(id);

-- Create employees table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    email VARCHAR UNIQUE,
    phone VARCHAR,
    role role DEFAULT 'employee',
    team_id INTEGER REFERENCES teams(id),
    hire_date DATE DEFAULT CURRENT_DATE,
    hashed_password VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_team_id ON employees(team_id);
CREATE INDEX idx_employees_id ON employees(id);

-- Create attendance table
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    date DATE DEFAULT CURRENT_DATE,
    status attendancetype NOT NULL,
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_attendance_employee_id ON attendance(employee_id);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE UNIQUE INDEX uq_attendance_employee_date ON attendance(employee_id, date);
CREATE INDEX idx_attendance_status ON attendance(status);

-- Create team_trends table
CREATE TABLE team_trends (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    date DATE NOT NULL,
    total_employees INTEGER NOT NULL,
    present_count INTEGER NOT NULL,
    absent_count INTEGER NOT NULL,
    wfh_count INTEGER NOT NULL,
    half_day_count INTEGER NOT NULL,
    leave_count INTEGER NOT NULL
);
CREATE INDEX idx_team_trends_team_id ON team_trends(team_id);
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
CREATE INDEX idx_ai_insights_generated_at ON ai_insights(generated_at);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    actor_id INTEGER REFERENCES employees(id),
    actor_email VARCHAR,
    method VARCHAR NOT NULL,
    path VARCHAR NOT NULL,
    status_code INTEGER NOT NULL,
    action VARCHAR NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);

-- Insert sample data for teams
INSERT INTO teams (name) VALUES 
('Engineering'),
('Product'),
('Marketing'),
('Sales'),
('Human Resources');

-- Insert sample data for employees
-- Default password for all seeded users: Admin123!
INSERT INTO employees (first_name, last_name, email, phone, role, team_id, hire_date, hashed_password) VALUES
-- Engineering team
('John', 'Doe', 'john.doe@example.com', '123-456-7890', 'manager'::role, 1, '2022-01-15',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),
('Jane', 'Smith', 'jane.smith@example.com', '123-456-7891', 'employee'::role, 1, '2022-02-01',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),
('Michael', 'Johnson', 'michael.johnson@example.com', '123-456-7892', 'employee'::role, 1, '2022-03-10',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),

-- Product team
('Emily', 'Williams', 'emily.williams@example.com', '123-456-7893', 'manager'::role, 2, '2022-01-20',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),
('David', 'Brown', 'david.brown@example.com', '123-456-7894', 'employee'::role, 2, '2022-02-15',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),

-- Marketing team
('Sarah', 'Jones', 'sarah.jones@example.com', '123-456-7895', 'manager'::role, 3, '2022-01-25',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),
('Robert', 'Miller', 'robert.miller@example.com', '123-456-7896', 'employee'::role, 3, '2022-02-20',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),

-- Sales team
('Jessica', 'Davis', 'jessica.davis@example.com', '123-456-7897', 'manager'::role, 4, '2022-01-10',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),
('Thomas', 'Wilson', 'thomas.wilson@example.com', '123-456-7898', 'employee'::role, 4, '2022-03-01',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),

-- HR team
('Lisa', 'Moore', 'lisa.moore@example.com', '123-456-7899', 'manager'::role, 5, '2022-01-05',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),
('James', 'Taylor', 'james.taylor@example.com', '123-456-7900', 'employee'::role, 5, '2022-02-05',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e'),

-- Platform admin (password: Admin123!)
('Platform', 'Admin', 'admin@example.com', '000-000-0000', 'admin'::role, 1, '2022-01-01',
 '$2b$12$725RI/Kr.uNs9hD70huHp.dK1X7b3bhVbECrhMSC3KDsPp4kCxL7e');

-- Insert sample attendance data (last 7 days)
-- Day 1
INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes) VALUES
(1, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '09:00', CURRENT_DATE - 6 + TIME '17:30', NULL),
(2, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '08:45', CURRENT_DATE - 6 + TIME '17:15', NULL),
(3, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '09:15', CURRENT_DATE - 6 + TIME '18:00', NULL),
(4, CURRENT_DATE - 2, 'wfh'::attendancetype, CURRENT_DATE - 6 + TIME '09:30', CURRENT_DATE - 6 + TIME '17:45', 'Working on product roadmap'),
(5, CURRENT_DATE - 2, 'absent'::attendancetype, NULL, NULL, 'Sick leave'),
(6, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '08:30', CURRENT_DATE - 6 + TIME '16:30', NULL),
(7, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '09:00', CURRENT_DATE - 6 + TIME '17:00', NULL),
(8, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '08:45', CURRENT_DATE - 6 + TIME '17:30', NULL),
(9, CURRENT_DATE - 2, 'half_day'::attendancetype, CURRENT_DATE - 6 + TIME '09:00', CURRENT_DATE - 6 + TIME '13:00', 'Doctor appointment'),
(10, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '08:30', CURRENT_DATE - 6 + TIME '17:00', NULL),
(11, CURRENT_DATE - 2, 'present'::attendancetype, CURRENT_DATE - 6 + TIME '09:15', CURRENT_DATE - 6 + TIME '17:45', NULL);

-- Day 2
INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes) VALUES
(1, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '09:00', CURRENT_DATE - 5 + TIME '17:30', NULL),
(2, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '08:50', CURRENT_DATE - 5 + TIME '17:20', NULL),
(3, CURRENT_DATE - 1, 'wfh'::attendancetype, CURRENT_DATE - 5 + TIME '09:10', CURRENT_DATE - 5 + TIME '18:15', 'Working on new feature'),
(4, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '09:00', CURRENT_DATE - 5 + TIME '17:30', NULL),
(5, CURRENT_DATE - 1, 'absent'::attendancetype, NULL, NULL, 'Sick leave'),
(6, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '08:45', CURRENT_DATE - 5 + TIME '16:45', NULL),
(7, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '09:00', CURRENT_DATE - 5 + TIME '17:15', NULL),
(8, CURRENT_DATE - 1, 'leave'::attendancetype, NULL, NULL, 'Vacation'),
(9, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '08:55', CURRENT_DATE - 5 + TIME '17:25', NULL),
(10, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '08:30', CURRENT_DATE - 5 + TIME '17:00', NULL),
(11, CURRENT_DATE - 1, 'present'::attendancetype, CURRENT_DATE - 5 + TIME '09:05', CURRENT_DATE - 5 + TIME '17:35', NULL);

-- Insert sample AI insights 
INSERT INTO ai_insights (query, summary, details, generated_at) VALUES
('Attendance trends for Engineering team', 'The Engineering team has maintained a 90% attendance rate over the past month.', 
 '{"present_percentage": 90, "wfh_percentage": 5, "absent_percentage": 3, "half_day_percentage": 2}'::jsonb, 
 CURRENT_TIMESTAMP - INTERVAL '7 days');

INSERT INTO ai_insights (query, summary, details, generated_at) VALUES
('Who has the most WFH days?', 'Michael Johnson has the highest number of work-from-home days in the past month.', 
 '{"top_wfh_employees": [{"name": "Michael Johnson", "wfh_days": 7}, {"name": "Emily Williams", "wfh_days": 5}]}'::jsonb, 
 CURRENT_TIMESTAMP - INTERVAL '5 days');

INSERT INTO ai_insights (query, summary, details, generated_at) VALUES
('Department with highest absence rate', 'The Product team has the highest absence rate at 8% over the past quarter.', 
 '{"department_absence_rates": [{"name": "Product", "rate": 8}, {"name": "Sales", "rate": 6}, {"name": "Engineering", "rate": 4}]}'::jsonb, 
 CURRENT_TIMESTAMP - INTERVAL '3 days');

-- Create view for daily attendance summary
CREATE OR REPLACE VIEW daily_attendance_summary AS
SELECT 
    a.date,
    t.id AS team_id,
    t.name AS team_name,
    COUNT(DISTINCT CASE WHEN a.status = 'present'::attendancetype THEN a.employee_id END) AS present_count,
    COUNT(DISTINCT CASE WHEN a.status = 'absent'::attendancetype THEN a.employee_id END) AS absent_count,
    COUNT(DISTINCT CASE WHEN a.status = 'wfh'::attendancetype THEN a.employee_id END) AS wfh_count,
    COUNT(DISTINCT CASE WHEN a.status = 'half_day'::attendancetype THEN a.employee_id END) AS half_day_count,
    COUNT(DISTINCT CASE WHEN a.status = 'leave'::attendancetype THEN a.employee_id END) AS leave_count,
    COUNT(DISTINCT e.id) AS total_employees
FROM 
    teams t
JOIN 
    employees e ON e.team_id = t.id
LEFT JOIN 
    attendance a ON a.employee_id = e.id AND a.date = CURRENT_DATE
GROUP BY 
    a.date, t.id, t.name;

-- Create view for team attendance trends
CREATE OR REPLACE VIEW team_attendance_trends AS
SELECT 
    t.id AS team_id,
    t.name AS team_name,
    a.date,
    COUNT(DISTINCT CASE WHEN a.status = 'present'::attendancetype THEN a.employee_id END) AS present_count,
    COUNT(DISTINCT CASE WHEN a.status = 'absent'::attendancetype THEN a.employee_id END) AS absent_count,
    COUNT(DISTINCT CASE WHEN a.status = 'wfh'::attendancetype THEN a.employee_id END) AS wfh_count,
    COUNT(DISTINCT CASE WHEN a.status = 'half_day'::attendancetype THEN a.employee_id END) AS half_day_count,
    COUNT(DISTINCT CASE WHEN a.status = 'leave'::attendancetype THEN a.employee_id END) AS leave_count,
    COUNT(DISTINCT e.id) AS total_employees
FROM 
    teams t
JOIN 
    employees e ON e.team_id = t.id
LEFT JOIN 
    attendance a ON a.employee_id = e.id
WHERE 
    a.date BETWEEN CURRENT_DATE - 30 AND CURRENT_DATE
GROUP BY 
    t.id, t.name, a.date
ORDER BY 
    t.name, a.date;

-- Create function for updating timestamps automatically
CREATE OR REPLACE FUNCTION update_timestamp_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_teams_timestamp BEFORE UPDATE ON teams
FOR EACH ROW EXECUTE FUNCTION update_timestamp_column();

CREATE TRIGGER update_employees_timestamp BEFORE UPDATE ON employees
FOR EACH ROW EXECUTE FUNCTION update_timestamp_column();

CREATE TRIGGER update_attendance_timestamp BEFORE UPDATE ON attendance
FOR EACH ROW EXECUTE FUNCTION update_timestamp_column();

-- Create function to auto-update team_trends table
CREATE OR REPLACE FUNCTION update_team_trends()
RETURNS TRIGGER AS $$
BEGIN
    -- Delete existing record for the team and date if it exists
    DELETE FROM team_trends 
    WHERE team_id = (SELECT team_id FROM employees WHERE id = NEW.employee_id)
    AND date = NEW.date;
    
    -- Insert updated record
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
        COUNT(DISTINCT CASE WHEN a.status = 'present'::attendancetype THEN a.employee_id END),
        COUNT(DISTINCT CASE WHEN a.status = 'absent'::attendancetype THEN a.employee_id END),
        COUNT(DISTINCT CASE WHEN a.status = 'wfh'::attendancetype THEN a.employee_id END),
        COUNT(DISTINCT CASE WHEN a.status = 'half_day'::attendancetype THEN a.employee_id END),
        COUNT(DISTINCT CASE WHEN a.status = 'leave'::attendancetype THEN a.employee_id END)
    FROM 
        employees e
    LEFT JOIN 
        attendance a ON a.employee_id = e.id AND a.date = NEW.date
    WHERE 
        e.team_id = (SELECT team_id FROM employees WHERE id = NEW.employee_id)
    GROUP BY 
        e.team_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating team_trends
CREATE TRIGGER update_team_trends_after_attendance_change
AFTER INSERT OR UPDATE ON attendance
FOR EACH ROW
EXECUTE FUNCTION update_team_trends();