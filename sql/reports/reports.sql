-- Reports and Analytics for Attendance Management System
-- Contains SQL queries and functions for generating various attendance reports

-- Function to get attendance summary for a specific date range
CREATE OR REPLACE FUNCTION get_attendance_summary(
    start_date DATE,
    end_date DATE
) RETURNS TABLE (
    date DATE,
    total_employees INTEGER,
    present_count INTEGER,
    absent_count INTEGER,
    wfh_count INTEGER,
    half_day_count INTEGER,
    leave_count INTEGER,
    attendance_percentage NUMERIC,
    present_percentage NUMERIC,
    wfh_percentage NUMERIC,
    absent_percentage NUMERIC,
    leave_percentage NUMERIC,
    half_day_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH date_range AS (
        SELECT d::DATE
        FROM generate_series(start_date, end_date, '1 day'::INTERVAL) d
    ),
    employee_count AS (
        SELECT COUNT(id) AS count
        FROM employees
        WHERE hire_date <= end_date
    ),
    daily_attendance AS (
        SELECT
            d.d AS date,
            COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id END) AS present_count,
            COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id END) AS absent_count,
            COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id END) AS wfh_count,
            COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.employee_id END) AS half_day_count,
            COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.employee_id END) AS leave_count,
            (SELECT count FROM employee_count) AS total_employees
        FROM
            date_range d
        LEFT JOIN
            attendance a ON d.d = a.date
        GROUP BY
            d.d
    )
    SELECT
        date,
        total_employees,
        present_count,
        absent_count,
        wfh_count,
        half_day_count,
        leave_count,
        ROUND(
            (present_count + wfh_count + (half_day_count::NUMERIC / 2)) / 
            NULLIF(total_employees, 0) * 100, 
            2
        ) AS attendance_percentage,
        ROUND(present_count::NUMERIC / NULLIF(total_employees, 0) * 100, 2) AS present_percentage,
        ROUND(wfh_count::NUMERIC / NULLIF(total_employees, 0) * 100, 2) AS wfh_percentage,
        ROUND(absent_count::NUMERIC / NULLIF(total_employees, 0) * 100, 2) AS absent_percentage,
        ROUND(leave_count::NUMERIC / NULLIF(total_employees, 0) * 100, 2) AS leave_percentage,
        ROUND(half_day_count::NUMERIC / NULLIF(total_employees, 0) * 100, 2) AS half_day_percentage
    FROM
        daily_attendance
    ORDER BY
        date;
END;
$$ LANGUAGE plpgsql;

-- Function to get team attendance summary for a specific date range
CREATE OR REPLACE FUNCTION get_team_attendance_summary(
    p_team_id INTEGER,
    start_date DATE,
    end_date DATE
) RETURNS TABLE (
    date DATE,
    team_id INTEGER,
    team_name TEXT,
    total_employees INTEGER,
    present_count INTEGER,
    absent_count INTEGER,
    wfh_count INTEGER,
    half_day_count INTEGER,
    leave_count INTEGER,
    attendance_percentage NUMERIC,
    avg_check_in TIME,
    avg_check_out TIME,
    avg_hours_worked NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH date_range AS (
        SELECT d::DATE
        FROM generate_series(start_date, end_date, '1 day'::INTERVAL) d
    ),
    team_employee_count AS (
        SELECT COUNT(id) AS count
        FROM employees
        WHERE team_id = p_team_id AND hire_date <= end_date
    ),
    daily_team_attendance AS (
        SELECT
            d.d AS date,
            t.id AS team_id,
            t.name AS team_name,
            COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id END) AS present_count,
            COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id END) AS absent_count,
            COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id END) AS wfh_count,
            COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.employee_id END) AS half_day_count,
            COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.employee_id END) AS leave_count,
            (SELECT count FROM team_employee_count) AS total_employees,
            AVG(CASE WHEN a.check_in IS NOT NULL THEN a.check_in::TIME END) AS avg_check_in,
            AVG(CASE WHEN a.check_out IS NOT NULL THEN a.check_out::TIME END) AS avg_check_out,
            AVG(CASE 
                WHEN a.check_out IS NOT NULL AND a.check_in IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600 
                ELSE NULL 
            END) AS avg_hours_worked
        FROM
            date_range d
        CROSS JOIN
            teams t
        LEFT JOIN
            employees e ON e.team_id = t.id
        LEFT JOIN
            attendance a ON d.d = a.date AND e.id = a.employee_id
        WHERE
            t.id = p_team_id
        GROUP BY
            d.d, t.id, t.name
    )
    SELECT
        date,
        team_id,
        team_name,
        total_employees,
        present_count,
        absent_count,
        wfh_count,
        half_day_count,
        leave_count,
        ROUND(
            (present_count + wfh_count + (half_day_count::NUMERIC / 2)) / 
            NULLIF(total_employees, 0) * 100, 
            2
        ) AS attendance_percentage,
        avg_check_in,
        avg_check_out,
        ROUND(avg_hours_worked, 2) AS avg_hours_worked
    FROM
        daily_team_attendance
    ORDER BY
        date;
END;
$$ LANGUAGE plpgsql;

-- Function to get employee attendance for a specific date range
CREATE OR REPLACE FUNCTION get_employee_attendance(
    p_employee_id INTEGER,
    start_date DATE,
    end_date DATE
) RETURNS TABLE (
    date DATE,
    day_of_week TEXT,
    status attendance_type,
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    hours_worked NUMERIC,
    notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH date_range AS (
        SELECT d::DATE
        FROM generate_series(start_date, end_date, '1 day'::INTERVAL) d
    )
    SELECT
        d.d AS date,
        TO_CHAR(d.d, 'Day') AS day_of_week,
        COALESCE(a.status, 
                 CASE WHEN EXTRACT(DOW FROM d.d) IN (0, 6) THEN NULL ELSE 'absent'::attendance_type END) AS status,
        a.check_in,
        a.check_out,
        CASE 
            WHEN a.check_out IS NOT NULL AND a.check_in IS NOT NULL 
            THEN ROUND(EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600, 2)
            ELSE NULL 
        END AS hours_worked,
        a.notes
    FROM
        date_range d
    LEFT JOIN
        attendance a ON d.d = a.date AND a.employee_id = p_employee_id
    ORDER BY
        d.d;
END;
$$ LANGUAGE plpgsql;

-- Monthly attendance summary report
CREATE OR REPLACE FUNCTION get_monthly_attendance_summary(
    year INTEGER,
    month INTEGER
) RETURNS TABLE (
    team_name TEXT,
    total_employees INTEGER,
    avg_attendance_percentage NUMERIC,
    avg_present_percentage NUMERIC,
    avg_wfh_percentage NUMERIC,
    avg_absent_percentage NUMERIC,
    avg_leave_percentage NUMERIC,
    avg_half_day_percentage NUMERIC,
    avg_hours_worked NUMERIC
) AS $$
DECLARE
    start_date DATE;
    end_date DATE;
BEGIN
    -- Calculate the start and end dates for the given month
    start_date := make_date(year, month, 1);
    end_date := (start_date + INTERVAL '1 month' - INTERVAL '1 day')::DATE;
    
    RETURN QUERY
    WITH daily_attendance AS (
        SELECT
            t.name AS team_name,
            date,
            COUNT(DISTINCT e.id) AS total_employees,
            COUNT(DISTINCT CASE WHEN a.status = 'present' THEN a.employee_id END) AS present_count,
            COUNT(DISTINCT CASE WHEN a.status = 'absent' THEN a.employee_id END) AS absent_count,
            COUNT(DISTINCT CASE WHEN a.status = 'wfh' THEN a.employee_id END) AS wfh_count,
            COUNT(DISTINCT CASE WHEN a.status = 'half_day' THEN a.employee_id END) AS half_day_count,
            COUNT(DISTINCT CASE WHEN a.status = 'leave' THEN a.employee_id END) AS leave_count,
            AVG(CASE 
                WHEN a.check_out IS NOT NULL AND a.check_in IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600 
                ELSE NULL 
            END) AS daily_avg_hours
        FROM
            teams t
        JOIN
            employees e ON e.team_id = t.id
        LEFT JOIN
            attendance a ON e.id = a.employee_id AND a.date BETWEEN start_date AND end_date
        WHERE
            EXTRACT(DOW FROM a.date) NOT IN (0, 6) OR a.date IS NULL
        GROUP BY
            t.name, date
    )
    SELECT
        team_name,
        MAX(total_employees) AS total_employees,
        ROUND(AVG(
            (present_count + wfh_count + (half_day_count::NUMERIC / 2)) / 
            NULLIF(total_employees, 0) * 100
        ), 2) AS avg_attendance_percentage,
        ROUND(AVG(present_count::NUMERIC / NULLIF(total_employees, 0) * 100), 2) AS avg_present_percentage,
        ROUND(AVG(wfh_count::NUMERIC / NULLIF(total_employees, 0) * 100), 2) AS avg_wfh_percentage,
        ROUND(AVG(absent_count::NUMERIC / NULLIF(total_employees, 0) * 100), 2) AS avg_absent_percentage,
        ROUND(AVG(leave_count::NUMERIC / NULLIF(total_employees, 0) * 100), 2) AS avg_leave_percentage,
        ROUND(AVG(half_day_count::NUMERIC / NULLIF(total_employees, 0) * 100), 2) AS avg_half_day_percentage,
        ROUND(AVG(daily_avg_hours), 2) AS avg_hours_worked
    FROM
        daily_attendance
    GROUP BY
        team_name
    ORDER BY
        avg_attendance_percentage DESC;
END;
$$ LANGUAGE plpgsql;

-- Report for employees with highest absences
CREATE OR REPLACE FUNCTION get_high_absence_employees(
    start_date DATE,
    end_date DATE,
    min_absences INTEGER DEFAULT 3
) RETURNS TABLE (
    employee_id INTEGER,
    employee_name TEXT,
    team_name TEXT,
    absence_count INTEGER,
    absence_percentage NUMERIC,
    most_common_day TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH workdays AS (
        SELECT COUNT(*) AS total_workdays
        FROM generate_series(start_date, end_date, '1 day'::INTERVAL) d
        WHERE EXTRACT(DOW FROM d) NOT IN (0, 6)
    ),
    absence_data AS (
        SELECT
            e.id AS employee_id,
            e.first_name || ' ' || e.last_name AS employee_name,
            t.name AS team_name,
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS absence_count,
            TO_CHAR(MODE() WITHIN GROUP (ORDER BY a.date), 'Day') AS most_common_day
        FROM
            employees e
        JOIN
            teams t ON e.team_id = t.id
        LEFT JOIN
            attendance a ON e.id = a.employee_id 
                AND a.date BETWEEN start_date AND end_date
                AND a.status = 'absent'
        GROUP BY
            e.id, e.first_name, e.last_name, t.name
        HAVING
            COUNT(CASE WHEN a.status = 'absent' THEN 1 END) >= min_absences
    )
    SELECT
        a.employee_id,
        a.employee_name,
        a.team_name,
        a.absence_count,
        ROUND((a.absence_count::NUMERIC / w.total_workdays) * 100, 2) AS absence_percentage,
        a.most_common_day
    FROM
        absence_data a
    CROSS JOIN
        workdays w
    ORDER BY
        a.absence_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to identify attendance patterns
CREATE OR REPLACE FUNCTION identify_attendance_patterns(
    min_occurrence INTEGER DEFAULT 3
) RETURNS TABLE (
    employee_id INTEGER,
    employee_name TEXT,
    team_name TEXT,
    pattern_type TEXT,
    day_of_week TEXT,
    count INTEGER,
    percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    
    -- Identify Monday absence patterns
    SELECT
        e.id AS employee_id,
        e.first_name || ' ' || e.last_name AS employee_name,
        t.name AS team_name,
        'Monday Absences' AS pattern_type,
        'Monday' AS day_of_week,
        COUNT(*) AS count,
        ROUND(
            COUNT(*)::NUMERIC / NULLIF(
                (SELECT COUNT(DISTINCT date) 
                 FROM attendance 
                 WHERE EXTRACT(DOW FROM date) = 1), 0
            ) * 100,
            2
        ) AS percentage
    FROM
        employees e
    JOIN
        teams t ON e.team_id = t.id
    JOIN
        attendance a ON e.id = a.employee_id
    WHERE
        EXTRACT(DOW FROM a.date) = 1  -- Monday
        AND a.status = 'absent'
    GROUP BY
        e.id, e.first_name, e.last_name, t.name
    HAVING
        COUNT(*) >= min_occurrence
    
    UNION ALL
    
    -- Identify Friday leave/half-day patterns
    SELECT
        e.id AS employee_id,
        e.first_name || ' ' || e.last_name AS employee_name,
        t.name AS team_name,
        'Friday Leave/Half-days' AS pattern_type,
        'Friday' AS day_of_week,
        COUNT(*) AS count,
        ROUND(
            COUNT(*)::NUMERIC / NULLIF(
                (SELECT COUNT(DISTINCT date) 
                 FROM attendance 
                 WHERE EXTRACT(DOW FROM date) = 5), 0
            ) * 100,
            2
        ) AS percentage
    FROM
        employees e
    JOIN
        teams t ON e.team_id = t.id
    JOIN
        attendance a ON e.id = a.employee_id
    WHERE
        EXTRACT(DOW FROM a.date) = 5  -- Friday
        AND a.status IN ('leave', 'half_day')
    GROUP BY
        e.id, e.first_name, e.last_name, t.name
    HAVING
        COUNT(*) >= min_occurrence
    
    UNION ALL
    
    -- Identify WFH on specific day patterns
    SELECT
        e.id AS employee_id,
        e.first_name || ' ' || e.last_name AS employee_name,
        t.name AS team_name,
        'Regular WFH Day' AS pattern_type,
        TO_CHAR(a.date, 'Day') AS day_of_week,
        COUNT(*) AS count,
        ROUND(
            COUNT(*)::NUMERIC / NULLIF(
                (SELECT COUNT(DISTINCT date) 
                 FROM attendance 
                 WHERE EXTRACT(DOW FROM date) = EXTRACT(DOW FROM a.date)), 0
            ) * 100,
            2
        ) AS percentage
    FROM
        employees e
    JOIN
        teams t ON e.team_id = t.id
    JOIN
        attendance a ON e.id = a.employee_id
    WHERE
        a.status = 'wfh'
    GROUP BY
        e.id, e.first_name, e.last_name, t.name, EXTRACT(DOW FROM a.date), TO_CHAR(a.date, 'Day')
    HAVING
        COUNT(*) >= min_occurrence
        AND ROUND(
            COUNT(*)::NUMERIC / NULLIF(
                (SELECT COUNT(DISTINCT date) 
                 FROM attendance 
                 WHERE EXTRACT(DOW FROM date) = EXTRACT(DOW FROM a.date)), 0
            ) * 100,
            2
        ) >= 50  -- At least 50% of this day is WFH
    
    ORDER BY
        pattern_type, percentage DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get late arrival report
CREATE OR REPLACE FUNCTION get_late_arrival_report(
    start_date DATE,
    end_date DATE,
    late_threshold TIME DEFAULT '09:30:00'::TIME
) RETURNS TABLE (
    employee_id INTEGER,
    employee_name TEXT,
    team_name TEXT,
    late_count INTEGER,
    total_workdays INTEGER,
    late_percentage NUMERIC,
    avg_arrival_time TIME
) AS $$
BEGIN
    RETURN QUERY
    WITH late_arrivals AS (
        SELECT
            e.id AS employee_id,
            e.first_name || ' ' || e.last_name AS employee_name,
            t.name AS team_name,
            COUNT(CASE WHEN a.check_in::TIME > late_threshold THEN 1 END) AS late_count,
            COUNT(CASE WHEN a.status IN ('present', 'half_day') THEN 1 END) AS total_workdays,
            AVG(a.check_in::TIME) AS avg_arrival_time
        FROM
            employees e
        JOIN
            teams t ON e.team_id = t.id
        LEFT JOIN
            attendance a ON e.id = a.employee_id 
                AND a.date BETWEEN start_date AND end_date
                AND a.status IN ('present', 'half_day')
        GROUP BY
            e.id, e.first_name, e.last_name, t.name
        HAVING
            COUNT(CASE WHEN a.check_in::TIME > late_threshold THEN 1 END) > 0
    )
    SELECT
        employee_id,
        employee_name,
        team_name,
        late_count,
        total_workdays,
        ROUND((late_count::NUMERIC / total_workdays) * 100, 2) AS late_percentage,
        avg_arrival_time
    FROM
        late_arrivals
    ORDER BY
        late_percentage DESC;
END;
$$ LANGUAGE plpgsql;

-- Average work hours by team and day of week
CREATE OR REPLACE FUNCTION get_avg_work_hours_by_team_and_day(
    start_date DATE,
    end_date DATE
) RETURNS TABLE (
    team_name TEXT,
    day_of_week TEXT,
    avg_hours_worked NUMERIC,
    avg_check_in TIME,
    avg_check_out TIME
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.name AS team_name,
        TO_CHAR(a.date, 'Day') AS day_of_week,
        ROUND(AVG(
            CASE 
                WHEN a.check_out IS NOT NULL AND a.check_in IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (a.check_out - a.check_in))/3600 
                ELSE NULL 
            END
        ), 2) AS avg_hours_worked,
        (AVG(a.check_in::TIME))::TIME AS avg_check_in,
        (AVG(a.check_out::TIME))::TIME AS avg_check_out
    FROM
        teams t
    JOIN
        employees e ON e.team_id = t.id
    JOIN
        attendance a ON e.id = a.employee_id
    WHERE
        a.date BETWEEN start_date AND end_date
        AND a.status IN ('present', 'wfh', 'half_day')
        AND a.check_in IS NOT NULL
        AND a.check_out IS NOT NULL
    GROUP BY
        t.name, EXTRACT(DOW FROM a.date), TO_CHAR(a.date, 'Day')
    ORDER BY
        t.name, EXTRACT(DOW FROM a.date);
END;
$$ LANGUAGE plpgsql;

-- Year-over-year attendance comparison
CREATE OR REPLACE FUNCTION get_yoy_attendance_comparison(
    current_year INTEGER,
    previous_year INTEGER
) RETURNS TABLE (
    month TEXT,
    current_year_attendance NUMERIC,
    previous_year_attendance NUMERIC,
    change NUMERIC,
    current_year_wfh NUMERIC,
    previous_year_wfh NUMERIC,
    wfh_change NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH current_year_data AS (
        SELECT
            TO_CHAR(a.date, 'Month') AS month,
            EXTRACT(MONTH FROM a.date) AS month_num,
            ROUND(
                COUNT(CASE WHEN a.status IN ('present', 'wfh') OR a.status = 'half_day' THEN a.employee_id END)::NUMERIC /
                NULLIF(COUNT(DISTINCT e.id) * COUNT(DISTINCT a.date), 0) * 100,
                2
            ) AS attendance_percentage,
            ROUND(
                COUNT(CASE WHEN a.status = 'wfh' THEN a.employee_id END)::NUMERIC /
                NULLIF(COUNT(DISTINCT e.id) * COUNT(DISTINCT a.date), 0) * 100,
                2
            ) AS wfh_percentage
        FROM
            employees e
        LEFT JOIN
            attendance a ON e.id = a.employee_id
        WHERE
            EXTRACT(YEAR FROM a.date) = current_year
            AND EXTRACT(DOW FROM a.date) NOT IN (0, 6)
        GROUP BY
            EXTRACT(MONTH FROM a.date), TO_CHAR(a.date, 'Month')
    ),
    previous_year_data AS (
        SELECT
            TO_CHAR(a.date, 'Month') AS month,
            EXTRACT(MONTH FROM a.date) AS month_num,
            ROUND(
                COUNT(CASE WHEN a.status IN ('present', 'wfh') OR a.status = 'half_day' THEN a.employee_id END)::NUMERIC /
                NULLIF(COUNT(DISTINCT e.id) * COUNT(DISTINCT a.date), 0) * 100,
                2
            ) AS attendance_percentage,
            ROUND(
                COUNT(CASE WHEN a.status = 'wfh' THEN a.employee_id END)::NUMERIC /
                NULLIF(COUNT(DISTINCT e.id) * COUNT(DISTINCT a.date), 0) * 100,
                2
            ) AS wfh_percentage
        FROM
            employees e
        LEFT JOIN
            attendance a ON e.id = a.employee_id
        WHERE
            EXTRACT(YEAR FROM a.date) = previous_year
            AND EXTRACT(DOW FROM a.date) NOT IN (0, 6)
        GROUP BY
            EXTRACT(MONTH FROM a.date), TO_CHAR(a.date, 'Month')
    )
    SELECT
        c.month,
        c.attendance_percentage AS current_year_attendance,
        p.attendance_percentage AS previous_year_attendance,
        ROUND(c.attendance_percentage - p.attendance_percentage, 2) AS change,
        c.wfh_percentage AS current_year_wfh,
        p.wfh_percentage AS previous_year_wfh,
        ROUND(c.wfh_percentage - p.wfh_percentage, 2) AS wfh_change
    FROM
        current_year_data c
    LEFT JOIN
        previous_year_data p ON c.month_num = p.month_num
    ORDER BY
        c.month_num;
END;
$$ LANGUAGE plpgsql;

-- Create some sample views for frequently used reports

-- View for current month's attendance summary
CREATE OR REPLACE VIEW current_month_attendance_summary AS
SELECT * FROM get_monthly_attendance_summary(
    EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER,
    EXTRACT(MONTH FROM CURRENT_DATE)::INTEGER
);

-- View for last 7 days attendance
CREATE OR REPLACE VIEW last_7_days_attendance AS
SELECT * FROM get_attendance_summary(
    CURRENT_DATE - INTERVAL '7 days',
    CURRENT_DATE
);

-- View for employees with attendance issues in current month
CREATE OR REPLACE VIEW current_month_attendance_issues AS
SELECT
    e.id AS employee_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    t.name AS team_name,
    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS absence_count,
    COUNT(CASE WHEN a.status = 'present' OR a.status = 'wfh' THEN 1 END) AS present_count,
    COUNT(CASE WHEN a.check_in::TIME > '09:30:00'::TIME AND a.status IN ('present', 'half_day') THEN 1 END) AS late_arrival_count,
    ROUND(
        COUNT(CASE WHEN a.status IN ('present', 'wfh') THEN 1 END)::NUMERIC /
        NULLIF(COUNT(CASE WHEN a.status IN ('present', 'wfh', 'absent', 'leave', 'half_day') THEN 1 END), 0) * 100,
        2
    ) AS attendance_percentage
FROM
    employees e
JOIN
    teams t ON e.team_id = t.id
LEFT JOIN
    attendance a ON e.id = a.employee_id 
        AND a.date BETWEEN date_trunc('month', CURRENT_DATE) AND CURRENT_DATE
WHERE
    EXTRACT(DOW FROM a.date) NOT IN (0, 6)
GROUP BY
    e.id, e.first_name, e.last_name, t.name
HAVING
    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) >= 2
    OR COUNT(CASE WHEN a.check_in::TIME > '09:30:00'::TIME AND a.status IN ('present', 'half_day') THEN 1 END) >= 3
    OR ROUND(
        COUNT(CASE WHEN a.status IN ('present', 'wfh') THEN 1 END)::NUMERIC /
        NULLIF(COUNT(CASE WHEN a.status IN ('present', 'wfh', 'absent', 'leave', 'half_day') THEN 1 END), 0) * 100,
        2
    ) < 80
ORDER BY
    attendance_percentage ASC; 