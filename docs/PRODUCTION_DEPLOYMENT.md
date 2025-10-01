# BlingAuto API - Production Deployment Guide

## Overview

This guide provides production-ready deployment procedures with automated migrations, zero-downtime updates, and rollback strategies.

## Quick Start

### First-Time Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd blingauto_api

# 2. Configure environment
cp .env.example .env
nano .env  # Update with production credentials

# 3. Deploy
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Subsequent Deployments

```bash
# Pull latest changes and deploy
./scripts/deploy.sh
```

That's it! The script handles:
- ✅ Database backups
- ✅ Image building
- ✅ Zero-downtime migration
- ✅ Automatic rollback on failure
- ✅ Health checks

## Architecture

### Deployment Flow

```
1. Database Backup
   ↓
2. Build New Images
   ↓
3. Run Migrations (isolated container)
   ↓
4. Start New API (waits for migrations)
   ↓
5. Health Checks
   ↓
6. Cleanup Old Resources
```

### Key Components

**Migration Runner** (`docker-entrypoint-migrations.sh`):
- Waits for database readiness
- Applies Alembic migrations
- Verifies migration success
- Exits with status code

**API Entrypoint** (`docker-entrypoint-api.sh`):
- Waits for database
- Waits for migrations to complete
- Optionally creates initial admin user
- Starts Uvicorn server

**Deploy Script** (`deploy.sh`):
- Orchestrates entire deployment
- Handles backups and rollbacks
- Validates service health

## Configuration

### Environment Variables

Create a `.env` file with production settings:

```bash
# Application
ENVIRONMENT=production
APP_NAME=BlingAuto API
APP_VERSION=1.0.0
DEBUG=false

# Server
WORKERS=4
API_PORT=8000

# Database
POSTGRES_DB=blingauto
POSTGRES_USER=blingauto_user
POSTGRES_PASSWORD=<strong-password-here>
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_PASSWORD=<strong-redis-password>
REDIS_MAX_CONNECTIONS=50

# Security (CHANGE THESE!)
SECRET_KEY=<generate-strong-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (Optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=noreply@example.com
SMTP_PASSWORD=<email-password>
SMTP_FROM_EMAIL=noreply@blingauto.com
FRONTEND_URL=https://blingauto.com

# Initial Admin (Optional - runs once)
INITIAL_ADMIN_EMAIL=admin@blingauto.com
INITIAL_ADMIN_PASSWORD=<strong-admin-password>
INITIAL_ADMIN_FIRST_NAME=Admin
INITIAL_ADMIN_LAST_NAME=User

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=5000

# CORS
CORS_ALLOW_CREDENTIALS=true

# Account Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
PASSWORD_MIN_LENGTH=8
```

### Generate Strong Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate passwords
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment Commands

### Full Deployment

```bash
./scripts/deploy.sh
```

### Manual Step-by-Step

```bash
# 1. Build images
docker-compose build

# 2. Start infrastructure
docker-compose up -d postgres redis

# 3. Run migrations
docker-compose up migrations

# 4. Start API
docker-compose up -d api

# 5. Check status
docker-compose ps
docker-compose logs -f api
```

### Migration-Only Update

```bash
# Rebuild migration container
docker-compose build migrations

# Run migrations
docker-compose up migrations

# Restart API to pick up changes
docker-compose restart api
```

### Code-Only Update (No DB Changes)

```bash
# Build new API image
docker-compose build api

# Rolling restart
docker-compose up -d --no-deps --build api
```

## Monitoring & Health Checks

### Service Health

```bash
# Check all services
docker-compose ps

# Check API health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "version": "1.0.0"
# }
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs migrations
docker-compose logs postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

### Database Status

```bash
# Check current migration version
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "SELECT version_num FROM alembic_version;"

# Check table list
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "\dt"
```

## Rollback Procedures

### Rollback Application Code

```bash
# 1. Stop current API
docker-compose stop api

# 2. Checkout previous version
git checkout <previous-commit-or-tag>

# 3. Rebuild and deploy
docker-compose build api
docker-compose up -d api
```

### Rollback Database Migration

```bash
# 1. Check current version
docker-compose exec api alembic current

# 2. Downgrade to previous version
docker-compose exec api alembic downgrade -1

# Or downgrade to specific version
docker-compose exec api alembic downgrade 002

# 3. Restart API
docker-compose restart api
```

### Restore from Backup

```bash
# 1. Stop API
docker-compose stop api

# 2. Restore database
docker-compose exec -T postgres psql -U blingauto_user -d blingauto \
  < backups/db_backup_YYYYMMDD_HHMMSS.sql

# 3. Restart services
docker-compose restart api
```

## Troubleshooting

### Migration Failures

**Problem**: Migrations fail to apply

**Solution**:
```bash
# Check migration logs
docker-compose logs migrations

# Try manual migration
docker-compose exec api sh -c "cd /app && alembic upgrade head"

# If still failing, check specific migration file
docker-compose exec api alembic current
docker-compose exec api alembic history
```

### API Won't Start

**Problem**: API container keeps restarting

**Solution**:
```bash
# Check API logs
docker-compose logs --tail=50 api

# Common issues:
# 1. Database connection - verify DATABASE_URL
# 2. Missing migrations - run migrations first
# 3. Port conflict - change API_PORT in .env

# Test database connection
docker-compose exec api python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
with engine.connect() as conn:
    conn.execute('SELECT 1')
print('✓ Database connection OK')
"
```

### Database Connection Issues

**Problem**: "could not connect to server"

**Solution**:
```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Test connection from API container
docker-compose exec api sh -c '
  apt-get update && apt-get install -y postgresql-client
  psql $DATABASE_URL -c "SELECT 1"
'
```

### Out of Disk Space

**Problem**: No space left on device

**Solution**:
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove old images
docker image prune -a

# Check disk usage
df -h
docker system df
```

## Performance Tuning

### Database Connection Pool

Adjust in `.env`:
```bash
DATABASE_POOL_SIZE=20      # Base pool size
DATABASE_MAX_OVERFLOW=40   # Extra connections under load
```

### Uvicorn Workers

```bash
# Adjust based on CPU cores
WORKERS=4  # Rule of thumb: (2 x cores) + 1
```

### Redis Connection Pool

```bash
REDIS_MAX_CONNECTIONS=50  # Max concurrent connections
REDIS_TTL=300             # Cache TTL in seconds
```

## Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong SECRET_KEY
- [ ] Configured HTTPS/SSL (via reverse proxy)
- [ ] Set up firewall rules
- [ ] Enabled rate limiting
- [ ] Configured CORS properly
- [ ] Set DEBUG=false
- [ ] Regular database backups configured
- [ ] Monitoring and alerting in place
- [ ] Secrets stored securely (not in git)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/blingauto_api
            git pull
            ./scripts/deploy.sh
```

## Backup Strategy

### Automated Backups

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/blingauto_api && docker-compose exec -T postgres pg_dump -U blingauto_user blingauto | gzip > backups/daily_$(date +\%Y\%m\%d).sql.gz

# Weekly backup (Sunday 3 AM)
0 3 * * 0 cd /opt/blingauto_api && docker-compose exec -T postgres pg_dump -U blingauto_user blingauto | gzip > backups/weekly_$(date +\%Y\%m\%d).sql.gz
```

### Backup Retention

```bash
# Keep last 7 daily backups
find backups/daily_*.sql.gz -mtime +7 -delete

# Keep last 4 weekly backups
find backups/weekly_*.sql.gz -mtime +28 -delete
```

## Scaling

### Horizontal Scaling (Multiple API Instances)

Update `docker-compose.yml`:
```yaml
api:
  deploy:
    replicas: 3  # Run 3 instances
```

### Load Balancer

Add nginx reverse proxy:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - api
```

## Support

- **Documentation**: `/docs` endpoint
- **Health Check**: `/health` endpoint
- **Logs**: `docker-compose logs`
- **Issues**: Check GitHub issues

## Summary

The automated deployment solution provides:

✅ **Zero-downtime deployments** - New code deployed without service interruption
✅ **Automatic migrations** - Database schema updates handled automatically
✅ **Health checks** - Service readiness verified before traffic routing
✅ **Automatic backups** - Database backed up before each deployment
✅ **Rollback support** - Easy revert to previous versions
✅ **Error handling** - Deployment stops on failure with clear error messages

**Production-ready deployment in one command**: `./scripts/deploy.sh`
