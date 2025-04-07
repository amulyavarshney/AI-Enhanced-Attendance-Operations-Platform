-- Mock Data Script for Attendance Management System
-- This script adds historical and varied attendance data for realistic testing

-- More Teams
INSERT INTO teams (name) VALUES 
('Product Development'),
('Customer Support'),
('Quality Assurance'),
('Operations'),
('Research');

-- More Employees with varied roles and teams
INSERT INTO employees (first_name, last_name, email, phone, role, team_id, hire_date) VALUES
-- Engineering team additions
('Alex', 'Rivera', 'alex.rivera@example.com', '555-1111', 'employee', 1, '2022-02-15'),
('Sophia', 'Chen', 'sophia.chen@example.com', '555-2222', 'employee', 1, '2022-03-01'),
('Daniel', 'Kim', 'daniel.kim@example.com', '555-3333', 'employee', 1, '2021-11-10'),

-- Marketing team additions
('Olivia', 'Martinez', 'olivia.martinez@example.com', '555-4444', 'employee', 2, '2022-01-05'),
('Ethan', 'Williams', 'ethan.williams@example.com', '555-5555', 'employee', 2, '2021-09-20'),

-- Sales team additions
('Ava', 'Garcia', 'ava.garcia@example.com', '555-6666', 'employee', 3, '2022-04-11'),
('Noah', 'Lee', 'noah.lee@example.com', '555-7777', 'employee', 3, '2021-08-03'),

-- HR team additions
('Isabella', 'Lopez', 'isabella.lopez@example.com', '555-8888', 'employee', 4, '2022-05-16'),
('William', 'Harris', 'william.harris@example.com', '555-9999', 'employee', 4, '2021-10-22'),

-- Finance team additions
('Emma', 'Clark', 'emma.clark@example.com', '555-0000', 'employee', 5, '2022-06-08'),
('Liam', 'Lewis', 'liam.lewis@example.com', '555-1212', 'employee', 5, '2021-07-15'),

-- New teams
('Mia', 'Walker', 'mia.walker@example.com', '555-2323', 'manager', 6, '2021-04-18'),
('Mason', 'Hall', 'mason.hall@example.com', '555-3434', 'employee', 6, '2022-01-27'),
('Charlotte', 'Young', 'charlotte.young@example.com', '555-4545', 'employee', 6, '2022-03-15'),

('Amelia', 'Allen', 'amelia.allen@example.com', '555-5656', 'manager', 7, '2021-03-21'),
('Logan', 'King', 'logan.king@example.com', '555-6767', 'employee', 7, '2022-02-10'),
('Harper', 'Wright', 'harper.wright@example.com', '555-7878', 'employee', 7, '2022-04-05'),

('Evelyn', 'Scott', 'evelyn.scott@example.com', '555-8989', 'manager', 8, '2021-02-28'),
('James', 'Green', 'james.green@example.com', '555-9090', 'employee', 8, '2022-01-17'),
('Abigail', 'Baker', 'abigail.baker@example.com', '555-0101', 'employee', 8, '2022-03-28'),

('Benjamin', 'Adams', 'benjamin.adams@example.com', '555-1313', 'manager', 9, '2021-05-13'),
('Elizabeth', 'Nelson', 'elizabeth.nelson@example.com', '555-2424', 'employee', 9, '2022-02-22'),
('Lucas', 'Hill', 'lucas.hill@example.com', '555-3535', 'employee', 9, '2022-05-09'),

('Sofia', 'Ramirez', 'sofia.ramirez@example.com', '555-4646', 'manager', 10, '2021-06-25'),
('Henry', 'Campbell', 'henry.campbell@example.com', '555-5757', 'employee', 10, '2022-01-31'),
('Avery', 'Mitchell', 'avery.mitchell@example.com', '555-6868', 'employee', 10, '2022-04-19');

-- Function to generate random attendance data for a given date range
CREATE OR REPLACE FUNCTION generate_random_attendance(start_date DATE, end_date DATE) RETURNS VOID AS $$
DECLARE
    curr_date DATE := start_date;
    emp RECORD;
    rand FLOAT;
    status_val attendance_type;
    check_in_time TIME;
    check_out_time TIME;
    is_weekend BOOLEAN;
    emp_cursor CURSOR FOR SELECT id FROM employees;
BEGIN
    WHILE curr_date <= end_date LOOP
        -- Check if it's a weekend (Saturday=6, Sunday=0)
        is_weekend := EXTRACT(DOW FROM curr_date) IN (0, 6);
        
        -- For each employee
        OPEN emp_cursor;
        LOOP
            FETCH emp_cursor INTO emp;
            EXIT WHEN NOT FOUND;
            
            -- Skip weekends for most employees (90% probability)
            IF is_weekend AND random() < 0.9 THEN
                CONTINUE;
            END IF;
            
            -- Generate a random number to determine attendance status
            rand := random();
            
            -- Weighted probabilities for different attendance statuses
            IF rand < 0.75 THEN
                status_val := 'present';
                check_in_time := '08:00:00'::TIME + (random() * INTERVAL '120 minutes');
                check_out_time := '17:00:00'::TIME + (random() * INTERVAL '120 minutes');
            ELSIF rand < 0.85 THEN
                status_val := 'wfh';
                check_in_time := '08:30:00'::TIME + (random() * INTERVAL '90 minutes');
                check_out_time := '17:00:00'::TIME + (random() * INTERVAL '90 minutes');
            ELSIF rand < 0.9 THEN
                status_val := 'half_day';
                -- 50% morning half-day, 50% afternoon half-day
                IF random() < 0.5 THEN
                    check_in_time := '08:30:00'::TIME + (random() * INTERVAL '60 minutes');
                    check_out_time := '12:30:00'::TIME + (random() * INTERVAL '30 minutes');
                ELSE
                    check_in_time := '13:00:00'::TIME + (random() * INTERVAL '30 minutes');
                    check_out_time := '17:00:00'::TIME + (random() * INTERVAL '60 minutes');
                END IF;
            ELSIF rand < 0.97 THEN
                status_val := 'leave';
                check_in_time := NULL;
                check_out_time := NULL;
            ELSE
                status_val := 'absent';
                check_in_time := NULL;
                check_out_time := NULL;
            END IF;
            
            -- For some dates in the past, insert attendance record (avoid duplicates with existing records)
            BEGIN
                INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes)
                VALUES (
                    emp.id, 
                    curr_date, 
                    status_val,
                    CASE WHEN check_in_time IS NOT NULL THEN curr_date + check_in_time ELSE NULL END,
                    CASE WHEN check_out_time IS NOT NULL THEN curr_date + check_out_time ELSE NULL END,
                    CASE 
                        WHEN status_val = 'absent' THEN 
                            (ARRAY['Sick leave', 'Personal emergency', 'Family emergency', 'Not specified'])[1 + floor(random() * 4)]
                        WHEN status_val = 'leave' THEN 
                            (ARRAY['Vacation', 'Personal leave', 'Family event', 'Medical appointment'])[1 + floor(random() * 4)]
                        WHEN status_val = 'wfh' THEN 
                            (ARRAY['Working from home', 'Remote work day', 'Home office'])[1 + floor(random() * 3)]
                        ELSE NULL
                    END
                )
                ON CONFLICT (employee_id, date) DO NOTHING;
            EXCEPTION
                WHEN OTHERS THEN
                    -- Ignore errors
                    NULL;
            END;
            
        END LOOP;
        CLOSE emp_cursor;
        
        curr_date := curr_date + INTERVAL '1 day';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Generate attendance data for the past 90 days
SELECT generate_random_attendance(CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE - INTERVAL '3 days');

-- Create some specific patterns for analytics testing

-- Employee who's frequently absent on Mondays
DO $$
DECLARE
    mondays DATE[];
    i INTEGER;
BEGIN
    -- Find Mondays in the last 3 months
    mondays := ARRAY(
        SELECT dt 
        FROM generate_series(CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE - INTERVAL '7 days', INTERVAL '1 day') AS dt
        WHERE EXTRACT(DOW FROM dt) = 1
    );
    
    -- Mark employee 5 (David Wilson) as absent on 70% of Mondays
    FOR i IN 1..array_length(mondays, 1) LOOP
        IF random() < 0.7 THEN
            INSERT INTO attendance (employee_id, date, status, notes)
            VALUES (5, mondays[i], 'absent', 'Recurring absence on Monday')
            ON CONFLICT (employee_id, date) DO UPDATE 
            SET status = 'absent', notes = 'Recurring absence on Monday';
        END IF;
    END LOOP;
END $$;

-- Employee who always works from home on Wednesdays
DO $$
DECLARE
    wednesdays DATE[];
    i INTEGER;
BEGIN
    -- Find Wednesdays in the last 3 months
    wednesdays := ARRAY(
        SELECT dt 
        FROM generate_series(CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE - INTERVAL '7 days', INTERVAL '1 day') AS dt
        WHERE EXTRACT(DOW FROM dt) = 3
    );
    
    -- Mark employee 3 (Michael Johnson) as WFH on Wednesdays
    FOR i IN 1..array_length(wednesdays, 1) LOOP
        INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes)
        VALUES (
            3, 
            wednesdays[i], 
            'wfh', 
            wednesdays[i] + '09:00:00'::TIME + (random() * INTERVAL '30 minutes'),
            wednesdays[i] + '17:00:00'::TIME + (random() * INTERVAL '60 minutes'),
            'Regular WFH day'
        )
        ON CONFLICT (employee_id, date) DO UPDATE 
        SET status = 'wfh', notes = 'Regular WFH day';
    END LOOP;
END $$;

-- Team that has a lot of half-days on Fridays
DO $$
DECLARE
    fridays DATE[];
    team_members INTEGER[];
    i INTEGER;
    j INTEGER;
BEGIN
    -- Find Fridays in the last 3 months
    fridays := ARRAY(
        SELECT dt 
        FROM generate_series(CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE - INTERVAL '7 days', INTERVAL '1 day') AS dt
        WHERE EXTRACT(DOW FROM dt) = 5
    );
    
    -- Get Marketing team members (team_id = 2)
    team_members := ARRAY(SELECT id FROM employees WHERE team_id = 2);
    
    -- For each Friday
    FOR i IN 1..array_length(fridays, 1) LOOP
        -- For each team member
        FOR j IN 1..array_length(team_members, 1) LOOP
            -- 80% chance of half-day on Friday for Marketing team
            IF random() < 0.8 THEN
                INSERT INTO attendance (employee_id, date, status, check_in, check_out, notes)
                VALUES (
                    team_members[j], 
                    fridays[i], 
                    'half_day', 
                    fridays[i] + '08:30:00'::TIME + (random() * INTERVAL '30 minutes'),
                    fridays[i] + '13:00:00'::TIME + (random() * INTERVAL '30 minutes'),
                    'Team half-day Friday'
                )
                ON CONFLICT (employee_id, date) DO UPDATE 
                SET status = 'half_day', notes = 'Team half-day Friday';
            END IF;
        END LOOP;
    END LOOP;
END $$;

-- Vacation periods (consecutive leave days)
DO $$
DECLARE
    emp_id INTEGER;
    start_date DATE;
    vacation_length INTEGER;
    i INTEGER;
BEGIN
    -- Create several vacation periods for different employees
    FOR i IN 1..15 LOOP
        -- Random employee
        emp_id := (SELECT id FROM employees ORDER BY random() LIMIT 1);
        
        -- Random start date in the past 90 days
        start_date := CURRENT_DATE - INTERVAL '90 days' + (random() * 75)::INTEGER;
        
        -- Vacation length between 3 and 14 days
        vacation_length := 3 + (random() * 12)::INTEGER;
        
        -- Insert leave records for the vacation period
        FOR j IN 0..vacation_length-1 LOOP
            INSERT INTO attendance (employee_id, date, status, notes)
            VALUES (
                emp_id, 
                start_date + j, 
                'leave', 
                'Vacation period'
            )
            ON CONFLICT (employee_id, date) DO UPDATE 
            SET status = 'leave', notes = 'Vacation period';
        END LOOP;
    END LOOP;
END $$;

-- Generate more AI insights
INSERT INTO ai_insights (query, summary, details, generated_at) VALUES
('What departments have the highest attendance rates?', 
 'Engineering and Finance teams have the highest attendance rates at 92% and 90% respectively over the past month.',
 '{"attendance_rates": {"Engineering": 0.92, "Finance": 0.90, "Sales": 0.85, "Human Resources": 0.88, "Marketing": 0.75}, "time_period": "past_month"}',
 CURRENT_TIMESTAMP - '14 days'::interval),

('Are there any attendance patterns before holidays?', 
 'There is a 30% increase in time-off requests and a 25% increase in WFH days before major holidays.',
 '{"pre_holiday_pattern": {"leave_increase": 0.3, "wfh_increase": 0.25, "half_day_increase": 0.15}, "pattern_confidence": 0.85}',
 CURRENT_TIMESTAMP - '10 days'::interval),

('What is the average check-in time by team?', 
 'Marketing team has the latest average check-in time at 9:20 AM, while Finance has the earliest at 8:40 AM.',
 '{"average_check_in": {"Marketing": "09:20", "Sales": "09:05", "Engineering": "08:55", "Human Resources": "08:50", "Finance": "08:40"}, "time_period": "past_month"}',
 CURRENT_TIMESTAMP - '6 days'::interval),

('Which team has the most consistent work schedule?', 
 'Finance team shows the most consistent work schedule with 85% of check-ins within a 15-minute window.',
 '{"schedule_consistency": {"Finance": 0.85, "Human Resources": 0.75, "Engineering": 0.7, "Sales": 0.65, "Marketing": 0.6}, "metric": "percentage_within_15min_window"}',
 CURRENT_TIMESTAMP - '4 days'::interval),

('What is the typical duration between when someone is hired and when they take their first leave?', 
 'On average, employees take their first leave day 48 days after being hired.',
 '{"average_days_to_first_leave": 48, "median_days": 42, "by_department": {"Engineering": 52, "Marketing": 40, "Sales": 45, "Human Resources": 38, "Finance": 55}}',
 CURRENT_TIMESTAMP - '2 days'::interval);

-- Create materialized view for attendance reporting
CREATE MATERIALIZED VIEW monthly_attendance_summary AS
SELECT
    date_trunc('month', a.date) AS month,
    t.id AS team_id,
    t.name AS team_name,
    COUNT(DISTINCT e.id) AS team_size,
    COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id ELSE NULL END) AS present_count,
    COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id ELSE NULL END) AS absent_count,
    COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id ELSE NULL END) AS wfh_count,
    COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.employee_id ELSE NULL END) AS half_day_count,
    COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.employee_id ELSE NULL END) AS leave_count,
    ROUND(COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id ELSE NULL END)::numeric / 
        NULLIF(COUNT(DISTINCT CASE WHEN a.status IN ('present', 'absent', 'wfh', 'half_day', 'leave') THEN a.employee_id ELSE NULL END), 0) * 100, 2) AS present_percentage,
    ROUND(COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id ELSE NULL END)::numeric / 
        NULLIF(COUNT(DISTINCT CASE WHEN a.status IN ('present', 'absent', 'wfh', 'half_day', 'leave') THEN a.employee_id ELSE NULL END), 0) * 100, 2) AS wfh_percentage,
    ROUND(COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id ELSE NULL END)::numeric / 
        NULLIF(COUNT(DISTINCT CASE WHEN a.status IN ('present', 'absent', 'wfh', 'half_day', 'leave') THEN a.employee_id ELSE NULL END), 0) * 100, 2) AS absent_percentage,
    ROUND(AVG(EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600), 2) AS avg_hours_worked
FROM 
    teams t
JOIN 
    employees e ON t.id = e.team_id
LEFT JOIN 
    attendance a ON e.id = a.employee_id
WHERE
    a.date >= date_trunc('month', CURRENT_DATE - INTERVAL '6 months')
GROUP BY
    date_trunc('month', a.date), t.id, t.name
ORDER BY
    month DESC, team_name;

-- Create index on the materialized view
CREATE INDEX idx_monthly_summary_team ON monthly_attendance_summary(team_id);
CREATE INDEX idx_monthly_summary_month ON monthly_attendance_summary(month);

-- Create refresh function
CREATE OR REPLACE FUNCTION refresh_monthly_summary()
RETURNS TRIGGER AS $$
BEGIN
    REFRESH MATERIALIZED VIEW monthly_attendance_summary;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to refresh the materialized view
CREATE TRIGGER refresh_monthly_summary_trigger
AFTER INSERT OR UPDATE OR DELETE ON attendance
FOR EACH STATEMENT EXECUTE FUNCTION refresh_monthly_summary();

-- Create function to get employee attendance percentage for any date range
CREATE OR REPLACE FUNCTION get_employee_attendance_stats(
    p_employee_id INTEGER,
    p_start_date DATE,
    p_end_date DATE
) RETURNS TABLE (
    employee_id INTEGER,
    employee_name TEXT,
    team_name TEXT,
    total_days INTEGER,
    present_days INTEGER,
    absent_days INTEGER,
    wfh_days INTEGER,
    half_days INTEGER,
    leave_days INTEGER,
    attendance_percentage NUMERIC,
    avg_hours_worked NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.first_name || ' ' || e.last_name,
        t.name,
        (SELECT COUNT(*) FROM generate_series(p_start_date, p_end_date, INTERVAL '1 day') 
         WHERE EXTRACT(DOW FROM generate_series) NOT IN (0, 6)) AS total_workdays,
        COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.date ELSE NULL END) AS present_days,
        COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.date ELSE NULL END) AS absent_days,
        COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.date ELSE NULL END) AS wfh_days,
        COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.date ELSE NULL END) AS half_days,
        COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.date ELSE NULL END) AS leave_days,
        ROUND(
            (COUNT(DISTINCT CASE WHEN a.status IN ('present', 'wfh') THEN a.date ELSE NULL END) + 
             COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.date ELSE NULL END)::numeric / 2)::numeric /
            NULLIF((SELECT COUNT(*) FROM generate_series(p_start_date, p_end_date, INTERVAL '1 day') 
                  WHERE EXTRACT(DOW FROM generate_series) NOT IN (0, 6)), 0) * 100, 2
        ) AS attendance_percentage,
        ROUND(AVG(CASE WHEN a.check_out IS NOT NULL AND a.check_in IS NOT NULL 
                      THEN EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600 
                      ELSE NULL END), 2) AS avg_hours_worked
    FROM 
        employees e
    JOIN 
        teams t ON e.team_id = t.id
    LEFT JOIN 
        attendance a ON e.id = a.employee_id AND a.date BETWEEN p_start_date AND p_end_date
    WHERE 
        e.id = p_employee_id
    GROUP BY 
        e.id, e.first_name, e.last_name, t.name;
END;
$$ LANGUAGE plpgsql; 