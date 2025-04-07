from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta, date
import os
import logging
from openai import AzureOpenAI
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

class AIService:
    def __init__(self):
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
        
        This method now uses a two-tiered approach:
        1. First attempts to convert the query to SQL and analyze the results (preferred)
        2. Falls back to pattern-based analysis if SQL approach fails
        
        Args:
            query: Natural language query about attendance data
            db: Database session
            
        Returns:
            AIInsight object containing the query, summary, and details
        """
        if not self.client:
            logger.error("Azure OpenAI client not initialized.")
            return schemas.AIInsight(
                query=query,
                summary="AI insights are currently unavailable. Please try again later.",
                details={"error": "Azure OpenAI client not initialized"}
            )
            
        try:
            # First try using the SQL-based approach
            try:
                logger.info(f"Attempting SQL-based analysis for query: {query}")
                sql_insight = await self.analyze_custom_query(query, db)
                if sql_insight and "error" not in sql_insight.details:
                    logger.info("SQL-based analysis successful")
                    # Save the insight to the database
                    try:
                        crud.save_ai_insight(db, sql_insight)
                    except Exception as e:
                        logger.warning(f"Failed to save insight to database: {str(e)}")
                    return sql_insight
                logger.info("SQL-based analysis unsuccessful, falling back to standard approach")
            except Exception as sql_error:
                if "should be explicitly declared as text" in str(sql_error):
                    logger.warning("SQLAlchemy text expression error. This is already being handled in analyze_custom_query.")
                else:
                    logger.warning(f"SQL-based analysis failed, falling back to standard approach: {str(sql_error)}")
            
            # Fall back to the existing approach if SQL analysis failed
            if "absent" in query.lower():
                # Get attendance data for the last 30 days
                start_date = date.today() - timedelta(days=30)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_absent_analysis_prompt(attendance_data)
                details = self._process_absent_data(attendance_data)
            elif "wfh" in query.lower():
                # Get WFH data for the last week
                start_date = date.today() - timedelta(days=7)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_wfh_analysis_prompt(attendance_data)
                details = self._process_wfh_data(attendance_data)
            elif "leave" in query.lower():
                # Get leave data for the last month
                start_date = date.today() - timedelta(days=30)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_leave_analysis_prompt(attendance_data)
                details = self._process_leave_data(attendance_data)
            else:
                # Default to general attendance summary
                start_date = date.today() - timedelta(days=7)
                attendance_data = self._get_attendance_data(db, start_date)
                prompt = self._create_general_summary_prompt(attendance_data)
                details = self._process_general_data(attendance_data)
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_MODEL"),
                messages=[
                    {"role": "system", "content": "You are an AI assistant that provides insights about employee attendance data."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            insight = schemas.AIInsight(
                query=query,
                summary=response.choices[0].message.content.strip(),
                details=details
            )
            
            # Save the insight to the database
            try:
                crud.save_ai_insight(db, insight)
            except Exception as e:
                logger.warning(f"Failed to save insight to database: {str(e)}")
            
            return insight
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return schemas.AIInsight(
                query=query,
                summary="An error occurred while generating insights. Please try again later.",
                details={"error": str(e)}
            )
    
    def _get_attendance_data(self, db: Session, start_date: date):
        return db.query(models.Attendance).filter(
            models.Attendance.date >= start_date
        ).all()
    
    def _get_employee_name(self, employee):
        """Get the full name of an employee"""
        return f"{employee.first_name} {employee.last_name}"
    
    def _clean_sql_query(self, query_text):
        """Clean a SQL query by removing markdown formatting and other artifacts.
        
        Args:
            query_text: The SQL query text that may contain markdown formatting
            
        Returns:
            Clean SQL query ready for execution
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
        clean_query = clean_query.replace(
            "status = 'absent'", "status::text = 'absent'"
        ).replace(
            "status = 'present'", "status::text = 'present'"
        ).replace(
            "status = 'half_day'", "status::text = 'half_day'"
        ).replace(
            "status = 'wfh'", "status::text = 'wfh'"
        ).replace(
            "status = 'leave'", "status::text = 'leave'"
        ).replace(
            "role = 'manager'", "role::text = 'manager'"
        ).replace(
            "role = 'employee'", "role::text = 'employee'"
        ).replace(
            "role = 'admin'", "role::text = 'admin'"
        )
        
        return clean_query
    
    def _process_absent_data(self, attendance_data):
        employee_absences = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.ABSENT:
                employee_name = self._get_employee_name(record.employee)
                employee_absences[employee_name] = employee_absences.get(employee_name, 0) + 1
        
        return {
            "employee_absences": employee_absences,
            "total_absences": sum(employee_absences.values()),
            "most_absent_employee": max(employee_absences.items(), key=lambda x: x[1])[0] if employee_absences else None
        }
    
    def _process_wfh_data(self, attendance_data):
        wfh_count = sum(1 for record in attendance_data if record.status == models.AttendanceType.WFH)
        total_days = len(attendance_data)
        
        employee_wfh = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.WFH:
                employee_name = self._get_employee_name(record.employee)
                employee_wfh[employee_name] = employee_wfh.get(employee_name, 0) + 1
        
        return {
            "wfh_count": wfh_count,
            "total_days": total_days,
            "wfh_percentage": (wfh_count / total_days * 100) if total_days > 0 else 0,
            "employee_wfh": employee_wfh
        }
    
    def _process_leave_data(self, attendance_data):
        leave_count = sum(1 for record in attendance_data if record.status == models.AttendanceType.LEAVE)
        total_days = len(attendance_data)
        
        employee_leave = {}
        for record in attendance_data:
            if record.status == models.AttendanceType.LEAVE:
                employee_name = self._get_employee_name(record.employee)
                employee_leave[employee_name] = employee_leave.get(employee_name, 0) + 1
        
        return {
            "leave_count": leave_count,
            "total_days": total_days,
            "leave_percentage": (leave_count / total_days * 100) if total_days > 0 else 0,
            "employee_leave": employee_leave,
            "most_leave_employee": max(employee_leave.items(), key=lambda x: x[1])[0] if employee_leave else None
        }
    
    def _process_general_data(self, attendance_data):
        status_counts = {
            models.AttendanceType.PRESENT: 0,
            models.AttendanceType.ABSENT: 0,
            models.AttendanceType.WFH: 0,
            models.AttendanceType.HALF_DAY: 0,
            models.AttendanceType.LEAVE: 0
        }
        
        for record in attendance_data:
            if record.status in status_counts:
                status_counts[record.status] += 1
        
        return {
            "status_counts": {status.value: count for status, count in status_counts.items()},
            "total_records": len(attendance_data)
        }
    
    def _create_absent_analysis_prompt(self, attendance_data):
        details = self._process_absent_data(attendance_data)
        
        prompt = "Based on the following attendance data, analyze who was absent the most:\n\n"
        for employee, count in details["employee_absences"].items():
            prompt += f"{employee}: {count} days absent\n"
        
        prompt += f"\nTotal absences: {details['total_absences']}"
        prompt += "\nPlease provide a natural language summary of the absenteeism patterns."
        return prompt
    
    def _create_wfh_analysis_prompt(self, attendance_data):
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
    
    def _create_leave_analysis_prompt(self, attendance_data):
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
    
    def _create_general_summary_prompt(self, attendance_data):
        details = self._process_general_data(attendance_data)
        
        prompt = "Based on the attendance data for the past week:\n\n"
        for status, count in details["status_counts"].items():
            prompt += f"{status}: {count} days\n"
        
        prompt += f"\nTotal records: {details['total_records']}"
        prompt += "\nPlease provide a natural language summary of the attendance patterns."
        return prompt

    async def analyze_custom_query(self, query: str, db: Session) -> schemas.AIInsight:
        """Process a natural language query from user, generate SQL, and provide insights.
        
        Args:
            query: User's natural language query about attendance data
            db: Database session
            
        Returns:
            AIInsight object containing the query, summary, and details
        """
        if not self.client:
            logger.error("Azure OpenAI client not initialized.")
            return schemas.AIInsight(
                query=query,
                summary="AI insights are currently unavailable. Please try again later.",
                details={"error": "Azure OpenAI client not initialized"}
            )
        
        try:
            # Generate SQL from natural language query
            sql_prompt = f"""
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
            
            User query: {query}
            
            IMPORTANT: Return ONLY the raw SQL query without any markdown formatting, explanation, or code blocks. Do not use ``` or any other markdown. Return just the SQL query itself.
            """
            
            # Generate SQL query using Azure OpenAI
            sql_response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_MODEL"),
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates only PostgreSQL queries. Ensure your queries are safe and follow best practices."},
                    {"role": "user", "content": sql_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            generated_sql = sql_response.choices[0].message.content.strip()
            logger.info(f"Generated SQL: {generated_sql}")
            
            # Clean the SQL query by removing markdown code blocks
            clean_sql = self._clean_sql_query(generated_sql)
            logger.info(f"Cleaned SQL: {clean_sql}")
            
            # Execute the SQL query
            try:
                logger.info(f"Executing SQL: {clean_sql}")
                try:
                    result = db.execute(text(clean_sql))
                    raw_data = result.fetchall()
                    column_names = result.keys()
                    
                    # Log success and result count
                    row_count = len(raw_data)
                    logger.info(f"SQL execution successful. Retrieved {row_count} rows.")
                    if row_count == 0:
                        logger.warning("Query returned 0 rows, but executed successfully.")
                    
                except Exception as sql_exec_error:
                    if "should be explicitly declared as text" in str(sql_exec_error):
                        # This shouldn't happen since we're now using text(), but just in case
                        logger.error(f"Text expression error despite using SQLAlchemy text(): {str(sql_exec_error)}")
                        raise
                    else:
                        raise
                
                # Convert to a list of dictionaries
                data = [dict(zip(column_names, row)) for row in raw_data]
                
                # Process query results into insights
                analysis_prompt = f"""
                Based on the following data, provide insights and analysis.
                
                User query: {query}
                
                SQL query used:
                {clean_sql}
                
                Query results:
                {data}
                
                Analyze the data and provide valuable insights related to:
                1. Key patterns, trends, or anomalies in the data
                2. Notable employee or team behaviors
                3. Attendance patterns (if relevant)
                4. Any actionable recommendations
                
                Format your response as a concise, professional analysis of 3-4 sentences that directly answers the user's query.
                """
                
                # Generate insights using Azure OpenAI
                insight_response = self.client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_MODEL"),
                    messages=[
                        {"role": "system", "content": "You are an attendance data analyst that provides clear, concise insights."},
                        {"role": "user", "content": analysis_prompt}
                    ]
                )
                
                summary = insight_response.choices[0].message.content.strip()
                
                insight = schemas.AIInsight(
                    query=query,
                    summary=summary,
                    details={
                        "generated_sql": clean_sql,
                        "data": data
                    }
                )
                
                # Save the insight to the database
                try:
                    crud.save_ai_insight(db, insight)
                except Exception as e:
                    logger.warning(f"Failed to save insight to database: {str(e)}")
                
                return insight
            except Exception as e:
                logger.error(f"Error executing SQL: {str(e)}")
                
                # If there's an error with the SQL, try to get AI to fix it
                fix_prompt = f"""
                There was an error executing this SQL query:
                {clean_sql}
                
                Error: {str(e)}
                
                Common issues to check:
                1. Enum handling: Use status::text = 'value' instead of status = 'value'
                2. Add proper GROUP BY clauses for all non-aggregated columns in SELECT
                3. Use NULLIF() to avoid division by zero
                4. Cast numeric values properly
                5. Ensure date formats are correct
                
                Please fix the query. IMPORTANT: Return ONLY the raw SQL query without any markdown formatting, explanation, or code blocks. Do not use ``` or any other markdown tags.
                """
                
                fix_response = self.client.chat.completions.create(
                    model=os.getenv("AZURE_OPENAI_MODEL"),
                    messages=[
                        {"role": "system", "content": "You are a SQL expert that fixes PostgreSQL queries. Ensure your queries are safe and follow best practices."},
                        {"role": "user", "content": fix_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                fixed_sql = fix_response.choices[0].message.content.strip()
                logger.info(f"Fixed SQL: {fixed_sql}")
                
                # Clean the fixed SQL query
                clean_fixed_sql = self._clean_sql_query(fixed_sql)
                logger.info(f"Cleaned fixed SQL: {clean_fixed_sql}")
                
                try:
                    logger.info(f"Executing fixed SQL: {clean_fixed_sql}")
                    try:
                        result = db.execute(text(clean_fixed_sql))
                        raw_data = result.fetchall()
                        column_names = result.keys()
                        
                        # Log success and result count
                        row_count = len(raw_data)
                        logger.info(f"Fixed SQL execution successful. Retrieved {row_count} rows.")
                        if row_count == 0:
                            logger.warning("Fixed query returned 0 rows, but executed successfully.")
                        
                    except Exception as sql_exec_error:
                        if "should be explicitly declared as text" in str(sql_exec_error):
                            # This shouldn't happen since we're now using text(), but just in case
                            logger.error(f"Text expression error despite using SQLAlchemy text(): {str(sql_exec_error)}")
                            raise
                        else:
                            raise
                    
                    # Convert to a list of dictionaries
                    data = [dict(zip(column_names, row)) for row in raw_data]
                    
                    # Process query results into insights
                    analysis_prompt = f"""
                    You are an AI analyst for an attendance management system. Based on the following data, provide insights and analysis.
                    
                    User query: {query}
                    
                    SQL queries used:
                    Original: {clean_sql}
                    Fixed: {clean_fixed_sql}
                    
                    Query results:
                    {data}
                    
                    Analyze the data and provide valuable insights related to:
                    1. Key patterns, trends, or anomalies in the data
                    2. Notable employee or team behaviors
                    3. Attendance patterns (if relevant)
                    4. Any actionable recommendations
                    
                    Format your response as a concise, professional analysis of 3-4 sentences that directly answers the user's query.
                    """
                    
                    # Generate insights using Azure OpenAI
                    insight_response = self.client.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_MODEL"),
                        messages=[
                            {"role": "system", "content": "You are an attendance data analyst that provides clear, concise insights."},
                            {"role": "user", "content": analysis_prompt}
                        ]
                    )
                    
                    summary = insight_response.choices[0].message.content.strip()
                    
                    insight = schemas.AIInsight(
                        query=query,
                        summary=summary,
                        details={
                            "generated_sql": clean_sql,
                            "fixed_sql": clean_fixed_sql,
                            "data": data
                        }
                    )
                    
                    # Save the insight to the database
                    try:
                        crud.save_ai_insight(db, insight)
                    except Exception as e:
                        logger.warning(f"Failed to save insight to database: {str(e)}")
                    
                    return insight
                except Exception as e2:
                    logger.error(f"Error executing fixed SQL: {str(e2)}")
                    return schemas.AIInsight(
                        query=query,
                        summary="Unable to analyze this query. Please try rephrasing or ask a different question.",
                        details={
                            "error": f"Original error: {str(e)}, Fix attempt error: {str(e2)}",
                            "generated_sql": clean_sql,
                            "fixed_sql": clean_fixed_sql
                        }
                    )
        except Exception as e:
            logger.error(f"Error in analyze_custom_query: {str(e)}")
            return schemas.AIInsight(
                query=query,
                summary="An error occurred while analyzing your query. Please try again later.",
                details={"error": str(e)}
            ) 