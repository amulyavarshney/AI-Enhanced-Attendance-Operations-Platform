#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database
createdb attendance_db
createdb attendance_test_db

# Initialize Alembic
alembic init alembic

# Run migrations
alembic upgrade head

# Set PYTHONPATH to include the current directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run tests
pytest app/tests/

# Start the application
uvicorn app.main:app --reload 