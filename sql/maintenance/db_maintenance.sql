-- Database Maintenance Script for Attendance Management System
-- Contains functions for data archiving, cleanup, and database optimization

-- Create archive tables with the same structure as the main tables
CREATE TABLE archived_attendance (
    LIKE attendance INCLUDING ALL
);

CREATE TABLE archived_team_trends (
    LIKE team_trends INCLUDING ALL
);

CREATE TABLE archived_ai_insights (
    LIKE ai_insights INCLUDING ALL
);

-- Function to archive attendance records older than a specified cutoff date
CREATE OR REPLACE FUNCTION archive_old_attendance(cutoff_date DATE) RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move attendance records older than cutoff_date to archive table
    INSERT INTO archived_attendance
    SELECT * FROM attendance
    WHERE date < cutoff_date;
    
    -- Get the count of archived records
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Delete the archived records from the main table
    DELETE FROM attendance
    WHERE date < cutoff_date;
    
    -- Return the number of archived records
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to archive team trends older than a specified cutoff date
CREATE OR REPLACE FUNCTION archive_old_team_trends(cutoff_date DATE) RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Move team_trends records older than cutoff_date to archive table
    INSERT INTO archived_team_trends
    SELECT * FROM team_trends
    WHERE date < cutoff_date;
    
    -- Get the count of archived records
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Delete the archived records from the main table
    DELETE FROM team_trends
    WHERE date < cutoff_date;
    
    -- Return the number of archived records
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to archive AI insights older than a specified cutoff date
CREATE OR REPLACE FUNCTION archive_old_ai_insights(days_to_keep INTEGER) RETURNS INTEGER AS $$
DECLARE
    cutoff_timestamp TIMESTAMP;
    archived_count INTEGER;
BEGIN
    -- Calculate the cutoff timestamp
    cutoff_timestamp := CURRENT_TIMESTAMP - (days_to_keep || ' days')::INTERVAL;
    
    -- Move ai_insights records older than cutoff_timestamp to archive table
    INSERT INTO archived_ai_insights
    SELECT * FROM ai_insights
    WHERE generated_at < cutoff_timestamp;
    
    -- Get the count of archived records
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Delete the archived records from the main table
    DELETE FROM ai_insights
    WHERE generated_at < cutoff_timestamp;
    
    -- Return the number of archived records
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old data (permanent deletion from archive tables)
CREATE OR REPLACE FUNCTION permanent_cleanup(retention_years INTEGER) RETURNS INTEGER AS $$
DECLARE
    cutoff_date DATE;
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Calculate the cutoff date based on retention years
    cutoff_date := CURRENT_DATE - (retention_years || ' years')::INTERVAL;
    
    -- Delete old records from archive tables
    DELETE FROM archived_attendance WHERE date < cutoff_date;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    DELETE FROM archived_team_trends WHERE date < cutoff_date;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    DELETE FROM archived_ai_insights WHERE generated_at < cutoff_date::TIMESTAMP;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Return the total number of permanently deleted records
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to run VACUUM and ANALYZE on important tables
CREATE OR REPLACE FUNCTION optimize_database() RETURNS VOID AS $$
BEGIN
    -- Vacuum and analyze attendance table
    EXECUTE 'VACUUM ANALYZE attendance';
    EXECUTE 'VACUUM ANALYZE teams';
    EXECUTE 'VACUUM ANALYZE employees';
    EXECUTE 'VACUUM ANALYZE team_trends';
    EXECUTE 'VACUUM ANALYZE ai_insights';
    
    -- Also vacuum archived tables if they contain data
    IF EXISTS (SELECT 1 FROM archived_attendance LIMIT 1) THEN
        EXECUTE 'VACUUM ANALYZE archived_attendance';
    END IF;
    
    IF EXISTS (SELECT 1 FROM archived_team_trends LIMIT 1) THEN
        EXECUTE 'VACUUM ANALYZE archived_team_trends';
    END IF;
    
    IF EXISTS (SELECT 1 FROM archived_ai_insights LIMIT 1) THEN
        EXECUTE 'VACUUM ANALYZE archived_ai_insights';
    END IF;
    
    -- Refresh the materialized view
    EXECUTE 'REFRESH MATERIALIZED VIEW monthly_attendance_summary';
END;
$$ LANGUAGE plpgsql;

-- Create a table to store database statistics for performance monitoring
CREATE TABLE database_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    table_name TEXT NOT NULL,
    row_count BIGINT,
    total_size_bytes BIGINT,
    index_size_bytes BIGINT,
    vacuum_count BIGINT,
    dead_tuples BIGINT,
    last_vacuum TIMESTAMP,
    last_analyze TIMESTAMP
);

-- Function to collect and store database statistics
CREATE OR REPLACE FUNCTION collect_database_stats() RETURNS INTEGER AS $$
DECLARE
    tables TEXT[] := ARRAY['teams', 'employees', 'attendance', 'team_trends', 'ai_insights', 
                          'archived_attendance', 'archived_team_trends', 'archived_ai_insights'];
    tbl TEXT;
    insert_count INTEGER := 0;
BEGIN
    -- For each table, collect statistics and insert into database_stats
    FOREACH tbl IN ARRAY tables
    LOOP
        BEGIN
            INSERT INTO database_stats (
                table_name,
                row_count,
                total_size_bytes,
                index_size_bytes,
                vacuum_count,
                dead_tuples,
                last_vacuum,
                last_analyze
            )
            SELECT
                tbl,
                (SELECT reltuples::BIGINT FROM pg_class WHERE relname = tbl),
                pg_total_relation_size(tbl),
                pg_indexes_size(tbl),
                (SELECT n_vacuum FROM pg_stat_user_tables WHERE relname = tbl),
                (SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = tbl),
                (SELECT last_vacuum FROM pg_stat_user_tables WHERE relname = tbl),
                (SELECT last_analyze FROM pg_stat_user_tables WHERE relname = tbl);
                
            insert_count := insert_count + 1;
        EXCEPTION
            WHEN OTHERS THEN
                -- Skip if table doesn't exist or other error
                NULL;
        END;
    END LOOP;
    
    -- Return the number of tables for which statistics were collected
    RETURN insert_count;
END;
$$ LANGUAGE plpgsql;

-- Function to detect potential performance issues
CREATE OR REPLACE FUNCTION check_performance_issues() RETURNS TABLE (
    issue_type TEXT,
    table_name TEXT,
    description TEXT,
    recommended_action TEXT
) AS $$
BEGIN
    -- Check for tables with high dead tuple counts
    RETURN QUERY
    SELECT 
        'High dead tuple count' AS issue_type,
        s.table_name,
        'Table has ' || s.dead_tuples || ' dead tuples, which is ' || 
        ROUND((s.dead_tuples::NUMERIC / NULLIF(s.row_count, 0)) * 100, 2) || '% of total rows' AS description,
        'Run VACUUM ANALYZE on this table' AS recommended_action
    FROM 
        database_stats s
    WHERE 
        s.timestamp = (SELECT MAX(timestamp) FROM database_stats)
        AND s.row_count > 0
        AND (s.dead_tuples::NUMERIC / NULLIF(s.row_count, 0)) > 0.1
    ORDER BY 
        (s.dead_tuples::NUMERIC / NULLIF(s.row_count, 0)) DESC;
    
    -- Check for tables that haven't been vacuumed in a long time
    RETURN QUERY
    SELECT 
        'Outdated statistics' AS issue_type,
        s.table_name,
        'Table was last analyzed on ' || s.last_analyze || ', which is ' || 
        EXTRACT(DAY FROM CURRENT_TIMESTAMP - s.last_analyze) || ' days ago' AS description,
        'Run ANALYZE on this table' AS recommended_action
    FROM 
        database_stats s
    WHERE 
        s.timestamp = (SELECT MAX(timestamp) FROM database_stats)
        AND s.last_analyze IS NOT NULL
        AND s.last_analyze < CURRENT_TIMESTAMP - INTERVAL '7 days'
        AND EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = s.table_name)
    ORDER BY 
        s.last_analyze ASC;
    
    -- Check for large tables
    RETURN QUERY
    SELECT 
        'Large table' AS issue_type,
        s.table_name,
        'Table size is ' || (s.total_size_bytes / 1024 / 1024) || ' MB with ' || s.row_count || ' rows' AS description,
        CASE 
            WHEN s.table_name LIKE 'archived_%' THEN 'Consider moving to cold storage or partitioning'
            ELSE 'Consider archiving old data or partitioning'
        END AS recommended_action
    FROM 
        database_stats s
    WHERE 
        s.timestamp = (SELECT MAX(timestamp) FROM database_stats)
        AND s.total_size_bytes > 100 * 1024 * 1024  -- 100 MB
    ORDER BY 
        s.total_size_bytes DESC;
END;
$$ LANGUAGE plpgsql;

-- Create monthly maintenance procedure
CREATE OR REPLACE PROCEDURE monthly_maintenance(
    attendance_months_to_keep INTEGER DEFAULT 6,
    team_trends_months_to_keep INTEGER DEFAULT 12,
    ai_insights_days_to_keep INTEGER DEFAULT 90,
    retention_years INTEGER DEFAULT 5
) AS $$
DECLARE
    attendance_cutoff DATE := CURRENT_DATE - (attendance_months_to_keep || ' months')::INTERVAL;
    team_trends_cutoff DATE := CURRENT_DATE - (team_trends_months_to_keep || ' months')::INTERVAL;
    archived_attendance_count INTEGER;
    archived_team_trends_count INTEGER;
    archived_ai_insights_count INTEGER;
    deleted_count INTEGER;
BEGIN
    -- Archive old records
    archived_attendance_count := archive_old_attendance(attendance_cutoff);
    archived_team_trends_count := archive_old_team_trends(team_trends_cutoff);
    archived_ai_insights_count := archive_old_ai_insights(ai_insights_days_to_keep);
    
    -- Permanent cleanup of very old archived data
    deleted_count := permanent_cleanup(retention_years);
    
    -- Optimize database
    PERFORM optimize_database();
    
    -- Collect statistics
    PERFORM collect_database_stats();
    
    -- Log maintenance activity
    RAISE NOTICE 'Monthly maintenance completed:';
    RAISE NOTICE 'Archived attendance records: %', archived_attendance_count;
    RAISE NOTICE 'Archived team trends records: %', archived_team_trends_count;
    RAISE NOTICE 'Archived AI insights records: %', archived_ai_insights_count;
    RAISE NOTICE 'Permanently deleted archive records: %', deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create a table for logging maintenance runs
CREATE TABLE maintenance_log (
    id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    maintenance_type TEXT NOT NULL,
    records_processed INTEGER,
    duration_ms INTEGER,
    details JSONB
);

-- Add a function to run and log the maintenance
CREATE OR REPLACE FUNCTION run_and_log_maintenance(maintenance_type TEXT) RETURNS VOID AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    duration INTEGER;
    records_processed INTEGER := 0;
    details JSONB := '{}'::JSONB;
BEGIN
    start_time := clock_timestamp();
    
    IF maintenance_type = 'monthly' THEN
        CALL monthly_maintenance();
        -- We don't have a direct count here, so we'll estimate from the latest stats
        SELECT SUM(row_count)::INTEGER INTO records_processed 
        FROM database_stats 
        WHERE timestamp = (SELECT MAX(timestamp) FROM database_stats);
        
    ELSIF maintenance_type = 'archive_attendance' THEN
        SELECT archive_old_attendance(CURRENT_DATE - INTERVAL '6 months') INTO records_processed;
        details := jsonb_build_object('cutoff_date', CURRENT_DATE - INTERVAL '6 months');
        
    ELSIF maintenance_type = 'archive_team_trends' THEN
        SELECT archive_old_team_trends(CURRENT_DATE - INTERVAL '12 months') INTO records_processed;
        details := jsonb_build_object('cutoff_date', CURRENT_DATE - INTERVAL '12 months');
        
    ELSIF maintenance_type = 'archive_ai_insights' THEN
        SELECT archive_old_ai_insights(90) INTO records_processed;
        details := jsonb_build_object('days_kept', 90);
        
    ELSIF maintenance_type = 'optimize' THEN
        PERFORM optimize_database();
        details := jsonb_build_object('tables_processed', 
                   (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'));
        
    ELSIF maintenance_type = 'collect_stats' THEN
        SELECT collect_database_stats() INTO records_processed;
        details := jsonb_build_object('tables_analyzed', records_processed);
        
    ELSE
        RAISE EXCEPTION 'Unknown maintenance type: %', maintenance_type;
    END IF;
    
    end_time := clock_timestamp();
    duration := EXTRACT(EPOCH FROM (end_time - start_time)) * 1000;
    
    -- Log the maintenance run
    INSERT INTO maintenance_log (maintenance_type, records_processed, duration_ms, details)
    VALUES (maintenance_type, records_processed, duration, details);
END;
$$ LANGUAGE plpgsql;

-- Add samples for testing the maintenance procedures
COMMENT ON FUNCTION run_and_log_maintenance(TEXT) IS 'Run with one of these types: monthly, archive_attendance, archive_team_trends, archive_ai_insights, optimize, collect_stats';

-- Example usage:
-- SELECT run_and_log_maintenance('collect_stats');
-- SELECT run_and_log_maintenance('optimize');
-- SELECT run_and_log_maintenance('monthly');

-- Create views for maintenance reporting
CREATE VIEW maintenance_summary AS
SELECT 
    maintenance_type,
    COUNT(*) AS run_count,
    MAX(run_timestamp) AS last_run,
    MIN(run_timestamp) AS first_run,
    AVG(duration_ms) AS avg_duration_ms,
    SUM(records_processed) AS total_records_processed
FROM 
    maintenance_log
GROUP BY 
    maintenance_type
ORDER BY 
    last_run DESC;

-- Create function to get recommendations for next maintenance tasks
CREATE OR REPLACE FUNCTION get_maintenance_recommendations() RETURNS TABLE (
    recommended_maintenance TEXT,
    priority TEXT,
    reason TEXT,
    last_run TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    
    -- Check for monthly maintenance
    SELECT 
        'monthly' AS recommended_maintenance,
        CASE 
            WHEN MAX(run_timestamp) IS NULL OR MAX(run_timestamp) < CURRENT_TIMESTAMP - INTERVAL '30 days' 
            THEN 'High'
            ELSE 'Low'
        END AS priority,
        CASE 
            WHEN MAX(run_timestamp) IS NULL THEN 'Never run'
            ELSE 'Last run ' || EXTRACT(DAY FROM CURRENT_TIMESTAMP - MAX(run_timestamp)) || ' days ago'
        END AS reason,
        MAX(run_timestamp) AS last_run
    FROM 
        maintenance_log
    WHERE 
        maintenance_type = 'monthly'
    
    UNION ALL
    
    -- Check for optimize
    SELECT 
        'optimize' AS recommended_maintenance,
        CASE 
            WHEN MAX(run_timestamp) IS NULL OR MAX(run_timestamp) < CURRENT_TIMESTAMP - INTERVAL '7 days' 
            THEN 'Medium'
            ELSE 'Low'
        END AS priority,
        CASE 
            WHEN MAX(run_timestamp) IS NULL THEN 'Never run'
            ELSE 'Last run ' || EXTRACT(DAY FROM CURRENT_TIMESTAMP - MAX(run_timestamp)) || ' days ago'
        END AS reason,
        MAX(run_timestamp) AS last_run
    FROM 
        maintenance_log
    WHERE 
        maintenance_type = 'optimize'
    
    UNION ALL
    
    -- Check for collect_stats
    SELECT 
        'collect_stats' AS recommended_maintenance,
        CASE 
            WHEN MAX(run_timestamp) IS NULL OR MAX(run_timestamp) < CURRENT_TIMESTAMP - INTERVAL '1 day' 
            THEN 'Medium'
            ELSE 'Low'
        END AS priority,
        CASE 
            WHEN MAX(run_timestamp) IS NULL THEN 'Never run'
            ELSE 'Last run ' || EXTRACT(DAY FROM CURRENT_TIMESTAMP - MAX(run_timestamp)) || ' days ago'
        END AS reason,
        MAX(run_timestamp) AS last_run
    FROM 
        maintenance_log
    WHERE 
        maintenance_type = 'collect_stats'
    
    ORDER BY 
        CASE priority
            WHEN 'High' THEN 1
            WHEN 'Medium' THEN 2
            ELSE 3
        END,
        last_run ASC NULLS FIRST;
END;
$$ LANGUAGE plpgsql; 