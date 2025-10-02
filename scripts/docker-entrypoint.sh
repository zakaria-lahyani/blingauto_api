#!/bin/bash
# =============================================================================
# BlingAuto API - Docker Entrypoint Script
# Handles startup tasks: wait for services, run migrations, start application
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}BlingAuto API - Starting Application${NC}"
echo -e "${GREEN}==============================================================================${NC}"

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"

    # Extract database connection details from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
        DB_HOST="postgres"
        DB_PORT="5432"
    fi

    echo -e "${YELLOW}Connecting to PostgreSQL at ${DB_HOST}:${DB_PORT}${NC}"

    until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
        echo -e "${YELLOW}PostgreSQL is unavailable - sleeping${NC}"
        sleep 2
    done

    echo -e "${GREEN}PostgreSQL is up and ready!${NC}"
}

# Function to wait for Redis
wait_for_redis() {
    if [ -z "$REDIS_URL" ]; then
        echo -e "${YELLOW}Redis not configured - skipping${NC}"
        return 0
    fi

    echo -e "${YELLOW}Waiting for Redis...${NC}"

    # Extract Redis host from REDIS_URL
    # Format: redis://:password@host:port/db
    REDIS_HOST=$(echo $REDIS_URL | sed -n 's/.*@\(.*\):.*/\1/p')
    REDIS_PORT=$(echo $REDIS_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

    if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PORT" ]; then
        REDIS_HOST="redis"
        REDIS_PORT="6379"
    fi

    echo -e "${YELLOW}Connecting to Redis at ${REDIS_HOST}:${REDIS_PORT}${NC}"

    until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; do
        echo -e "${YELLOW}Redis is unavailable - sleeping${NC}"
        sleep 2
    done

    echo -e "${GREEN}Redis is up and ready!${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"

    if alembic upgrade head; then
        echo -e "${GREEN}Migrations completed successfully!${NC}"
    else
        echo -e "${RED}Migration failed!${NC}"
        exit 1
    fi
}

# Function to create initial admin user (optional)
create_admin_user() {
    if [ -n "$INITIAL_ADMIN_EMAIL" ] && [ -n "$INITIAL_ADMIN_PASSWORD" ]; then
        echo -e "${YELLOW}Creating initial admin user...${NC}"

        if python scripts/create_admin.py; then
            echo -e "${GREEN}Admin user setup completed!${NC}"
        else
            echo -e "${RED}Admin user setup failed, but continuing...${NC}"
        fi
    else
        echo -e "${YELLOW}Admin user creation skipped (no credentials configured)${NC}"
    fi
}

# Main execution
main() {
    echo -e "${YELLOW}Environment: ${ENVIRONMENT:-production}${NC}"
    echo -e "${YELLOW}App Version: ${APP_VERSION:-1.0.0}${NC}"
    echo ""

    # Note: Migrations are handled by a separate migrations service in docker-compose
    # This ensures migrations run once before the API starts
    # The API service depends on migrations completing successfully

    echo ""
    echo -e "${GREEN}==============================================================================${NC}"
    echo -e "${GREEN}Starting BlingAuto API Server${NC}"
    echo -e "${GREEN}==============================================================================${NC}"
    echo ""

    # Start the application
    # Pass all arguments to the command
    exec "$@"
}

# Run main function
main "$@"
