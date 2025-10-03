# Stopper et supprimer tous les conteneurs
docker stop $(docker ps -aq) 
docker rm -f $(docker ps -aq) 

# Supprimer toutes les images
docker rmi -f $(docker images -q) 

# Supprimer tous les volumes
docker volume rm $(docker volume ls -q) 

# Nettoyer tout le reste (dangling, networks orphelins…)
docker system prune -af --volumes

# Rebuild et lancer via docker-compose
docker-compose -f docker-compose.yml build --no-cache
docker-compose -f docker-compose.yml up -d  
docker-compose exec api python scripts/seed_test_users.py


cd /c/Users/zak/Desktop/workspace/project/lavage/api/blingauto_api/postman/scripts && powershell -ExecutionPolicy Bypass -File ./check-and-verify-users.ps1

docker exec blingauto-postgres psql -U blingauto_user -d blingauto -c "SELECT u.id, u.email, u.first_name, u.last_name, u.is_email_verified, u.created_at as user_created_at, evt.token, evt.created_at as token_created_at, evt.expires_at, evt.is_used FROM users u LEFT JOIN email_verification_tokens evt ON u.email = evt.email WHERE u.is_email_verified = FALSE ORDER BY u.created_at DESC;"

docker exec blingauto-postgres psql -U blingauto_user -d blingauto -c "SELECT u.id, u.email, u.first_name, u.last_name, u.is_email_verified, u.created_at as user_created_at, evt.token, evt.created_at as token_created_at, evt.expires_at, evt.used FROM users u LEFT JOIN email_verification_tokens evt ON u.email = evt.email WHERE u.is_email_verified = FALSE ORDER BY u.created_at DESC;"


# BlingAuto Car Wash Management API

A production-ready, enterprise-grade car wash management system built with **Clean Architecture** principles, featuring comprehensive booking management, scheduling, inventory tracking, and business analytics.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

BlingAuto API is a comprehensive backend system for managing all aspects of a car wash business, from customer bookings and service management to staff scheduling, inventory control, and financial reporting. Built with scalability, maintainability, and security as core principles.

### Key Features

- ✅ **Complete Booking Lifecycle** - From creation to completion with real-time status tracking
- ✅ **Multi-Location Support** - In-facility wash bays and mobile teams
- ✅ **Smart Scheduling** - Automated capacity management and availability checking
- ✅ **Role-Based Access Control** - 4 user roles with granular permissions
- ✅ **Inventory Management** - Product tracking, stock movements, and alerts
- ✅ **Expense Tracking** - Budget management and financial reporting
- ✅ **Staff Management** - Attendance, scheduling, and document management
- ✅ **Walk-in Services** - Quick service registration for on-demand customers
- ✅ **Analytics & Reporting** - Business insights and performance metrics
- ✅ **Production-Ready** - Docker deployment with auto-migrations and health checks

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture Guide](docs/architecture/README.md) | Clean Architecture implementation and design patterns |
| [API Reference](docs/api/README.md) | Complete endpoint documentation with examples |
| [Business Rules](docs/rules/) | Comprehensive business logic and validation rules |
| [Deployment Guide](DEPLOYMENT.md) | Production deployment with Docker Compose |
| [ADRs](docs/ADRs/README.md) | Architectural Decision Records |

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **PostgreSQL 14+** (if not using Docker)
- **Redis 6+** (if not using Docker)

### One-Command Deployment

```bash
# Clone the repository
git clone <repository-url>
cd blingauto_api

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings (required: SECRET_KEY, DATABASE_URL, REDIS_URL)

# Start all services with Docker Compose
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

**That's it!** The system will automatically:
- ✅ Create the PostgreSQL database with required extensions
- ✅ Run all migrations to set up the schema
- ✅ Create a default admin user (if configured)
- ✅ Start the API server on port 8000

### Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Base URL**: http://localhost:8000/api/v1

### Default Admin User

If you set the following environment variables in `.env`, a default admin will be created:

```env
INITIAL_ADMIN_EMAIL=admin@blingauto.com
INITIAL_ADMIN_PASSWORD=YourSecurePassword123!
INITIAL_ADMIN_FIRST_NAME=Admin
INITIAL_ADMIN_LAST_NAME=User
```

## 🏗️ Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│        API Layer (FastAPI)          │  ← HTTP I/O
├─────────────────────────────────────┤
│         Use Cases Layer             │  ← Application Logic
├─────────────────────────────────────┤
│         Domain Layer                │  ← Business Rules (Pure Python)
├─────────────────────────────────────┤
│         Ports (Interfaces)          │  ← Abstractions
├─────────────────────────────────────┤
│    Adapters (Implementations)       │  ← Technical Details
└─────────────────────────────────────┘
```

**Dependency Rule**: Inner layers have NO knowledge of outer layers.

### Feature Structure

Each feature is **completely isolated** with its own:

```
features/<feature>/
├── domain/              # Pure business logic (entities, policies)
│   ├── entities.py
│   └── policies.py
├── ports/               # Interface definitions
│   ├── repositories.py
│   └── services.py
├── use_cases/           # Application orchestration
│   ├── create_*.py
│   ├── update_*.py
│   └── ...
├── adapters/            # Technical implementations
│   ├── models.py        # SQLAlchemy models
│   ├── repositories.py  # Repository implementations
│   └── external_*.py    # External service adapters
├── api/                 # HTTP layer
│   ├── router.py        # FastAPI routes
│   ├── schemas.py       # Pydantic models
│   └── dependencies.py  # Dependency injection
└── tests/               # All test levels
    ├── unit/
    ├── integration/
    └── e2e/
```

## 🎯 Features

### 1. Authentication & Authorization

- **JWT-based authentication** with access & refresh tokens
- **Role-Based Access Control (RBAC)**: Admin, Manager, Washer, Client
- **Email verification** with secure token generation
- **Password reset** flow with time-limited tokens
- **Account lockout** after 5 failed login attempts
- **Token rotation** for enhanced security

**API Endpoints**: `/api/v1/auth/*`

### 2. Booking Management

Complete booking lifecycle with state machine:

```
PENDING → CONFIRMED → IN_PROGRESS → COMPLETED
   ↓           ↓            ↓
CANCELLED  CANCELLED   NO_SHOW
```

**Features**:
- Create bookings with multiple services (1-10 services)
- Real-time availability checking
- Service modification (add/remove)
- Rescheduling with minimum notice requirements
- Cancellation with time-based fees
- Quality rating system (1-5 stars)
- No-show handling with penalties

**API Endpoints**: `/api/v1/bookings/*`

**Business Rules**:
- Maximum 90 days advance booking
- Minimum 2 hours notice for rescheduling
- Cancellation fees: 50% (24h notice) / 100% (<24h notice)
- Total duration: 30-240 minutes per booking

### 3. Service Catalog

- **Hierarchical categories** with display ordering
- **Service pricing** with decimal precision
- **Duration tracking** in minutes
- **Popular service** marking and filtering
- **Active/Inactive** status management
- **Service search** with caching

**API Endpoints**: `/api/v1/services/*`

### 4. Vehicle Management

- **Customer vehicle registry** with make, model, year, color
- **License plate** tracking with uniqueness
- **Default vehicle** selection per customer
- **Soft delete** support with history preservation

**API Endpoints**: `/api/v1/vehicles/*`

### 5. Pricing Engine

- **Dynamic price calculation** for service bundles
- **Quote validation** against service catalog
- **Cancellation fee calculation** based on timing
- **Overtime charges** for bookings exceeding estimated duration

**API Endpoints**: `/api/v1/pricing/*`

### 6. Facility Management

**Wash Bays**:
- Bay capacity and availability tracking
- Vehicle size constraints
- Status management (AVAILABLE, OCCUPIED, MAINTENANCE, CLOSED)

**Mobile Teams**:
- Team assignment and scheduling
- Service radius enforcement
- GPS location tracking

**API Endpoints**: `/api/v1/facilities/*`

### 7. Staff Management

- **Staff profiles** with roles and shift schedules
- **Attendance tracking** with check-in/check-out
- **Document management** (certifications, licenses)
- **Work schedules** with day/shift assignments
- **File storage** for staff documents

**API Endpoints**: `/api/v1/staff/*`

### 8. Walk-in Services

- **Quick registration** for on-demand customers
- **Vehicle tracking** for walk-in bookings
- **Payment processing** integration
- **Service completion** workflow

**API Endpoints**: `/api/v1/walkins/*`

### 9. Inventory Management

- **Product catalog** with SKU tracking
- **Stock level monitoring** with min/max thresholds
- **Stock movements** (IN, OUT, ADJUSTMENT, TRANSFER)
- **Reorder alerts** based on reorder points
- **Supplier management**

**API Endpoints**: `/api/v1/inventory/*`

### 10. Expense Management

- **Expense tracking** by category (OPERATIONAL, SALARY, MAINTENANCE, UTILITIES, SUPPLIES, MARKETING, OTHER)
- **Budget management** with monthly/yearly periods
- **Approval workflow** (PENDING → APPROVED → PAID)
- **Payment method** tracking
- **Monthly summaries** and reporting

**API Endpoints**: `/api/v1/expenses/*`

### 11. Analytics & Reporting

- **Revenue tracking** by period
- **Booking statistics** (completion rate, average rating)
- **Popular services** analysis
- **Staff performance** metrics
- **Inventory turnover** reporting
- **Expense analysis** by category

**API Endpoints**: `/api/v1/analytics/*`

## 🔒 Security Features

- **Password Hashing**: Argon2 (OWASP recommended)
- **JWT Tokens**: RS256 signing with rotation
- **Rate Limiting**: Configurable per-endpoint limits
- **CORS**: Configurable origin whitelist
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Input Validation**: Pydantic schemas with strict validation
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Progressive Account Lockout**: Increasing duration with repeated violations

## 📊 Business Rules Implementation

All business rules are implemented in the **domain layer** with zero framework dependencies:

### Authentication Rules (RG-AUTH-*)

- **RG-AUTH-001**: Email uniqueness and format validation
- **RG-AUTH-002**: Password complexity (min 8 chars, max 128)
- **RG-AUTH-003**: Name validation and normalization
- **RG-AUTH-006**: Account lockout after 5 failed attempts
- **RG-AUTH-007**: Email verification required for activation
- **RG-AUTH-009**: RBAC hierarchy (Admin > Manager > Washer > Client)

### Booking Rules (RG-BOK-*)

- **RG-BOK-001**: 1-10 services per booking
- **RG-BOK-002**: Total duration 30-240 minutes
- **RG-BOK-003**: Max booking price $10,000
- **RG-BOK-004**: Cannot schedule in the past
- **RG-BOK-005**: Max 90 days advance booking
- **RG-BOK-006**: State machine enforcement
- **RG-BOK-007**: Minimum 2 hours notice for changes
- **RG-BOK-008**: Cancellation fee calculation
- **RG-BOK-010**: Rating 1-5 stars, once per booking

### Service Rules (RG-SVC-*)

- **RG-SVC-003**: Service name uniqueness per category
- **RG-SVC-004**: Price must be positive (> 0)
- **RG-SVC-005**: Duration must be positive (> 0)
- **RG-SVC-006**: Max 5 popular services per category

### Vehicle Rules (RG-VEH-*)

- **RG-VEH-001**: Make validation (2-50 chars)
- **RG-VEH-002**: Model validation (1-50 chars)
- **RG-VEH-003**: Year validation (1900 - current+2)
- **RG-VEH-006**: One default vehicle per customer
- **RG-VEH-007**: Soft delete with history preservation

### Facility Rules (RG-FAC-*)

- **RG-FAC-001**: Wash bay capacity management
- **RG-FAC-002**: Vehicle size constraints
- **RG-FAC-003**: Mobile team soft delete only
- **RG-FAC-004**: Service radius enforcement (50km)

### Scheduling Rules (RG-SCH-*)

- **RG-SCH-001**: Business hours enforcement
- **RG-SCH-002**: Minimum 1-hour advance booking
- **RG-SCH-003**: 15-minute time slot increments

See [Business Rules Documentation](docs/rules/) for complete reference.

## 🛠️ Technology Stack

### Core Framework
- **FastAPI 0.104+** - Modern async web framework
- **Python 3.11+** - Latest Python with type hints
- **Pydantic 2.x** - Data validation and settings
- **Uvicorn** - ASGI server

### Database & Caching
- **PostgreSQL 14+** - Primary database with JSONB support
- **SQLAlchemy 2.x** - Async ORM with relationship loading
- **Alembic** - Database migrations
- **Redis 6+** - Caching and session storage

### Authentication & Security
- **python-jose** - JWT token handling
- **passlib** - Password hashing (Argon2)
- **python-multipart** - File upload support

### Development & Testing
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage
- **black** - Code formatting
- **ruff** - Fast linting
- **mypy** - Static type checking

### Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **NGINX** - Reverse proxy (optional)

## 📁 Project Structure

```
blingauto_api/
├── app/
│   ├── core/                    # Core infrastructure
│   │   ├── config/              # Settings management
│   │   ├── db/                  # Database session & models
│   │   ├── cache/               # Redis client
│   │   ├── security/            # JWT, password hashing
│   │   ├── middleware/          # Request processing
│   │   └── errors/              # Error handling
│   ├── features/                # Feature modules (Clean Architecture)
│   │   ├── auth/                # Authentication & authorization
│   │   ├── bookings/            # Booking management
│   │   ├── services/            # Service catalog
│   │   ├── vehicles/            # Vehicle registry
│   │   ├── pricing/             # Pricing engine
│   │   ├── facilities/          # Wash bays & mobile teams
│   │   ├── staff/               # Staff management
│   │   ├── walkins/             # Walk-in services
│   │   ├── inventory/           # Inventory tracking
│   │   ├── expenses/            # Expense management
│   │   └── analytics/           # Reporting & analytics
│   ├── shared/                  # Shared utilities
│   │   ├── auth.py              # Auth dependencies
│   │   └── pagination.py        # Pagination helpers
│   └── interfaces/              # API interfaces
│       ├── http_api.py          # FastAPI app factory
│       └── health.py            # Health check endpoints
├── migrations/                  # Alembic migrations
├── scripts/                     # Deployment scripts
│   ├── docker-entrypoint-api.sh
│   ├── docker-entrypoint-migrations.sh
│   ├── create_default_admin.py
│   └── init-db.sql
├── docs/                        # Documentation
├── tests/                       # Test suites
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # API container
├── alembic.ini                  # Migration config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test suites
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests
pytest tests/e2e/                     # End-to-end tests

# Run tests for specific feature
pytest tests/unit/test_auth.py

# Generate coverage report
pytest --cov=app --cov-report=term-missing
```

## 🔧 Development Setup

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with local settings

# Start PostgreSQL and Redis (required)
# Then run migrations
alembic upgrade head

# Create admin user
python scripts/create_default_admin.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Key configuration variables (see `.env.example` for complete list):

```env
# Application
APP_NAME=BlingAuto API
APP_VERSION=1.0.0
ENVIRONMENT=development

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/blingauto
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Initial Admin User
INITIAL_ADMIN_EMAIL=admin@blingauto.com
INITIAL_ADMIN_PASSWORD=SecurePassword123!
```

## 🚢 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive production deployment guide.

### Quick Production Checklist

- [ ] Set strong `SECRET_KEY` (32+ random characters)
- [ ] Configure production database URL
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure CORS origins whitelist
- [ ] Enable rate limiting
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (NGINX)
- [ ] Set up database backups
- [ ] Configure monitoring and logging
- [ ] Review security headers
- [ ] Set up health check monitoring

### Docker Production Deployment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3

# Stop services
docker-compose down
```

## 📈 Performance & Scalability

- **Async I/O**: Full async/await throughout the stack
- **Connection Pooling**: SQLAlchemy async pool with configurable size
- **Query Optimization**: Eager loading with `selectinload` to prevent N+1
- **Caching**: Redis caching for frequent queries
- **Pagination**: Cursor-based pagination for large datasets
- **Rate Limiting**: Protect against abuse and DoS
- **Horizontal Scaling**: Stateless API design allows multiple instances

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Follow Clean Architecture** - respect layer boundaries
4. **Write tests** - minimum 80% coverage for new code
5. **Follow code style** - run `black` and `ruff`
6. **Update documentation** - keep docs in sync with changes
7. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
8. **Push** to your branch (`git push origin feature/amazing-feature`)
9. Open a **Pull Request**

### Code Style

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type check
mypy app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent async framework
- SQLAlchemy team for the powerful ORM
- Clean Architecture community for design principles
- All contributors to this project

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Email**: support@blingauto.com

---

**Built with ❤️ using Clean Architecture principles**

**Version**: 1.0.0 | **Status**: Production Ready ✅ | **Last Updated**: 2025-10-02
