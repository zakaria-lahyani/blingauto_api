# BlingAuto API - Quick Deployment Guide

## 🚀 One-Command Deployment

```bash
./scripts/deploy.sh
```

That's it! This single command handles everything:
- ✅ Database backups
- ✅ Image building
- ✅ Zero-downtime migration
- ✅ Automatic rollback on failure
- ✅ Health checks

---

## 📋 First-Time Setup (5 Minutes)

### 1. Configure Environment

```bash
# Create environment file
cat > .env << 'EOF'
# Database
POSTGRES_PASSWORD=<generate-strong-password>

# Redis
REDIS_PASSWORD=<generate-strong-password>

# Security
SECRET_KEY=<generate-secret-key>

# Optional: Initial Admin
INITIAL_ADMIN_EMAIL=admin@blingauto.com
INITIAL_ADMIN_PASSWORD=<admin-password>
EOF
```

**Generate secure values:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Deploy

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### 3. Verify

```bash
# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

---

## 🔄 Common Operations

### Deploy Updates
```bash
git pull
./scripts/deploy.sh
```

### View Logs
```bash
docker-compose logs -f api
```

### Check Status
```bash
docker-compose ps
```

### Restart API
```bash
docker-compose restart api
```

### Database Backup
```bash
docker-compose exec -T postgres pg_dump -U blingauto_user blingauto > backup_$(date +%Y%m%d).sql
```

### Rollback
```bash
# Restore from backup
docker-compose exec -T postgres psql -U blingauto_user blingauto < backup.sql

# Or downgrade migration
docker-compose exec api alembic downgrade -1
```

---

## 🏗️ How It Works

### Deployment Flow

```
1. Backup Database
   ↓
2. Build New Images
   ↓
3. Run Migrations (isolated)
   ↓
4. Start API (waits for migrations)
   ↓
5. Health Checks
   ↓
6. Success!
```

### Automatic Features

**Migration Runner**:
- Waits for database readiness (auto-retry)
- Applies Alembic migrations
- Verifies success
- Exits with status code

**API Startup**:
- Waits for database
- Waits for migrations
- Creates initial admin (if configured)
- Starts Uvicorn with health checks

**Deploy Script**:
- Backs up database before changes
- Builds new images
- Zero-downtime deployment
- Automatic rollback on failure
- Post-deployment verification

---

## 🔧 Troubleshooting

### Migration Failed?
```bash
# Check logs
docker-compose logs migrations

# Manual migration
docker-compose exec api alembic upgrade head
```

### API Won't Start?
```bash
# Check logs
docker-compose logs api

# Common fixes:
# 1. Verify DATABASE_URL in .env
# 2. Ensure migrations ran: docker-compose up migrations
# 3. Check port conflicts: change API_PORT in .env
```

### Database Connection Issues?
```bash
# Check postgres
docker-compose ps postgres
docker-compose logs postgres

# Test connection
docker-compose exec api python -c "
from sqlalchemy import create_engine; import os
engine = create_engine(os.getenv('DATABASE_URL').replace('+asyncpg', ''))
engine.connect(); print('✓ Connected')
"
```

---

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health

# Expected:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected"
# }
```

### Service Status
```bash
docker-compose ps

# All services should show "Up (healthy)"
```

### Database Version
```bash
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "SELECT version_num FROM alembic_version;"
```

---

## 🎯 Production Checklist

Before going live:

- [ ] Changed default passwords in `.env`
- [ ] Generated strong `SECRET_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configured HTTPS (via reverse proxy)
- [ ] Set up firewall rules
- [ ] Configured automated backups
- [ ] Tested rollback procedure
- [ ] Set up monitoring/alerting
- [ ] Documented access credentials (securely)

---

## 📚 Advanced Topics

See [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for:
- CI/CD integration
- Horizontal scaling
- Load balancing
- Performance tuning
- Security hardening
- Backup strategies

---

## 🆘 Support

- **Health**: http://localhost:8000/health
- **Docs**: http://localhost:8000/docs
- **Logs**: `docker-compose logs -f api`
- **Full Guide**: [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)

---

## Summary

**Deploy**: `./scripts/deploy.sh`

**Update**: `git pull && ./scripts/deploy.sh`

**Rollback**: Restore from `backups/db_backup_*.sql`

**That's it!** 🎉
