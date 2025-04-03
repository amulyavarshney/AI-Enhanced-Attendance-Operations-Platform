-- Create enum types
CREATE TYPE attendance_status AS ENUM ('present', 'absent', 'wfh', 'half_day');
CREATE TYPE employee_role AS ENUM ('admin', 'manager', 'employee');

-- Create departments table
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employees table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role employee_role DEFAULT 'employee',
    team_id INTEGER REFERENCES teams(id),
    department_id INTEGER REFERENCES departments(id),
    hire_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create attendance table
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    date DATE NOT NULL,
    status attendance_status NOT NULL,
    check_in TIMESTAMP WITH TIME ZONE,
    check_out TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, date)
);

-- Create leave_requests table
CREATE TABLE leave_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    leave_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reason TEXT,
    approved_by INTEGER REFERENCES employees(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create attendance_analytics table
CREATE TABLE attendance_analytics (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    date DATE NOT NULL,
    total_employees INTEGER NOT NULL,
    present_count INTEGER NOT NULL,
    absent_count INTEGER NOT NULL,
    wfh_count INTEGER NOT NULL,
    half_day_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, date)
);

-- Create ai_insights table
CREATE TABLE ai_insights (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    summary TEXT NOT NULL,
    details JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_attendance_employee_date ON attendance(employee_id, date);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_employees_team ON employees(team_id);
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_teams_department ON teams(department_id);
CREATE INDEX idx_leave_requests_employee ON leave_requests(employee_id);
CREATE INDEX idx_leave_requests_status ON leave_requests(status);
CREATE INDEX idx_attendance_analytics_team_date ON attendance_analytics(team_id, date);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_departments_updated_at
    BEFORE UPDATE ON departments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attendance_updated_at
    BEFORE UPDATE ON attendance
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leave_requests_updated_at
    BEFORE UPDATE ON leave_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attendance_analytics_updated_at
    BEFORE UPDATE ON attendance_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to calculate attendance analytics
CREATE OR REPLACE FUNCTION calculate_team_attendance_analytics(
    p_team_id INTEGER,
    p_date DATE
)
RETURNS void AS $$
BEGIN
    INSERT INTO attendance_analytics (
        team_id,
        date,
        total_employees,
        present_count,
        absent_count,
        wfh_count,
        half_day_count
    )
    SELECT 
        p_team_id,
        p_date,
        COUNT(DISTINCT e.id) as total_employees,
        COUNT(DISTINCT CASE WHEN a.status = 'present' THEN e.id END) as present_count,
        COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN e.id END) as absent_count,
        COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN e.id END) as wfh_count,
        COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN e.id END) as half_day_count
    FROM employees e
    LEFT JOIN attendance a ON e.id = a.employee_id AND a.date = p_date
    WHERE e.team_id = p_team_id
    ON CONFLICT (team_id, date) DO UPDATE
    SET
        total_employees = EXCLUDED.total_employees,
        present_count = EXCLUDED.present_count,
        absent_count = EXCLUDED.absent_count,
        wfh_count = EXCLUDED.wfh_count,
        half_day_count = EXCLUDED.half_day_count,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql; 