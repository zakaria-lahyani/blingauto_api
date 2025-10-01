#!/bin/bash
# =============================================================================
# Docker Entrypoint for BlingAuto API
# Handles startup, migration checks, and graceful shutdown
# =============================================================================

set -e

echo "=========================================="
echo "BlingAuto API - Starting Application"
echo "=========================================="
echo ""

# Configuration
MAX_RETRIES=60
RETRY_INTERVAL=2
DB_READY=false
MIGRATIONS_READY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if database is ready
check_database() {
    python << EOF
import sys
import os
from sqlalchemy import create_engine, text

try:
    database_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
    if not database_url:
        sys.exit(1)

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    sys.exit(0)
except:
    sys.exit(1)
EOF
}

# Function to check if migrations are applied
check_migrations() {
    python << EOF
import sys
import os
from sqlalchemy import create_engine, text

try:
    database_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if alembic_version table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            )
        """))
        if not result.scalar():
            sys.exit(1)

        # Check if at least one migration is applied
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        if version:
            print(f"{version}", end='')
            sys.exit(0)
        else:
            sys.exit(1)
except:
    sys.exit(1)
EOF
}

# Wait for database to be ready
echo -e "${BLUE}→ Waiting for database to be ready...${NC}"
for i in $(seq 1 $MAX_RETRIES); do
    if check_database 2>/dev/null; then
        DB_READY=true
        echo -e "${GREEN}✓ Database is ready!${NC}"
        break
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "  Still waiting for database... (attempt $i/$MAX_RETRIES)"
    fi
    sleep $RETRY_INTERVAL
done

if [ "$DB_READY" = false ]; then
    echo -e "${RED}✗ Failed to connect to database after $MAX_RETRIES attempts${NC}"
    exit 1
fi

# Wait for migrations to be applied
echo ""
echo -e "${BLUE}→ Waiting for database migrations to complete...${NC}"
for i in $(seq 1 $MAX_RETRIES); do
    version=$(check_migrations 2>/dev/null)
    if [ $? -eq 0 ]; then
        MIGRATIONS_READY=true
        echo -e "${GREEN}✓ Migrations are up to date! (version: $version)${NC}"
        break
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "  Still waiting for migrations... (attempt $i/$MAX_RETRIES)"
    fi
    sleep $RETRY_INTERVAL
done

if [ "$MIGRATIONS_READY" = false ]; then
    echo -e "${YELLOW}⚠ Warning: Migrations may not be applied${NC}"
    echo "  Continuing anyway... (check migration runner logs)"
fi

# Optional: Run initial admin setup if configured
if [ -n "$INITIAL_ADMIN_EMAIL" ] && [ -n "$INITIAL_ADMIN_PASSWORD" ]; then
    echo ""
    echo -e "${BLUE}→ Checking initial admin user setup...${NC}"

    python << 'EOF' || echo -e "${YELLOW}⚠ Admin setup skipped or failed${NC}"
import sys
import os
import asyncio
sys.path.insert(0, '/app')

async def setup_admin():
    try:
        from app.features.auth.application.services.admin_setup_service import create_initial_admin
        from app.core.db import async_session_maker

        email = os.getenv('INITIAL_ADMIN_EMAIL')
        password = os.getenv('INITIAL_ADMIN_PASSWORD')
        first_name = os.getenv('INITIAL_ADMIN_FIRST_NAME', 'Admin')
        last_name = os.getenv('INITIAL_ADMIN_LAST_NAME', 'User')

        if email and password:
            async with async_session_maker() as session:
                admin = await create_initial_admin(
                    session=session,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                if admin:
                    print(f"✓ Initial admin user created: {email}")
                else:
                    print(f"✓ Admin user already exists: {email}")
    except Exception as e:
        print(f"Warning: Admin setup error: {e}", file=sys.stderr)

asyncio.run(setup_admin())
EOF
fi

# Print application info
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Pre-flight checks complete!${NC}"
echo "=========================================="
echo ""
echo "Application Information:"
echo "  - Name: ${APP_NAME:-BlingAuto API}"
echo "  - Version: ${APP_VERSION:-1.0.0}"
echo "  - Environment: ${ENVIRONMENT:-production}"
echo "  - Host: ${HOST:-0.0.0.0}"
echo "  - Port: ${PORT:-8000}"
echo "  - Workers: ${WORKERS:-4}"
echo ""
echo "→ Starting Uvicorn server..."
echo ""

# Execute the main command (start uvicorn)
exec "$@"
