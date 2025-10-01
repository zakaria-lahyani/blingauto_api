#!/bin/bash
# =============================================================================
# Docker Entrypoint for BlingAuto API - Migration Runner
# Handles database migrations with retry logic and health checks
# =============================================================================

set -e

echo "=========================================="
echo "BlingAuto API - Migration Runner"
echo "=========================================="
echo ""

# Configuration
MAX_RETRIES=30
RETRY_INTERVAL=2
DB_READY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    sys.exit(0)
except Exception as e:
    print(f"Database not ready: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# Wait for database to be ready
echo "→ Waiting for database to be ready..."
for i in $(seq 1 $MAX_RETRIES); do
    if check_database 2>/dev/null; then
        DB_READY=true
        echo -e "${GREEN}✓ Database is ready!${NC}"
        break
    fi

    echo "  Attempt $i/$MAX_RETRIES - Database not ready, waiting ${RETRY_INTERVAL}s..."
    sleep $RETRY_INTERVAL
done

if [ "$DB_READY" = false ]; then
    echo -e "${RED}✗ Failed to connect to database after $MAX_RETRIES attempts${NC}"
    echo "  Please check your DATABASE_URL and database container status"
    exit 1
fi

echo ""
echo "→ Running database migrations..."

# Run Alembic migrations
if alembic upgrade head; then
    echo -e "${GREEN}✓ Migrations completed successfully!${NC}"
else
    echo -e "${RED}✗ Migration failed!${NC}"
    exit 1
fi

echo ""
echo "→ Verifying migration status..."

# Verify current migration version
python << 'EOF'
import sys
import os
from sqlalchemy import create_engine, text

try:
    database_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
    engine = create_engine(database_url)

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()

        if version:
            print(f"  Current migration version: {version}")
        else:
            print("  No migrations applied yet")

    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migration verification successful!${NC}"
else
    echo -e "${YELLOW}⚠ Warning: Could not verify migration status${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Migration runner completed successfully!${NC}"
echo "=========================================="
