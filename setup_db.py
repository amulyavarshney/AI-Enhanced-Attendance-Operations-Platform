import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.getenv('DB_NAME'),))
        exists = False #cur.fetchone()

        if not exists:
            # Read and execute schema.sql
            with open('schema.sql', 'r') as file:
                schema_sql = file.read()
                cur.execute(schema_sql)

            print("Database schema created successfully!")
        else:
            print(f"Database {os.getenv('DB_NAME')} already exists.")
        
        # Close database connection
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error setting up database: {str(e)}")
        raise

if __name__ == "__main__":
    setup_database() 