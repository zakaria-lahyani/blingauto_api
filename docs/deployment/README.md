# Deployment Guide

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Database Configuration](#database-configuration)
3. [Redis Configuration](#redis-configuration)
4. [Environment Variables](#environment-variables)
5. [Production Deployment](#production-deployment)
6. [Docker Deployment](#docker-deployment)
7. [NGINX Configuration](#nginx-configuration)

---

## Environment Setup

### Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 6 or higher
- **NGINX**: 1.20+ (production)
- **Docker**: 20.10+ (optional)

### Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Database Configuration

### PostgreSQL Setup

```bash
# Create database
createdb blingauto_db

# Create user
psql -c "CREATE USER blingauto_user WITH PASSWORD 'your_secure_password';"

# Grant permissions
psql -c "GRANT ALL PRIVILEGES ON DATABASE blingauto_db TO blingauto_user;"
```

### Run Migrations

```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "Description"
```

### Seed Initial Data

```bash
# Run seed script
python -m app.migrations.seeds.initial_data

# This creates:
# - Default categories
# - Sample services
# - Admin user (if configured)
```

---

## Redis Configuration

### Redis Setup

```bash
# Start Redis (Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally (Ubuntu)
sudo apt-get install redis-server
sudo systemctl start redis
```

### Redis Configuration

```conf
# /etc/redis/redis.conf

# Bind to localhost
bind 127.0.0.1

# Set password
requirepass your_redis_password

# Max memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
```

---

## Environment Variables

### Create .env file

```bash
cp .env.example .env
```

### Required Variables

```env
# Environment
ENVIRONMENT=production  # development, staging, production
DEBUG=False

# Application
APP_NAME=BlingAuto API
APP_VERSION=1.0.0

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://blingauto_user:password@localhost:5432/blingauto_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=False

# Redis
REDIS_URL=redis://:password@localhost:6379/0
REDIS_MAX_CONNECTIONS=10
REDIS_TTL=300

# Security
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@blingauto.com
SMTP_FROM_NAME=BlingAuto
SMTP_USE_TLS=True

# Frontend
FRONTEND_URL=https://app.blingauto.com

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# CORS
CORS_ORIGINS=https://app.blingauto.com,https://admin.blingauto.com
CORS_ALLOW_CREDENTIALS=True

# Logging
LOG_LEVEL=INFO
```

### Generate Secret Key

```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Production Deployment

### Using Uvicorn + Gunicorn

```bash
# Install production server
pip install gunicorn uvicorn[standard]

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

### Systemd Service

Create `/etc/systemd/system/blingauto-api.service`:

```ini
[Unit]
Description=BlingAuto API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=blingauto
Group=blingauto
WorkingDirectory=/var/www/blingauto-api
Environment="PATH=/var/www/blingauto-api/.venv/bin"
ExecStart=/var/www/blingauto-api/.venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable blingauto-api
sudo systemctl start blingauto-api
sudo systemctl status blingauto-api
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final image
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY app/ ./app/
COPY alembic.ini .
COPY .env .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/blingauto
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: blingauto_db
      POSTGRES_USER: blingauto_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass redis_password
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Build and Run

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

## NGINX Configuration

### nginx.conf

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    '$request_time';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=10r/m;

    # Upstream
    upstream api_backend {
        server api:8000;
    }

    server {
        listen 80;
        server_name api.blingauto.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.blingauto.com;

        # SSL certificates
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'" always;

        # Max body size
        client_max_body_size 10M;

        # Health check (no rate limit)
        location /health {
            proxy_pass http://api_backend;
            access_log off;
        }

        # Auth endpoints (strict rate limit)
        location /api/v1/auth {
            limit_req zone=auth_limit burst=5 nodelay;
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }

        # API endpoints (standard rate limit)
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }

        # Docs (no rate limit)
        location /docs {
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }

        location /redoc {
            proxy_pass http://api_backend;
            include /etc/nginx/proxy_params;
        }
    }
}
```

### proxy_params

```nginx
# /etc/nginx/proxy_params
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_redirect off;
proxy_buffering off;
proxy_request_buffering off;
```

---

## Monitoring

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2025-10-01T14:30:00Z"
}

# Readiness check
curl http://localhost:8000/health/ready

# Response
{
  "status": "ready",
  "database": "connected",
  "redis": "connected"
}
```

### Logs

```bash
# View logs
journalctl -u blingauto-api -f

# Docker logs
docker-compose logs -f api

# NGINX logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup
pg_dump -U blingauto_user -h localhost blingauto_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U blingauto_user -h localhost blingauto_db < backup_20251001.sql
```

### Automated Backups

```bash
# Cron job (daily at 2 AM)
0 2 * * * /usr/local/bin/backup-db.sh
```

### backup-db.sh

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/blingauto"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U blingauto_user blingauto_db | gzip > $BACKUP_DIR/backup_$DATE.sql.gz
# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

---

## Troubleshooting

### Common Issues

#### Can't connect to database
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U blingauto_user -h localhost -d blingauto_db

# Check DATABASE_URL in .env
```

#### Can't connect to Redis
```bash
# Check Redis is running
sudo systemctl status redis

# Test connection
redis-cli -a your_password ping
```

#### API returns 500 errors
```bash
# Check logs
journalctl -u blingauto-api -n 100

# Check environment variables
systemctl show blingauto-api --property=Environment
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate new SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review CORS settings
- [ ] Update dependencies
- [ ] Set up log rotation

---

**Last Updated**: 2025-10-01
