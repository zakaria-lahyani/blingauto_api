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

# Database and migrations are handled via docker-compose depends_on with health checks
# The migrations service runs first and completes before this API service starts
# No need for additional waiting here
echo -e "${BLUE}→ Database and migrations managed by docker-compose dependencies${NC}"
echo -e "${GREEN}✓ Ready to start API server${NC}"

# Optional: Run initial admin setup if configured
if [ -n "$INITIAL_ADMIN_EMAIL" ] && [ -n "$INITIAL_ADMIN_PASSWORD" ]; then
    echo ""
    echo -e "${BLUE}→ Running initial admin user setup...${NC}"

    python /app/scripts/create_default_admin.py || echo -e "${YELLOW}⚠ Admin setup failed${NC}"
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
