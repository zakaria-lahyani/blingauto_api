# BlingAuto Car Wash API

Production-ready FastAPI backend for car wash booking management with automated deployment.

## 🚀 Quick Deploy

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Set passwords and secrets

# 2. Deploy
./scripts/deploy.sh
```

**Done!** API is running at http://localhost:8000

## 📚 Documentation

- **Deployment Guide**: [README_DEPLOYMENT.md](README_DEPLOYMENT.md)
- **Quick Reference**: [QUICK_DEPLOY_GUIDE.md](QUICK_DEPLOY_GUIDE.md)
- **Production Guide**: [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md)
- **Architecture**: [docs/ARCHITECTURE_COMPLIANCE_WASH_BAY_CAPACITY.md](docs/ARCHITECTURE_COMPLIANCE_WASH_BAY_CAPACITY.md)

## ✨ Features

- **Authentication & Authorization** - JWT-based auth with RBAC (Admin, Manager, Washer, Client)
- **Booking Management** - Create, update, cancel bookings with state transitions
- **Wash Bay Capacity** - Automatic bay allocation, concurrent bookings support
- **Service Management** - Categories and services CRUD with pricing
- **Vehicle Management** - Customer vehicle tracking
- **Facility Management** - Wash bays and mobile teams configuration
- **Rate Limiting** - Built-in rate limiting and security features

## 🏗️ Architecture

**Clean Architecture** with strict separation:
- `domain/` - Business entities and policies
- `ports/` - Interface definitions
- `use_cases/` - Application logic
- `adapters/` - External integrations (DB, cache)
- `api/` - HTTP/REST layer

**Tech Stack**:
- FastAPI + Uvicorn
- PostgreSQL + Asyncpg
- Redis
- SQLAlchemy (async)
- Alembic (migrations)
- Docker + Docker Compose

## 📋 API Endpoints

Visit http://localhost:8000/docs for interactive API documentation.

**Core endpoints**:
- `/api/v1/auth/*` - Authentication
- `/api/v1/bookings/*` - Booking management
- `/api/v1/facilities/*` - Wash bays & mobile teams
- `/api/v1/services/*` - Services & categories
- `/api/v1/vehicles/*` - Vehicle management
- `/health` - Health check

## 🔄 Common Operations

```bash
# Deploy updates
git pull && ./scripts/deploy.sh

# View logs
docker-compose logs -f api

# Check status
docker-compose ps

# Restart API
docker-compose restart api

# Backup database
docker-compose exec -T postgres pg_dump -U blingauto_user blingauto > backup.sql

# Rollback
docker-compose exec -T postgres psql -U blingauto_user blingauto < backup.sql
```

## 🧪 Testing

```bash
# Run all tests
docker-compose exec api pytest tests/ -v

# Run specific test file
docker-compose exec api pytest tests/test_wash_bay_capacity.py -v

# Run with coverage
docker-compose exec api pytest --cov=app tests/
```

## 📊 Monitoring

```bash
# Health check
curl http://localhost:8000/health

# Service status
docker-compose ps

# Database migration version
docker-compose exec postgres psql -U blingauto_user -d blingauto \
  -c "SELECT version_num FROM alembic_version;"
```

## 🔒 Security

- Non-root Docker user
- JWT token authentication
- Password hashing (bcrypt)
- Rate limiting
- Account lockout protection
- Input validation
- SQL injection prevention
- XSS protection

## 📦 Project Structure

```
blingauto_api/
├── app/
│   ├── core/              # Core infrastructure
│   ├── features/          # Feature modules
│   │   ├── auth/          # Authentication
│   │   ├── bookings/      # Booking management
│   │   ├── facilities/    # Wash bays & teams
│   │   ├── services/      # Services & categories
│   │   └── vehicles/      # Vehicle management
│   └── shared/            # Shared utilities
├── migrations/            # Database migrations
├── scripts/               # Deployment scripts
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## 🤝 Contributing

1. Follow clean architecture principles
2. Write tests for new features
3. Update documentation
4. Run tests before committing
5. Use conventional commits

## 📄 License

MIT License

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Health**: `/health` endpoint
- **Logs**: `docker-compose logs -f api`

---

**Built with Clean Architecture** | **Production Ready** | **Zero-Downtime Deployments**
