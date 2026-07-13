from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, date
import os
import re
import logging
from openai import AzureOpenAI
from typing import Dict, Any, List, Tuple, Optional
from . import crud, models, schemas

"""
AI Service for Attendance Management System

This module provides AI-powered analytics and insights for attendance data using Azure OpenAI.
It supports two approaches for generating insights:

1. SQL-based Approach (Default):
   - Converts natural language queries to SQL using Azure OpenAI
   - Executes the SQL against the database
   - Analyzes the results to provide insights
   - Falls back to pattern-based approach if SQL generation fails

2. Pattern-based Approach (Fallback):
   - Uses predefined patterns to process specific query types (absent, WFH, leave)
   - Retrieves relevant data based on query type
   - Generates insights using predefined templates

Both approaches save insights to the database for future reference.
"""

logger = logging.getLogger(__name__)

# Hard limits for LLM-generated SQL execution
AI_SQL_MAX_ROWS = int(os.getenv("AI_SQL_MAX_ROWS", "200"))
AI_SQL_STATEMENT_TIMEOUT_MS = int(os.getenv("AI_SQL_STATEMENT_TIMEOUT_MS", "5000"))
_FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|"
    r"COPY|EXECUTE|CALL|MERGE|REPLACE|ATTACH|DETACH|VACUUM|ANALYZE|"
    r"COMMENT|SECURITY|OWNER|SET\s+ROLE|SET\s+SESSION|pg_sleep|"
    r"lo_import|lo_export|dblink|INTO\s+OUTFILE)\b",
    re.IGNORECASE,
)
_ALLOWED_TABLES = {
    "teams",
    "employees",
    "attendance",
    "team_trends",
    "ai_insights",
    "daily_attendance_summary",
    "team_attendance_trends",
}

class AIService:
    # SQL generation prompt template
    SQL_PROMPT_TEMPLATE = """
    You are a SQL query generator for an attendance management system. Convert the following natural language query to a PostgreSQL SQL query.
    
    Database schema:
    - teams: id, name, created_at, updated_at
    - employees: id, first_name, last_name, email, phone, role (enum: 'employee', 'manager', 'admin'), team_id, hire_date, created_at, updated_at
    - attendance: id, employee_id, date, status (enum: 'present', 'absent', 'half_day', 'wfh', 'leave'), check_in, check_out, notes, created_at, updated_at
    - team_trends: id, team_id, date, total_employees, present_count, absent_count, wfh_count, half_day_count, leave_count
    - ai_insights: id, query, summary, details, generated_at
    
    Views:
    - daily_attendance_summary: Shows daily attendance metrics grouped by team (date, team_id, team_name, present_count, absent_count, wfh_count, half_day_count, leave_count, total_employees)
    - team_attendance_trends: Shows attendance trends by team over the last 30 days (team_id, team_name, date, present_count, absent_count, wfh_count, half_day_count, leave_count, total_employees)
    
    Relationships:
    - employees.team_id references teams.id
    - attendance.employee_id references employees.id
    - team_trends.team_id references teams.id
    
    IMPORTANT ENUM HANDLING:
    - When referencing enum values in WHERE clauses, use the following format:
      WHERE status::text = 'absent'   # correct
      WHERE status = 'absent'         # may cause issues
    
    - Status enum values (all lowercase): 'present', 'absent', 'half_day', 'wfh', 'leave'
    - Role enum values (all lowercase): 'employee', 'manager', 'admin'
    
    Sample queries:
    1. For "Who has the most absences this month?":
    SELECT e.first_name, e.last_name, COUNT(*) as absence_count
    FROM employees e
    JOIN attendance a ON e.id = a.employee_id
    WHERE a.status::text = 'absent' AND a.date >= DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY e.id, e.first_name, e.last_name
    ORDER BY absence_count DESC
    LIMIT 5;
    
    2. For "Compare attendance rates between teams":
    SELECT t.name as team_name, 
        COUNT(CASE WHEN a.status::text = 'present' THEN 1 END) as present_count,
        COUNT(*) as total_records,
        ROUND(COUNT(CASE WHEN a.status::text = 'present' THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100, 2) as present_percentage
    FROM teams t
    JOIN employees e ON t.id = e.team_id
    JOIN attendance a ON e.id = a.employee_id
    WHERE a.date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY t.id, t.name
    ORDER BY present_percentage DESC;
    
    IMPORTANT SAFETY RULES:
    - Generate ONLY a single SELECT (or WITH ... SELECT) query
    - Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, or any write/DDL statement
    - Always include a LIMIT clause (maximum 200 rows)
    - Only query these relations: teams, employees, attendance, team_trends, ai_insights,
      daily_attendance_summary, team_attendance_trends
    
    User query: {query}
    
    IMPORTANT: Return ONLY the raw SQL query without any markdown formatting, explanation, or code blocks. Do not use ``` or any other markdown. Return just the SQL query itself.
    """
    
    # SQL fix prompt template
    SQL_FIX_PROMPT_TEMPLATE = """
    There was an error executing this SQL query:
    {sql}
    
    Error: {error}
    
    Common issues to check:
    1. Enum handling: Use status::text = 'value' instead of status = 'value'
    2. Add proper GROUP BY clauses for all non-aggregated columns in SELECT
    3. Use NULLIF() to avoid division by zero
    4. Cast numeric values properly
    5. Ensure date formats are correct
    6. Query must remain a single read-only SELECT with LIMIT <= 200
    
    Please fix the query. IMPORTANT: Return ONLY the raw SQL query without any markdown formatting, explanation, or code blocks. Do not use ``` or any other markdown tags.
    """
    
    # Analysis prompt template
    ANALYSIS_PROMPT_TEMPLATE = """
    Based on the following data, provide insights and analysis.
    
    User query: {query}
    
    SQL query used:
    {sql}
    
    Query results:
    {data}
    
    Analyze the data and provide valuable insights related to:
    1. Key patterns, trends, or anomalies in the data
    2. Notable employee or team behaviors
    3. Attendance patterns (if relevant)
    4. Any actionable recommendations
    
    Format your response as a concise, professional analysis of 3-4 sentences that directly answers the user's query.
    """
    
    def __init__(self):
        """Initialize the Azure OpenAI client."""
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            logger.info("Azure OpenAI client initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI client: {str(e)}")
            self.client = None

    async def generate_insights(self, query: str, db: Session) -> schemas.AIInsight:
        """Generate AI-powered insights from attendance data based on a natural language query.
        
        This method uses a two-tiered approach:
        1. First attempts to convert the query to SQL and analyze the results (preferred)
        2. Falls back to pattern-based analysis if SQL approach fails
        
        Args:
            query: Natural language query about attendance data
            db: Database session
            
        Returns:
            AIInsight object containing the query, summary, and details
        """
        if not self.client:
            return self._create_error_insight(
                query, 
                "AI insights are currently unavailable. Please try again later.",
                {"error": "Azure OpenAI client not initialized"}
            )
            
        try:
            # First try using the SQL-based approach
            try:
                logger.info(f"Attempting SQL-based analysis for query: {query}")
                sql_insight = await self.analyze_custom_query(query, db)
                if sql_insight and "error" not in sql_insight.details:
                    logger.info("SQL-based analysis successful")
                    if isinstance(sql_insight, schemas.AIInsight) and sql_insight.id:
                        return sql_insight
                    create_payload = (
                        sql_insight
                        if isinstance(sql_insight, schemas.AIInsightCreate)
                        else schemas.AIInsightCreate(
                            query=sql_insight.query,
                            summary=sql_insight.summary,
                            details=sql_insight.details,
                            generated_at=sql_insight.generated_at,
                        )
                    )
                    return self._save_insight(db, create_payload) or schemas.AIInsight(
                        id=0,
                        query=create_payload.query,
                        summary=create_payload.summary,
                        details=create_payload.details,
                        generated_at=create_payload.generated_at,
                    )
                logger.info("SQL-based analysis unsuccessful, falling back to standard approach")
            except Exception as sql_error:
                logger.warning(f"SQL-based analysis failed, falling back to standard approach: {str(sql_error)}")
            
            # Fall back to pattern-based approach
            return await self._generate_pattern_based_insight(query, db)
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return self._create_error_insight(
                query,
                "An error occurred while generating insights. Please try again later.",
                {"error": str(e)}
            )

    async def _generate_pattern_based_insight(self, query: str, db: Session) -> schemas.AIInsight:
        """Generate insights using pattern-based approach as fallback.
        
        Args:
            query: User query string
            db: Database session
            
        Returns:
            AIInsight object with pattern-based analysis
        """
        # Get relevant data based on the query keywords
        data_type, start_date = self._determine_data_type_and_timeframe(query)
        attendance_data = self._get_attendance_data(db, start_date)
        
        # Process data and create prompt based on data type
        details, prompt = self._process_data_by_type(data_type, attendance_data)
        
        # Generate response using OpenAI
        response = self._call_openai(
            system_content="You are an AI assistant that provides insights about employee attendance data.",
            user_content=prompt
        )
        
        # Create and save insight
        insight = schemas.AIInsightCreate(
            query=query,
            summary=response,
            details=details
        )
        
        return self._save_insight(db, insight) or schemas.AIInsight(
            id=0, query=insight.query, summary=insight.summary, details=insight.details,
            generated_at=insight.generated_at
        )

    def _determine_data_type_and_timeframe(self, query: str) -> Tuple[str, date]:
        """Determine data type and timeframe based on query keywords.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (data_type, start_date)
        """
        query_lower = query.lower()
        
        if "absent" in query_lower:
            return "absent", date.today() - timedelta(days=30)
        elif "wfh" in query_lower:
            return "wfh", date.today() - timedelta(days=7)
        elif "leave" in query_lower:
            return "leave", date.today() - timedelta(days=30)
        else:
            return "general", date.today() - timedelta(days=7)

    def _process_data_by_type(self, data_type: str, attendance_data: List) -> Tuple[Dict, str]:
        """Process attendance data based on data type and create appropriate prompt.
        
        Args:
            data_type: Type of data to process ('absent', 'wfh', 'leave', or 'general')
            attendance_data: List of attendance records
            
        Returns:
            Tuple of (details_dict, prompt_string)
        """
        if data_type == "absent":
            details = self._process_absent_data(attendance_data)
            prompt = self._create_absent_analysis_prompt(attendance_data)
        elif data_type == "wfh":
            details = self._process_wfh_data(attendance_data)
            prompt = self._create_wfh_analysis_prompt(attendance_data)
        elif data_type == "leave":
            details = self._process_leave_data(attendance_data)
            prompt = self._create_leave_analysis_prompt(attendance_data)
        else:  # general
            details = self._process_general_data(attendance_data)
            prompt = self._create_general_summary_prompt(attendance_data)
            
        return details, prompt

    async def analyze_custom_query(self, query: str, db: Session):
        """Process a natural language query, generate SQL, and provide insights.
        
        Args:
            query: User's natural language query about attendance data
            db: Database session
            
        Returns:
            AIInsightCreate on success, AIInsight (with id=0) on error
        """
        if not self.client:
            return self._create_error_insight(
                query, 
                "AI insights are currently unavailable. Please try again later.",
                {"error": "Azure OpenAI client not initialized"}
            )
        
        try:
            # Generate and execute SQL query
            generated_sql = self._generate_sql_query(query)
            clean_sql = self._clean_sql_query(generated_sql)
            
            try:
                # Try executing the SQL query
                data, column_names = self._execute_sql_query(db, clean_sql)
                
                # Generate insights from the results
                summary = self._analyze_sql_results(query, clean_sql, data)
                
                # Create and return insight
                return self._create_sql_insight(query, summary, clean_sql, data)
                
            except Exception as sql_error:
                # Attempt to fix the SQL query if execution failed
                logger.error(f"Error executing SQL: {str(sql_error)}")
                return await self._handle_sql_error(db, query, clean_sql, str(sql_error))
                
        except Exception as e:
            logger.error(f"Error in analyze_custom_query: {str(e)}")
            return self._create_error_insight(
                query,
                "An error occurred while analyzing your query. Please try again later.",
                {"error": str(e)}
            )

    def _generate_sql_query(self, query: str) -> str:
        """Generate a SQL query from a natural language query using Azure OpenAI.
        
        Args:
            query: Natural language query
            
        Returns:
            Generated SQL query string
        """
        sql_prompt = self.SQL_PROMPT_TEMPLATE.format(query=query)
        
        response = self._call_openai(
            system_content=(
                "You are a SQL expert that generates only safe, read-only PostgreSQL SELECT queries. "
                "Never generate write or DDL statements. Always include LIMIT."
            ),
            user_content=sql_prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        logger.info(f"Generated SQL: {response}")
        return response

    def _validate_readonly_sql(self, sql: str) -> str:
        """Validate LLM-generated SQL is a single safe SELECT and enforce LIMIT."""
        cleaned = sql.strip().rstrip(";")
        if not cleaned:
            raise ValueError("Generated SQL is empty")

        # Reject multiple statements
        if ";" in cleaned:
            raise ValueError("Multiple SQL statements are not allowed")

        normalized = re.sub(r"\s+", " ", cleaned).strip()
        upper = normalized.upper()

        if not (upper.startswith("SELECT") or upper.startswith("WITH")):
            raise ValueError("Only SELECT queries are allowed")

        if _FORBIDDEN_SQL_PATTERN.search(cleaned):
            raise ValueError("SQL contains forbidden keywords or operations")

        # Block selecting from clearly disallowed relations when FROM/JOIN is present
        relation_refs = re.findall(
            r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            cleaned,
            flags=re.IGNORECASE,
        )
        for relation in relation_refs:
            if relation.lower() not in _ALLOWED_TABLES:
                raise ValueError(f"Query references disallowed relation: {relation}")

        if not re.search(r"\bLIMIT\s+\d+", cleaned, flags=re.IGNORECASE):
            cleaned = f"{cleaned}\nLIMIT {AI_SQL_MAX_ROWS}"
        else:
            limit_match = re.search(r"\bLIMIT\s+(\d+)", cleaned, flags=re.IGNORECASE)
            if limit_match and int(limit_match.group(1)) > AI_SQL_MAX_ROWS:
                cleaned = re.sub(
                    r"\bLIMIT\s+\d+",
                    f"LIMIT {AI_SQL_MAX_ROWS}",
                    cleaned,
                    flags=re.IGNORECASE,
                )

        return cleaned

    def _execute_sql_query(self, db: Session, sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute a validated read-only SQL query with timeout and row cap."""
        safe_sql = self._validate_readonly_sql(sql)
        logger.info(f"Executing SQL: {safe_sql}")

        db.execute(text(f"SET LOCAL statement_timeout = {AI_SQL_STATEMENT_TIMEOUT_MS}"))
        result = db.execute(text(safe_sql))
        raw_data = result.fetchmany(AI_SQL_MAX_ROWS)
        column_names = list(result.keys())

        row_count = len(raw_data)
        logger.info(f"SQL execution successful. Retrieved {row_count} rows.")
        if row_count == 0:
            logger.warning("Query returned 0 rows, but executed successfully.")

        data = [dict(zip(column_names, row)) for row in raw_data]
        return data, column_names

    def _analyze_sql_results(self, query: str, sql: str, data: List[Dict[str, Any]]) -> str:
        """Analyze SQL query results and generate insights.
        
        Args:
            query: Original natural language query
            sql: Executed SQL query
            data: Query results
            
        Returns:
            Summary insights string
        """
        analysis_prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            query=query,
            sql=sql,
            data=data
        )
        
        return self._call_openai(
            system_content="You are an attendance data analyst that provides clear, concise insights.",
            user_content=analysis_prompt
        )

    async def _handle_sql_error(self, db: Session, query: str, sql: str, error: str):
        """Handle SQL execution errors by attempting to fix the query.
        
        Args:
            db: Database session
            query: Original natural language query
            sql: SQL query that caused an error
            error: Error message
            
        Returns:
            AIInsightCreate on success, AIInsight on error
        """
        # Try to fix the SQL query
        fix_prompt = self.SQL_FIX_PROMPT_TEMPLATE.format(sql=sql, error=error)
        
        fixed_sql = self._call_openai(
            system_content="You are a SQL expert that fixes PostgreSQL queries. Ensure your queries are safe and follow best practices.",
            user_content=fix_prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        logger.info(f"Fixed SQL: {fixed_sql}")
        
        clean_fixed_sql = self._clean_sql_query(fixed_sql)
        logger.info(f"Cleaned fixed SQL: {clean_fixed_sql}")
        
        try:
            # Try executing the fixed SQL
            data, _ = self._execute_sql_query(db, clean_fixed_sql)
            
            # Generate insights from the fixed query results
            analysis_prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
                query=query,
                sql=f"Original: {sql}\nFixed: {clean_fixed_sql}",
                data=data
            )
            
            summary = self._call_openai(
                system_content="You are an attendance data analyst that provides clear, concise insights.",
                user_content=analysis_prompt
            )
            
            # Create and return insight with fixed SQL
            return schemas.AIInsightCreate(
                query=query,
                summary=summary,
                details={
                    "generated_sql": sql,
                    "fixed_sql": clean_fixed_sql,
                    "data": data
                }
            )
            
        except Exception as e2:
            logger.error(f"Error executing fixed SQL: {str(e2)}")
            return self._create_error_insight(
                query,
                "Unable to analyze this query. Please try rephrasing or ask a different question.",
                {
                    "error": f"Original error: {error}, Fix attempt error: {str(e2)}",
                    "generated_sql": sql,
                    "fixed_sql": clean_fixed_sql
                }
            )

    def _call_openai(self, system_content: str, user_content: str, 
                    temperature: float = 0.7, max_tokens: int = None) -> str:
        """Call Azure OpenAI API with the given content.
        
        Args:
            system_content: System message content
            user_content: User message content
            temperature: Temperature parameter for OpenAI
            max_tokens: Maximum tokens parameter for OpenAI
            
        Returns:
            Response content string
        """
        params = {
            "model": os.getenv("AZURE_OPENAI_MODEL"),
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            "temperature": temperature
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
            
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content.strip()

    def _create_sql_insight(self, query: str, summary: str, sql: str, 
                          data: List[Dict[str, Any]]) -> schemas.AIInsightCreate:
        """Create an AIInsightCreate object from SQL query results.
        
        Args:
            query: Original natural language query
            summary: Summary insights
            sql: Executed SQL query
            data: Query results
            
        Returns:
            AIInsightCreate object
        """
        return schemas.AIInsightCreate(
            query=query,
            summary=summary,
            details={
                "generated_sql": sql,
                "data": data
            }
        )

    def _create_error_insight(self, query: str, summary: str, error_details: Dict[str, Any]) -> schemas.AIInsight:
        """Create an AIInsight object for error cases.
        
        Args:
            query: Original natural language query
            summary: Error summary message
            error_details: Detailed error information
            
        Returns:
            AIInsight object with error details
        """
        return schemas.AIInsight(
            id=0,
            query=query,
            summary=summary,
            details=error_details
        )

    def _save_insight(self, db: Session, insight: schemas.AIInsightCreate) -> Optional[schemas.AIInsight]:
        """Save an insight to the database, logging errors but not raising exceptions.
        
        Args:
            db: Database session
            insight: AIInsightCreate object to save

        Returns:
            Saved AIInsight with id, or None if save failed
        """
        try:
            saved = crud.save_ai_insight(db, insight)
            return schemas.AIInsight.model_validate(saved)
        except Exception as e:
            logger.warning(f"Failed to save insight to database: {str(e)}")
            return None

    def _get_attendance_data(self, db: Session, start_date: date) -> List:
        """Get attendance records from the database starting from a given date.
        
        Args:
            db: Database session
            start_date: Start date for attendance records
            
        Returns:
            List of attendance records
        """
        return db.query(models.Attendance).filter(
            models.Attendance.date >= start_date
        ).all()

    def _get_employee_name(self, employee) -> str:
        """Get the full name of an employee.
        
        Args:
            employee: Employee model object
            
        Returns:
            Employee's full name
        """
        return f"{employee.first_name} {employee.last_name}"

    def _clean_sql_query(self, query_text: str) -> str:
        """Clean a SQL query by removing markdown formatting and handling enum comparisons.
        
        Args:
            query_text: Raw SQL query text
            
        Returns:
            Cleaned SQL query
        """
        # Start with the original query
        clean_query = query_text.strip()
        
        # Remove markdown code block markers
        if clean_query.startswith('```'):
            # Extract content between code blocks
            lines = clean_query.split('\n')
            
            # Check if the first line contains a language specifier like ```sql
            start_idx = 1  # Default to skipping just the opening ```
            if len(lines) > 1 and lines[0].startswith('```') and len(lines[0]) > 3:
                # This is like ```sql or ```postgresql
                start_idx = 1
                
            # Get all lines except the start marker(s) 
            lines = lines[start_idx:]
            
            # Remove the closing code block if present
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            
            clean_query = '\n'.join(lines)
        
        # Remove any "sql" or "postgresql" language marker that might be at the start
        language_prefixes = ['sql', 'postgresql']
        for prefix in language_prefixes:
            if clean_query.lower().startswith(prefix):
                # Remove the prefix and any whitespace after it
                clean_query = clean_query[len(prefix):].lstrip()
        
        # Trim any additional whitespace
        clean_query = clean_query.strip()
        
        # Replace single quotes in strings that might cause issues
        clean_query = clean_query.replace("''", "'")
        
        # Handle common enum comparison patterns to ensure proper casting
        # This is a basic implementation - in a production system, you would use a proper SQL parser
        enum_replacements = {
            "status = 'absent'": "status::text = 'absent'",
            "status = 'present'": "status::text = 'present'",
            "status = 'half_day'": "status::text = 'half_day'",
            "status = 'wfh'": "status::text = 'wfh'",
            "status = 'leave'": "status::text = 'leave'",
            "role = 'manager'": "role::text = 'manager'",
            "role = 'employee'": "role::text = 'employee'",
            "role = 'admin'": "role::text = 'admin'"
        }
        
        for original, replacement in enum_replacements.items():
            clean_query = clean_query.replace(original, replacement)
        
        return clean_query

    # Data processing methods for pattern-based approach
    def _process_absent_data(self, attendance_data) -> Dict[str, Any]:
        """Process attendance data to extract absence information."""
        employee_absences = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.absent:
                employee_name = self._get_employee_name(record.employee)
                employee_absences[employee_name] = employee_absences.get(employee_name, 0) + 1
        
        return {
            "employee_absences": employee_absences,
            "total_absences": sum(employee_absences.values()),
            "most_absent_employee": max(employee_absences.items(), key=lambda x: x[1])[0] if employee_absences else None
        }
    
    def _process_wfh_data(self, attendance_data) -> Dict[str, Any]:
        """Process attendance data to extract WFH information."""
        wfh_count = sum(1 for record in attendance_data if record.status == models.AttendanceType.wfh)
        total_days = len(attendance_data)
        
        employee_wfh = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.wfh:
                employee_name = self._get_employee_name(record.employee)
                employee_wfh[employee_name] = employee_wfh.get(employee_name, 0) + 1
        
        return {
            "wfh_count": wfh_count,
            "total_days": total_days,
            "wfh_percentage": (wfh_count / total_days * 100) if total_days > 0 else 0,
            "employee_wfh": employee_wfh
        }
    
    def _process_leave_data(self, attendance_data) -> Dict[str, Any]:
        """Process attendance data to extract leave information."""
        leave_count = sum(1 for record in attendance_data if record.status == models.AttendanceType.leave)
        total_days = len(attendance_data)
        
        employee_leave = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.leave:
                employee_name = self._get_employee_name(record.employee)
                employee_leave[employee_name] = employee_leave.get(employee_name, 0) + 1
        
        return {
            "leave_count": leave_count,
            "total_days": total_days,
            "leave_percentage": (leave_count / total_days * 100) if total_days > 0 else 0,
            "employee_leave": employee_leave,
            "most_leave_employee": max(employee_leave.items(), key=lambda x: x[1])[0] if employee_leave else None
        }
    
    def _process_general_data(self, attendance_data) -> Dict[str, Any]:
        """Process attendance data to extract general patterns."""
        status_counts = {
            models.AttendanceType.present: 0,
            models.AttendanceType.absent: 0,
            models.AttendanceType.wfh: 0,
            models.AttendanceType.half_day: 0,
            models.AttendanceType.leave: 0
        }
        
        for record in attendance_data:
            if record.status in status_counts:
                status_counts[record.status] += 1
        
        return {
            "status_counts": {status.value: count for status, count in status_counts.items()},
            "total_records": len(attendance_data)
        }

    # Prompt creation methods for pattern-based approach
    def _create_absent_analysis_prompt(self, attendance_data) -> str:
        """Create a prompt for analyzing absence patterns."""
        details = self._process_absent_data(attendance_data)
        
        prompt = "Based on the following attendance data, analyze who was absent the most:\n\n"
        for employee, count in details["employee_absences"].items():
            prompt += f"{employee}: {count} days absent\n"
        
        prompt += f"\nTotal absences: {details['total_absences']}"
        prompt += "\nPlease provide a natural language summary of the absenteeism patterns."
        return prompt
    
    def _create_wfh_analysis_prompt(self, attendance_data) -> str:
        """Create a prompt for analyzing WFH patterns."""
        details = self._process_wfh_data(attendance_data)
        
        prompt = f"Based on the attendance data for the past week:\n"
        prompt += f"Total WFH days: {details['wfh_count']}\n"
        prompt += f"Total attendance records: {details['total_days']}\n"
        prompt += f"WFH percentage: {details['wfh_percentage']:.1f}%\n\n"
        
        prompt += "WFH days by employee:\n"
        for employee, count in details["employee_wfh"].items():
            prompt += f"{employee}: {count} days\n"
            
        prompt += "\nPlease provide a natural language summary of the WFH patterns."
        return prompt
    
    def _create_leave_analysis_prompt(self, attendance_data) -> str:
        """Create a prompt for analyzing leave patterns."""
        details = self._process_leave_data(attendance_data)
        
        prompt = f"Based on the attendance data for the past month:\n"
        prompt += f"Total leave days: {details['leave_count']}\n"
        prompt += f"Total attendance records: {details['total_days']}\n"
        prompt += f"Leave percentage: {details['leave_percentage']:.1f}%\n\n"
        
        prompt += "Leave days by employee:\n"
        for employee, count in details["employee_leave"].items():
            prompt += f"{employee}: {count} days\n"
            
        prompt += "\nPlease provide a natural language summary of the leave patterns."
        return prompt
    
    def _create_general_summary_prompt(self, attendance_data) -> str:
        """Create a prompt for general attendance summary."""
        details = self._process_general_data(attendance_data)
        
        prompt = "Based on the attendance data for the past week:\n\n"
        for status, count in details["status_counts"].items():
            prompt += f"{status}: {count} days\n"
        
        prompt += f"\nTotal records: {details['total_records']}"
        prompt += "\nPlease provide a natural language summary of the attendance patterns."
        return prompt 