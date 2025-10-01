# BlingAuto API - Production Deployment

## 🚀 One-Command Deployment

```bash
./scripts/deploy.sh
```

**That's all you need!** This command automatically:
- ✅ Backs up your database
- ✅ Builds new Docker images
- ✅ Runs database migrations
- ✅ Starts the API with zero downtime
- ✅ Verifies health checks
- ✅ Cleans up old resources

---

## 📋 First-Time Setup (5 Minutes)

### Step 1: Configure Environment

```bash
# Copy template
cp .env.example .env

# Generate strong secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(32))"

# Edit .env and paste the generated values
nano .env
```

**Minimum required changes in `.env`:**
- `SECRET_KEY` - Generate with command above
- `POSTGRES_PASSWORD` - Generate with command above
- `REDIS_PASSWORD` - Generate with command above

### Step 2: Deploy

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy
./scripts/deploy.sh
```

### Step 3: Verify

```bash
# Check health
curl http://localhost:8000/health

# View API documentation
open http://localhost:8000/docs
```

**Expected health response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

---

## 🔄 Deploying Updates

### Deploy Code + Migrations

```bash
# Pull latest code
git pull

# Deploy (migrations run automatically)
./scripts/deploy.sh
```

### Deploy Code Only (No DB Changes)

```bash
docker-compose build api
docker-compose up -d --no-deps api
```

---

## 📊 Monitoring

### Check Service Status

```bash
docker-compose ps
```

### View Logs

```bash
# Live logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Migration logs
docker-compose logs migrations
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 🔧 Common Operations

### Restart Services

```bash
# Restart API only
docker-compose restart api

# Restart all services
docker-compose restart
```

### Stop Services

```bash
docker-compose stop
```

### View Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U blingauto_user -d blingauto

# Check migration version
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "SELECT version_num FROM alembic_version;"
```

### Backup Database

```bash
# Manual backup
docker-compose exec -T postgres pg_dump -U blingauto_user blingauto \
  > backup_$(date +%Y%m%d).sql

# Automatic backups created in ./backups/ during deployment
```

### Restore Database

```bash
# From automatic backup
docker-compose exec -T postgres psql -U blingauto_user blingauto \
  < backups/db_backup_YYYYMMDD_HHMMSS.sql

# From manual backup
docker-compose exec -T postgres psql -U blingauto_user blingauto \
  < backup_20251001.sql
```

---

## 🛡️ Rollback

### Rollback Code

```bash
# Checkout previous version
git checkout <previous-commit>

# Redeploy
./scripts/deploy.sh
```

### Rollback Database Migration

```bash
# Downgrade one migration
docker-compose exec api alembic downgrade -1

# Downgrade to specific version
docker-compose exec api alembic downgrade 002

# Restart API
docker-compose restart api
```

### Full Rollback (Code + Database)

```bash
# 1. Stop API
docker-compose stop api

# 2. Restore database from backup
docker-compose exec -T postgres psql -U blingauto_user blingauto \
  < backups/db_backup_YYYYMMDD_HHMMSS.sql

# 3. Checkout previous code version
git checkout <previous-version>

# 4. Rebuild and start
docker-compose build api
docker-compose up -d api
```

---

## 🆘 Troubleshooting

### Problem: Migrations Failed

```bash
# Check logs
docker-compose logs migrations

# Manual migration
docker-compose exec api alembic upgrade head

# Check current version
docker-compose exec api alembic current
```

### Problem: API Won't Start

```bash
# Check logs
docker-compose logs api

# Common fixes:
# 1. Verify .env file exists and has correct values
# 2. Check DATABASE_URL is correct
# 3. Ensure migrations completed: docker-compose logs migrations
# 4. Check port conflicts: change API_PORT in .env
```

### Problem: Database Connection Failed

```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U blingauto_user -d blingauto -c "SELECT 1;"
```

### Problem: Out of Disk Space

```bash
# Clean up Docker resources
docker system prune -a --volumes

# Check disk usage
df -h
docker system df
```

---

## 📚 Documentation

- **Quick Guide**: [QUICK_DEPLOY_GUIDE.md](QUICK_DEPLOY_GUIDE.md)
- **Full Guide**: [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)
- **Summary**: [PRODUCTION_DEPLOYMENT_SUMMARY.md](PRODUCTION_DEPLOYMENT_SUMMARY.md)
- **Architecture**: [docs/ARCHITECTURE_COMPLIANCE_WASH_BAY_CAPACITY.md](docs/ARCHITECTURE_COMPLIANCE_WASH_BAY_CAPACITY.md)

---

## 🎯 What's Included

### Features

- ✅ **Automated Migrations** - Database schema updates run automatically
- ✅ **Zero Downtime** - New code deployed without service interruption
- ✅ **Health Checks** - Service readiness verified before traffic routing
- ✅ **Auto Backups** - Database backed up before each deployment
- ✅ **Rollback Support** - Easy revert to previous versions
- ✅ **Error Handling** - Clear error messages and automatic rollback on failure

### Recent Addition: Wash Bay Capacity Management

The latest deployment includes the wash bay capacity management feature:

- Multiple clients can book the same time slot (e.g., 10:00 AM)
- Each booking gets a different wash bay automatically
- When all bays are full, new bookings are rejected with a clear error
- Full architecture compliance (no cross-feature imports)

**Test it:**
```bash
# Create wash bays via API
curl -X POST http://localhost:8000/api/v1/facilities/wash-bays \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bay_number": "BAY-001", "max_vehicle_size": "standard", ...}'

# Create concurrent bookings at same time
# Each will get a different bay automatically!
```

---

## 🔒 Security Checklist

Before production deployment:

- [ ] Changed all default passwords in `.env`
- [ ] Generated strong `SECRET_KEY`
- [ ] Set `DEBUG=false`
- [ ] Configured HTTPS (via reverse proxy)
- [ ] Set up firewall rules
- [ ] Configured CORS for your domain
- [ ] Set up automated backups
- [ ] Tested rollback procedure
- [ ] Configured monitoring/alerting
- [ ] Secured `.env` file (not in git)

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| **Deploy** | `./scripts/deploy.sh` |
| **Update** | `git pull && ./scripts/deploy.sh` |
| **Logs** | `docker-compose logs -f api` |
| **Status** | `docker-compose ps` |
| **Health** | `curl http://localhost:8000/health` |
| **Restart** | `docker-compose restart api` |
| **Backup** | Auto-created in `./backups/` during deploy |
| **Rollback** | Restore from `./backups/db_backup_*.sql` |

---

## 📞 Support

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Logs**: `docker-compose logs -f`
- **Issues**: Check deployment logs in `./backups/` folder

---

## Summary

**Production deployment in one command**: `./scripts/deploy.sh`

**Zero-downtime updates**: Code and database migrations handled automatically

**Safe rollbacks**: Database backups created before each deployment

**Everything you need is ready!** 🎉
