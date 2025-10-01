# BlingAuto API - Docker Deployment Guide

**Production-Ready Deployment with Docker, PostgreSQL, and Redis**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Environment Configuration](#environment-configuration)
5. [Building and Running](#building-and-running)
6. [Service Architecture](#service-architecture)
7. [Database Migrations](#database-migrations)
8. [Health Checks](#health-checks)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)
11. [Production Best Practices](#production-best-practices)

---

## Overview

This deployment uses Docker Compose to orchestrate three main services:

- **PostgreSQL 16**: Production database with persistent storage
- **Redis 7**: High-performance caching and session management
- **BlingAuto API**: FastAPI application with automatic migrations

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       Docker Network                        │
│  ┌────────────┐      ┌────────────┐      ┌──────────────┐  │
│  │            │      │            │      │              │  │
│  │ PostgreSQL │◄─────┤ BlingAuto  │◄─────┤    Redis     │  │
│  │  (Port     │      │    API     │      │  (Port 6379) │  │
│  │   5432)    │      │  (Port     │      │              │  │
│  │            │      │   8000)    │      │              │  │
│  └────────────┘      └────────────┘      └──────────────┘  │
│       ▲                     ▲                     ▲         │
│       │                     │                     │         │
│  [Volume:                   │                [Volume:      │
│   postgres_data]            │                redis_data]   │
│                             │                              │
└─────────────────────────────┼──────────────────────────────┘
                              │
                         External Port
                            :8000
```

---

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository

### System Requirements

**Minimum**:
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space

**Recommended**:
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD storage

### Verify Installation

```bash
docker --version
# Docker version 24.0.0 or higher

docker-compose --version
# Docker Compose version v2.20.0 or higher
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/blingauto-api.git
cd blingauto-api
```

### 2. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your secure values
nano .env  # or use your preferred editor
```

**CRITICAL**: Update these values in `.env`:
```bash
# Security
SECRET_KEY=<generate-with-python-secrets>
POSTGRES_PASSWORD=<secure-password-min-20-chars>
REDIS_PASSWORD=<secure-password-min-20-chars>

# Database
POSTGRES_USER=blingauto_user
POSTGRES_DB=blingauto

# Initial Admin User
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=<secure-password-min-12-chars>
```

### 3. Generate Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
# Copy output to SECRET_KEY in .env
```

### 4. Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 5. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected output:
{
  "status": "healthy",
  "timestamp": "2025-10-01T...",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "system": {"status": "healthy", "cpu_percent": 15.2, ...}
  }
}

# Access API documentation
open http://localhost:8000/docs
```

### 6. Login as Admin

The initial admin user is automatically created on first startup:

```bash
# Login with admin credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "your-admin-password"
  }'

# Response includes access token
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "admin@yourdomain.com",
    "role": "admin",
    "full_name": "Admin User"
  }
}
```

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

---

## Environment Configuration

### Required Environment Variables

```bash
# =============================================================================
# CRITICAL - MUST CHANGE IN PRODUCTION
# =============================================================================
SECRET_KEY=your-secret-key-here-change-in-production
POSTGRES_PASSWORD=change_this_password_to_secure_value
REDIS_PASSWORD=change_this_redis_password_to_secure_value

# =============================================================================
# Application Configuration
# =============================================================================
ENVIRONMENT=production
APP_NAME=BlingAuto API
APP_VERSION=1.0.0
DEBUG=false

# =============================================================================
# Database Configuration
# =============================================================================
POSTGRES_DB=blingauto
POSTGRES_USER=blingauto_user
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}

# =============================================================================
# Redis Configuration
# =============================================================================
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# =============================================================================
# Server Configuration
# =============================================================================
WORKERS=4  # Adjust based on CPU cores
API_PORT=8000

# =============================================================================
# Initial Admin User (Optional)
# =============================================================================
# Automatically creates admin user on first startup
INITIAL_ADMIN_EMAIL=admin@yourdomain.com
INITIAL_ADMIN_PASSWORD=ChangeThisSecurePassword123!
INITIAL_ADMIN_FIRST_NAME=Admin
INITIAL_ADMIN_LAST_NAME=User

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Optional Variables

```bash
# Email Configuration (for password reset, verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@blingauto.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
```

---

## Building and Running

### Development Mode

```bash
# Start with auto-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View logs
docker-compose logs -f api
```

### Production Mode

```bash
# Build images
docker-compose build

# Start services in detached mode
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### Individual Service Commands

```bash
# Restart API only
docker-compose restart api

# View API logs
docker-compose logs -f api

# Execute command in API container
docker-compose exec api bash

# View PostgreSQL logs
docker-compose logs -f postgres

# Connect to PostgreSQL
docker-compose exec postgres psql -U blingauto_user -d blingauto

# View Redis logs
docker-compose logs -f redis

# Connect to Redis CLI
docker-compose exec redis redis-cli -a <REDIS_PASSWORD>
```

---

## Service Architecture

### Services Overview

#### 1. PostgreSQL Database

**Image**: `postgres:16-alpine`
**Port**: 5432 (internal), configurable external
**Volume**: `postgres_data` (persistent)

**Features**:
- Automatic initialization via `init-db.sql`
- Extensions: `uuid-ossp`, `pg_trgm`
- Health checks with `pg_isready`
- Timezone: UTC

**Configuration**:
```yaml
environment:
  POSTGRES_DB: blingauto
  POSTGRES_USER: blingauto_user
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

#### 2. Redis Cache

**Image**: `redis:7-alpine`
**Port**: 6379 (internal), configurable external
**Volume**: `redis_data` (persistent)

**Features**:
- Password authentication
- Memory limit: 256MB (configurable)
- LRU eviction policy
- Persistence: RDB snapshots every 60 seconds

**Configuration**:
```bash
redis-server \
  --requirepass ${REDIS_PASSWORD} \
  --maxmemory 256mb \
  --maxmemory-policy allkeys-lru
```

#### 3. BlingAuto API

**Image**: Custom (built from Dockerfile)
**Port**: 8000
**Health Check**: `/health` endpoint

**Features**:
- Multi-stage Docker build
- Non-root user (`appuser`)
- Automatic database migrations
- Health checks (liveness + readiness)
- 4 workers (configurable)

**Startup Sequence**:
1. Wait for PostgreSQL to be ready
2. Wait for Redis to be ready
3. Run Alembic migrations
4. Create initial admin user (if configured)
5. Start Uvicorn server

---

## Database Migrations

### Automatic Migrations

Migrations run automatically on container startup via the `migrations` service:

```yaml
migrations:
  command: ["alembic", "upgrade", "head"]
  depends_on:
    postgres:
      condition: service_healthy
```

### Manual Migrations

```bash
# Run migrations manually
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history

# View current version
docker-compose exec api alembic current

# Create new migration (auto-generate)
docker-compose exec api alembic revision --autogenerate -m "description"

# Create new migration (manual)
docker-compose exec api alembic revision -m "description"
```

### Migration Files Location

```
migrations/
├── versions/
│   ├── 001_initial_migration.py
│   ├── 002_add_facilities_tables.py
│   └── ...
├── env.py
└── script.py.mako
```

---

## Health Checks

### Available Endpoints

#### 1. Health Check (Liveness)

```bash
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "redis": {
      "status": "healthy"
    },
    "system": {
      "status": "healthy",
      "cpu_percent": 15.2,
      "memory_percent": 45.8,
      "disk_percent": 62.1
    }
  }
}
```

#### 2. Readiness Check

```bash
GET /ready
```

**Response**:
```json
{
  "ready": true,
  "timestamp": "2025-10-01T12:00:00Z",
  "checks": {
    "database": {
      "status": "healthy"
    }
  }
}
```

### Docker Health Checks

All services have built-in health checks:

```bash
# View health status
docker-compose ps

# Example output:
NAME                  STATUS                    PORTS
blingauto-api        Up 2 minutes (healthy)    0.0.0.0:8000->8000/tcp
blingauto-postgres   Up 2 minutes (healthy)    0.0.0.0:5432->5432/tcp
blingauto-redis      Up 2 minutes (healthy)    0.0.0.0:6379->6379/tcp
```

### Monitoring Health

```bash
# Watch health checks in real-time
watch -n 5 'curl -s http://localhost:8000/health | jq'

# Check database health
docker-compose exec postgres pg_isready -U blingauto_user

# Check Redis health
docker-compose exec redis redis-cli -a <REDIS_PASSWORD> ping
```

---

## Scaling

### Horizontal Scaling (Multiple API Instances)

```bash
# Scale API to 3 instances
docker-compose up -d --scale api=3

# Behind a load balancer (e.g., Nginx)
# See nginx.conf.example for configuration
```

### Vertical Scaling (Resource Limits)

Edit `docker-compose.yml`:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

### Worker Configuration

Adjust workers based on CPU cores:

```bash
# Formula: (2 * CPU_CORES) + 1
# 2 CPU cores = 5 workers
# 4 CPU cores = 9 workers
# 8 CPU cores = 17 workers

WORKERS=9  # Set in .env
```

### Database Connection Pooling

```bash
# Adjust in .env based on workers
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Total connections = WORKERS * POOL_SIZE + MAX_OVERFLOW
# Example: 4 workers * 10 pool = 40 + 20 overflow = 60 max connections
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs api

# Common causes:
# - Missing .env file
# - Invalid DATABASE_URL format
# - Port 8000 already in use
```

**Solution**:
```bash
# Check if port is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
API_PORT=8001 docker-compose up -d
```

#### 2. Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U blingauto_user -d blingauto -c "SELECT 1;"
```

**Solution**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Recreate if corrupted
docker-compose down
docker volume rm blingauto-postgres-data
docker-compose up -d
```

#### 3. Redis Connection Failed

```bash
# Check Redis logs
docker-compose logs redis

# Test connection
docker-compose exec redis redis-cli -a <REDIS_PASSWORD> ping
```

**Solution**:
```bash
# Verify REDIS_PASSWORD in .env matches docker-compose.yml
# Restart Redis
docker-compose restart redis
```

#### 4. Migration Failures

```bash
# View migration logs
docker-compose logs migrations

# Check current migration version
docker-compose exec api alembic current

# Manually run migrations
docker-compose exec api alembic upgrade head
```

**Solution**:
```bash
# Rollback and retry
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic upgrade head

# If database is corrupted, reset (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

#### 5. High Memory Usage

```bash
# Check resource usage
docker stats

# View container details
docker-compose exec api top
```

**Solution**:
```bash
# Reduce workers
WORKERS=2 docker-compose up -d

# Add memory limits in docker-compose.yml
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=true docker-compose up

# Run API in interactive mode
docker-compose run --rm api bash

# Inside container
python -m uvicorn main:app --reload --log-level debug
```

### Network Issues

```bash
# Inspect network
docker network inspect blingauto-network

# Test connectivity between services
docker-compose exec api ping postgres
docker-compose exec api ping redis

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

---

## Production Best Practices

### Security

1. **Secrets Management**
   ```bash
   # Use Docker secrets or external secret manager
   # Never commit .env to version control
   git update-index --assume-unchanged .env
   ```

2. **SSL/TLS**
   ```bash
   # Use reverse proxy (Nginx, Traefik) with SSL certificates
   # Configure DATABASE_URL with sslmode=require for remote PostgreSQL
   ```

3. **Network Isolation**
   ```bash
   # Remove port mappings for internal services
   # Only expose API port 8000
   ```

4. **Non-Root Containers**
   ```bash
   # Already configured in Dockerfile
   USER appuser
   ```

### Monitoring

1. **Logging**
   ```bash
   # Use centralized logging (ELK, Loki, CloudWatch)
   # Configure log drivers in docker-compose.yml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

2. **Metrics**
   ```bash
   # Integrate Prometheus + Grafana
   # Add metrics endpoint to API
   ```

3. **Alerting**
   ```bash
   # Configure alerts for:
   # - Health check failures
   # - High error rates
   # - Resource exhaustion
   ```

### Backups

1. **Database Backups**
   ```bash
   # Automated daily backups
   docker-compose exec postgres pg_dump -U blingauto_user blingauto > backup_$(date +%Y%m%d).sql

   # Restore from backup
   docker-compose exec -T postgres psql -U blingauto_user blingauto < backup_20251001.sql
   ```

2. **Volume Backups**
   ```bash
   # Backup volumes
   docker run --rm -v blingauto-postgres-data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz /data

   # Restore volumes
   docker run --rm -v blingauto-postgres-data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres-backup.tar.gz -C /
   ```

### Performance

1. **Connection Pooling**
   ```bash
   # Tune pool size based on load
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=40
   ```

2. **Redis Configuration**
   ```bash
   # Increase memory for caching
   --maxmemory 512mb
   ```

3. **Worker Tuning**
   ```bash
   # Monitor and adjust workers
   WORKERS=$(( $(nproc) * 2 + 1 ))
   ```

### Updates and Maintenance

1. **Rolling Updates**
   ```bash
   # Update with zero downtime (requires load balancer)
   docker-compose pull
   docker-compose up -d --no-deps --build api
   ```

2. **Database Migrations**
   ```bash
   # Test migrations in staging first
   # Always backup before production migrations
   ```

3. **Cleanup**
   ```bash
   # Remove unused images
   docker image prune -a

   # Remove unused volumes
   docker volume prune
   ```

---

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Health Endpoint**: http://localhost:8000/health
- **Project Repository**: https://github.com/yourusername/blingauto-api
- **Issue Tracker**: https://github.com/yourusername/blingauto-api/issues

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs`
3. Open an issue on GitHub
4. Contact: support@blingauto.com

---

**Last Updated**: 2025-10-01
**Version**: 1.0.0
**Docker Compose Version**: 3.8
