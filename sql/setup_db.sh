#!/bin/bash

# Attendance Management System Database Setup Script

# Configuration
DB_NAME=${1:-"attendance_db"}
DB_USER=${2:-"postgres"}
DB_PASSWORD=${3:-"postgres"}
DB_HOST=${4:-"localhost"}
DB_PORT=${5:-"5432"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run SQL scripts
run_sql() {
  echo -e "${BLUE}Running $1...${NC}"
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$1" 2>&1
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully executed $1${NC}"
    return 0
  else
    echo -e "${RED}✗ Failed to execute $1${NC}"
    return 1
  fi
}

# Function to display help
show_help() {
  echo -e "${YELLOW}Attendance Management System - Database Setup Script${NC}"
  echo
  echo "Usage: $0 [DB_NAME] [DB_USER] [DB_PASSWORD] [DB_HOST] [DB_PORT] [OPTION]"
  echo
  echo "Default parameters:"
  echo "  DB_NAME     = attendance_db"
  echo "  DB_USER     = postgres"
  echo "  DB_PASSWORD = postgres"
  echo "  DB_HOST     = localhost"
  echo "  DB_PORT     = 5432"
  echo
  echo "Options:"
  echo "  -h, --help     Show this help message"
  echo "  -a, --all      Run full database setup (default)"
  echo "  -s, --schema   Create only database schema"
  echo "  -d, --data     Load only sample data"
  echo "  -r, --reports  Create only reporting functions"
  echo "  -m, --maint    Create only maintenance functions"
  echo
  echo "Example:"
  echo "  $0 attendance_db postgres mypassword localhost 5432 --all"
  echo
}

# Check if database exists, if not create it
create_db_if_not_exists() {
  echo -e "${BLUE}Checking if database $DB_NAME exists...${NC}"
  if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${GREEN}✓ Database $DB_NAME already exists${NC}"
  else
    echo -e "${YELLOW}Database $DB_NAME does not exist. Creating...${NC}"
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" 2>&1
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✓ Successfully created database $DB_NAME${NC}"
    else
      echo -e "${RED}✗ Failed to create database $DB_NAME${NC}"
      exit 1
    fi
  fi
}

# Parse command line arguments for options
OPTION="--all"
for arg in "$@"; do
  case $arg in
    -h|--help)
      show_help
      exit 0
      ;;
    -a|--all)
      OPTION="--all"
      shift
      ;;
    -s|--schema)
      OPTION="--schema"
      shift
      ;;
    -d|--data)
      OPTION="--data"
      shift
      ;;
    -r|--reports)
      OPTION="--reports"
      shift
      ;;
    -m|--maint)
      OPTION="--maint"
      shift
      ;;
  esac
done

# Welcome message
echo -e "${YELLOW}=====================================================${NC}"
echo -e "${YELLOW}   Attendance Management System - Database Setup     ${NC}"
echo -e "${YELLOW}=====================================================${NC}"
echo
echo -e "Database: ${BLUE}$DB_NAME${NC}"
echo -e "User:     ${BLUE}$DB_USER${NC}"
echo -e "Host:     ${BLUE}$DB_HOST:$DB_PORT${NC}"
echo

# Create database if it doesn't exist
create_db_if_not_exists

# Execute according to selected option
case $OPTION in
  --all)
    echo -e "${YELLOW}Running full database setup...${NC}"
    run_sql "setup_database.sql"
    ;;
  --schema)
    echo -e "${YELLOW}Creating database schema...${NC}"
    run_sql "schema/schema.sql"
    ;;
  --data)
    echo -e "${YELLOW}Loading sample data...${NC}"
    run_sql "data/mock_data.sql"
    ;;
  --reports)
    echo -e "${YELLOW}Creating reporting functions...${NC}"
    run_sql "reports/reports.sql"
    ;;
  --maint)
    echo -e "${YELLOW}Creating maintenance functions...${NC}"
    run_sql "maintenance/db_maintenance.sql"
    ;;
  *)
    echo -e "${RED}Invalid option. Use --help to see available options.${NC}"
    exit 1
    ;;
esac

echo
echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}                 Setup Completed                      ${NC}"
echo -e "${GREEN}=====================================================${NC}" 