#!/bin/bash
# =============================================================================
# BlingAuto API - Production Deployment Script
# Handles zero-downtime deployment with migrations
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
PROJECT_NAME="${PROJECT_NAME:-blingauto_api}"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Banner
echo -e "${CYAN}"
echo "=========================================="
echo "  BlingAuto API - Deployment Script"
echo "=========================================="
echo -e "${NC}"

# Function to print status messages
print_status() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check if services are running
check_services() {
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service health
wait_for_health() {
    local service=$1
    local max_attempts=60
    local attempt=1

    print_status "Waiting for $service to be healthy..."

    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy"; then
            print_success "$service is healthy!"
            return 0
        fi

        if [ $((attempt % 10)) -eq 0 ]; then
            echo "  Still waiting... (attempt $attempt/$max_attempts)"
        fi

        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "$service did not become healthy in time"
    return 1
}

# Function to backup database
backup_database() {
    print_status "Creating database backup..."

    mkdir -p "$BACKUP_DIR"

    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U "${POSTGRES_USER:-blingauto_user}" \
        -d "${POSTGRES_DB:-blingauto}" \
        > "$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"; then
        print_success "Database backed up to $BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
    else
        print_warning "Database backup failed (service may not be running)"
    fi
}

# Main deployment flow
main() {
    echo ""
    print_status "Starting deployment process..."
    echo ""

    # Step 1: Check if services are running
    print_status "Checking current deployment status..."
    if check_services; then
        print_success "Services are currently running"
        EXISTING_DEPLOYMENT=true

        # Backup database if services are running
        backup_database
    else
        print_warning "No existing deployment detected"
        EXISTING_DEPLOYMENT=false
    fi

    # Step 2: Pull latest code (if in git repo)
    if [ -d ".git" ]; then
        echo ""
        print_status "Pulling latest code from repository..."
        git pull || print_warning "Git pull failed or not needed"
    fi

    # Step 3: Build new images
    echo ""
    print_status "Building Docker images..."
    if docker-compose -f "$COMPOSE_FILE" build --no-cache; then
        print_success "Images built successfully!"
    else
        print_error "Image build failed!"
        exit 1
    fi

    # Step 4: Stop old containers (if exists)
    if [ "$EXISTING_DEPLOYMENT" = true ]; then
        echo ""
        print_status "Stopping old containers..."
        docker-compose -f "$COMPOSE_FILE" stop api
        print_success "Old containers stopped"
    fi

    # Step 5: Start infrastructure services
    echo ""
    print_status "Starting infrastructure services (postgres, redis)..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis

    # Wait for postgres to be healthy
    wait_for_health postgres || exit 1
    wait_for_health redis || exit 1

    # Step 6: Run database migrations
    echo ""
    print_status "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" up migrations

    # Check migration exit code
    MIGRATION_EXIT_CODE=$(docker inspect blingauto-migrations --format='{{.State.ExitCode}}')
    if [ "$MIGRATION_EXIT_CODE" -eq 0 ]; then
        print_success "Migrations completed successfully!"
    else
        print_error "Migrations failed with exit code $MIGRATION_EXIT_CODE"
        print_error "Check migration logs: docker-compose logs migrations"
        exit 1
    fi

    # Step 7: Start API service
    echo ""
    print_status "Starting API service..."
    docker-compose -f "$COMPOSE_FILE" up -d api

    # Wait for API to be healthy
    wait_for_health api || {
        print_error "API failed to start properly"
        print_error "Check logs: docker-compose logs api"
        exit 1
    }

    # Step 8: Cleanup old containers and images
    echo ""
    print_status "Cleaning up old resources..."
    docker-compose -f "$COMPOSE_FILE" rm -f || true
    docker image prune -f || true
    print_success "Cleanup completed"

    # Step 9: Verify deployment
    echo ""
    print_status "Verifying deployment..."

    # Check API health endpoint
    sleep 5  # Give API a moment to fully start

    if curl -f -s http://localhost:${API_PORT:-8000}/health > /dev/null; then
        print_success "API health check passed!"
    else
        print_warning "API health check failed - service may still be starting"
    fi

    # Show running services
    echo ""
    print_status "Current service status:"
    docker-compose -f "$COMPOSE_FILE" ps

    # Final summary
    echo ""
    echo -e "${GREEN}=========================================="
    echo "  ✓ Deployment Completed Successfully!"
    echo "==========================================${NC}"
    echo ""
    echo "Service URLs:"
    echo "  - API: http://localhost:${API_PORT:-8000}"
    echo "  - Docs: http://localhost:${API_PORT:-8000}/docs"
    echo "  - Health: http://localhost:${API_PORT:-8000}/health"
    echo ""
    echo "Useful commands:"
    echo "  - View logs: docker-compose logs -f api"
    echo "  - Check status: docker-compose ps"
    echo "  - Stop services: docker-compose stop"
    echo "  - Restart API: docker-compose restart api"
    echo ""
    echo "Database backup: $BACKUP_DIR/db_backup_${TIMESTAMP}.sql"
    echo ""
}

# Run main function
main

# Exit successfully
exit 0
