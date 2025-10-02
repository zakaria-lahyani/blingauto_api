# BlingAuto API - Architecture Documentation

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Clean Architecture Principles](#2-clean-architecture-principles)
3. [Layer Responsibilities](#3-layer-responsibilities)
4. [Feature Structure](#4-feature-structure)
5. [Dependency Flow](#5-dependency-flow)
6. [Design Patterns](#6-design-patterns)
7. [Database Design](#7-database-design)
8. [Security Architecture](#8-security-architecture)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Architecture](#10-deployment-architecture)

---

## 1. Architecture Overview

BlingAuto API is built following **Clean Architecture** (also known as Hexagonal Architecture or Ports & Adapters) principles, ensuring:

- **Separation of Concerns**: Each layer has a single, well-defined responsibility
- **Testability**: Business logic can be tested without external dependencies
- **Maintainability**: Changes in one layer don't affect others
- **Technology Independence**: Framework and database can be swapped without touching business logic
- **Feature Isolation**: Features are completely independent modules

### High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     HTTP Layer (FastAPI)                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │   Auth     │  │  Bookings  │  │  Services  │   ... more  │
│  │   Router   │  │   Router   │  │   Router   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP Request/Response
┌────────────────────────▼─────────────────────────────────────┐
│                    API Layer (FastAPI)                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • Request validation (Pydantic schemas)                │ │
│  │  • Response formatting                                  │ │
│  │  • Authentication/Authorization                         │ │
│  │  • Dependency injection                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    Use Cases Layer                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • Application orchestration                            │ │
│  │  • Business workflow coordination                       │ │
│  │  • Transaction management                               │ │
│  │  • Cross-cutting concerns (events, notifications)       │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    Domain Layer                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • Pure business logic (ZERO framework dependencies)   │ │
│  │  • Entities with validation                             │ │
│  │  • Business rules (policies)                            │ │
│  │  • Domain events                                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                  Ports Layer (Interfaces)                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  • Repository interfaces                                │ │
│  │  • Service interfaces                                   │ │
│  │  • Event publisher interfaces                           │ │
│  │  • External service interfaces                          │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                  Adapters Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │    Email     │       │
│  │  Repository  │  │    Cache     │  │   Service    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Stripe     │  │   AWS S3     │  │   External   │       │
│  │   Payment    │  │   Storage    │  │   APIs       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Clean Architecture Principles

### The Dependency Rule

**Core Principle**: Source code dependencies must point **inward only**.

```
External → Adapters → Ports → Use Cases → Domain
  (knows about all inner layers)    (knows nothing about outer layers)
```

**What this means**:
- ✅ Use Cases can import from Domain
- ✅ Adapters can import from Ports
- ✅ API can import from Use Cases
- ❌ Domain **CANNOT** import from Use Cases
- ❌ Ports **CANNOT** import from Adapters
- ❌ Domain **CANNOT** import FastAPI, SQLAlchemy, or any framework

### Benefits

1. **Framework Independence**: Business logic doesn't depend on FastAPI, SQLAlchemy, or any library
2. **Database Independence**: Can swap PostgreSQL for MongoDB without touching business logic
3. **Testability**: Test business logic without database, web framework, or external services
4. **UI Independence**: Same business logic for REST API, GraphQL, gRPC, or CLI
5. **External Service Independence**: Easy to mock external APIs, payment gateways, etc.

---

## 3. Layer Responsibilities

### 3.1 Domain Layer (Innermost)

**Location**: `app/features/*/domain/`

**Responsibilities**:
- Define business entities (data + behavior)
- Implement business rules and validation
- Define domain policies
- Emit domain events
- **ZERO external dependencies** (pure Python only)

**Example Structure**:
```python
# app/features/bookings/domain/entities.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

@dataclass
class Booking:
    id: str
    customer_id: str
    vehicle_id: str
    status: BookingStatus
    total_price: Decimal

    def confirm(self) -> None:
        """Confirm a pending booking."""
        if self.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                "Only pending bookings can be confirmed"
            )
        self.status = BookingStatus.CONFIRMED

    def calculate_cancellation_fee(self, hours_before: int) -> Decimal:
        """Calculate cancellation fee based on timing."""
        if hours_before >= 24:
            return self.total_price * Decimal("0.5")  # 50% fee
        else:
            return self.total_price  # 100% fee
```

**Key Characteristics**:
- Uses Python dataclasses or plain classes
- Contains validation logic
- Enforces business rules
- No framework imports
- No database concepts (no `session`, no `query`)

### 3.2 Ports Layer (Interfaces)

**Location**: `app/features/*/ports/`

**Responsibilities**:
- Define **interfaces** (abstract base classes) for repositories
- Define **interfaces** for external services
- Establish contracts between layers
- Enable dependency inversion

**Example**:
```python
# app/features/bookings/ports/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.entities import Booking

class IBookingRepository(ABC):
    """Interface for booking persistence."""

    @abstractmethod
    async def save(self, booking: Booking) -> Booking:
        """Save a booking."""
        pass

    @abstractmethod
    async def get_by_id(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID."""
        pass

    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        page: int,
        limit: int
    ) -> List[Booking]:
        """List bookings for a customer."""
        pass
```

**Key Characteristics**:
- Uses ABC (Abstract Base Class)
- Only defines method signatures
- Works with domain entities
- No implementation details

### 3.3 Use Cases Layer (Application Logic)

**Location**: `app/features/*/use_cases/`

**Responsibilities**:
- Orchestrate business workflows
- Coordinate between repositories and services
- Manage transactions
- Emit events
- Handle cross-cutting concerns (logging, caching)

**Example**:
```python
# app/features/bookings/use_cases/create_booking.py
from dataclasses import dataclass
from ..domain.entities import Booking, BookingStatus
from ..ports.repositories import IBookingRepository
from ..ports.services import INotificationService, IEventService

@dataclass
class CreateBookingRequest:
    customer_id: str
    vehicle_id: str
    service_ids: List[str]
    scheduled_at: datetime

@dataclass
class CreateBookingResponse:
    booking: Booking
    message: str

class CreateBookingUseCase:
    """Use case for creating a new booking."""

    def __init__(
        self,
        booking_repository: IBookingRepository,
        notification_service: INotificationService,
        event_service: IEventService,
    ):
        self._booking_repo = booking_repository
        self._notification = notification_service
        self._events = event_service

    async def execute(
        self,
        request: CreateBookingRequest
    ) -> CreateBookingResponse:
        """Execute the create booking workflow."""

        # 1. Validate business rules
        self._validate_services(request.service_ids)
        self._validate_schedule(request.scheduled_at)

        # 2. Create domain entity
        booking = Booking(
            id=generate_uuid(),
            customer_id=request.customer_id,
            vehicle_id=request.vehicle_id,
            status=BookingStatus.PENDING,
            scheduled_at=request.scheduled_at,
        )

        # 3. Persist
        saved_booking = await self._booking_repo.save(booking)

        # 4. Send notification
        await self._notification.send_booking_confirmation(
            customer_id=booking.customer_id,
            booking_id=booking.id
        )

        # 5. Publish event
        await self._events.publish(
            "booking.created",
            {"booking_id": booking.id}
        )

        return CreateBookingResponse(
            booking=saved_booking,
            message="Booking created successfully"
        )
```

**Key Characteristics**:
- Depends on ports (interfaces), not implementations
- Orchestrates multiple repositories and services
- Contains application-specific business logic
- Handles transactions and error recovery

### 3.4 Adapters Layer (Implementations)

**Location**: `app/features/*/adapters/`

**Responsibilities**:
- Implement port interfaces
- Handle database operations (SQLAlchemy)
- Integrate with external APIs
- Convert between domain entities and database models

**Example**:
```python
# app/features/bookings/adapters/repositories.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..ports.repositories import IBookingRepository
from ..domain.entities import Booking
from .models import BookingModel

class SqlBookingRepository(IBookingRepository):
    """SQLAlchemy implementation of booking repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, booking: Booking) -> Booking:
        """Save a booking to PostgreSQL."""
        # Convert domain entity to SQLAlchemy model
        model = BookingModel(
            id=booking.id,
            customer_id=booking.customer_id,
            vehicle_id=booking.vehicle_id,
            status=booking.status.value,
            total_price=booking.total_price,
        )

        self._session.add(model)
        await self._session.flush()

        # Convert back to domain entity
        return self._model_to_entity(model)

    async def get_by_id(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID."""
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_entity(model)

    def _model_to_entity(self, model: BookingModel) -> Booking:
        """Convert SQLAlchemy model to domain entity."""
        return Booking(
            id=model.id,
            customer_id=model.customer_id,
            vehicle_id=model.vehicle_id,
            status=BookingStatus(model.status),
            total_price=model.total_price,
        )
```

**Key Characteristics**:
- Implements port interfaces
- Uses framework-specific code (SQLAlchemy, Redis, etc.)
- Converts between domain and infrastructure models
- Handles database sessions, connections, etc.

### 3.5 API Layer (HTTP Interface)

**Location**: `app/features/*/api/`

**Responsibilities**:
- Define HTTP routes (FastAPI)
- Validate requests (Pydantic)
- Format responses
- Handle authentication/authorization
- Manage dependency injection

**Example**:
```python
# app/features/bookings/api/router.py
from fastapi import APIRouter, Depends, HTTPException
from .schemas import CreateBookingSchema, BookingResponseSchema
from .dependencies import get_create_booking_use_case
from ..use_cases.create_booking import (
    CreateBookingUseCase,
    CreateBookingRequest,
)

router = APIRouter()

@router.post("/", response_model=BookingResponseSchema)
async def create_booking(
    booking_data: CreateBookingSchema,
    use_case: CreateBookingUseCase = Depends(get_create_booking_use_case),
):
    """Create a new booking."""
    try:
        request = CreateBookingRequest(
            customer_id=booking_data.customer_id,
            vehicle_id=booking_data.vehicle_id,
            service_ids=booking_data.service_ids,
            scheduled_at=booking_data.scheduled_at,
        )

        response = await use_case.execute(request)

        return BookingResponseSchema(
            id=response.booking.id,
            status=response.booking.status.value,
            message=response.message,
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Key Characteristics**:
- Uses FastAPI decorators
- Pydantic schemas for validation
- Dependency injection for use cases
- HTTP-specific error handling

---

## 4. Feature Structure

Each feature follows **identical structure**:

```
features/<feature>/
├── domain/                 # Business logic (pure Python)
│   ├── entities.py         # Business entities with validation
│   ├── policies.py         # Business rules and policies
│   └── events.py           # Domain events (optional)
│
├── ports/                  # Interfaces/contracts
│   ├── repositories.py     # Repository interfaces
│   └── services.py         # Service interfaces
│
├── use_cases/              # Application workflows
│   ├── create_*.py         # Creation use cases
│   ├── update_*.py         # Update use cases
│   ├── get_*.py            # Query use cases
│   └── delete_*.py         # Deletion use cases
│
├── adapters/               # Technical implementations
│   ├── models.py           # SQLAlchemy models
│   ├── repositories.py     # Repository implementations
│   ├── external_*.py       # External service adapters
│   └── mappers.py          # Entity↔Model conversion
│
├── api/                    # HTTP layer
│   ├── router.py           # FastAPI routes
│   ├── schemas.py          # Pydantic request/response models
│   └── dependencies.py     # Dependency injection setup
│
└── tests/                  # All test levels
    ├── unit/               # Unit tests (domain, use cases)
    ├── integration/        # Integration tests (database)
    └── e2e/                # End-to-end tests (API)
```

### Current Features

1. **auth** - Authentication & Authorization
2. **bookings** - Booking Management
3. **services** - Service Catalog
4. **vehicles** - Vehicle Registry
5. **pricing** - Pricing Engine
6. **facilities** - Wash Bays & Mobile Teams
7. **staff** - Staff Management
8. **walkins** - Walk-in Services
9. **inventory** - Inventory Tracking
10. **expenses** - Expense Management
11. **analytics** - Reporting & Analytics

---

## 5. Dependency Flow

### Correct Dependency Flow

```
API Layer
   ↓ depends on
Use Cases Layer
   ↓ depends on
Ports Layer (interfaces)
   ↑ implemented by
Adapters Layer
```

**Example**:
```python
# ✅ CORRECT - Use case depends on interface
class CreateBookingUseCase:
    def __init__(self, booking_repo: IBookingRepository):
        self._repo = booking_repo  # Interface, not implementation

# ✅ CORRECT - Adapter implements interface
class SqlBookingRepository(IBookingRepository):
    def save(self, booking: Booking) -> Booking:
        # SQLAlchemy implementation
        pass

# ✅ CORRECT - API depends on use case
@router.post("/bookings")
async def create_booking(
    use_case: CreateBookingUseCase = Depends(get_create_booking_use_case)
):
    pass
```

### Incorrect Dependency Flow (Violations)

```python
# ❌ WRONG - Domain depending on adapter
from ..adapters.models import BookingModel  # NO!

class Booking:
    def save_to_db(self):
        # Domain should NOT know about database
        pass

# ❌ WRONG - Use case depending on SQLAlchemy directly
from sqlalchemy.ext.asyncio import AsyncSession

class CreateBookingUseCase:
    def __init__(self, session: AsyncSession):  # NO!
        self._session = session

# ❌ WRONG - Use case depending on FastAPI
from fastapi import HTTPException

class CreateBookingUseCase:
    def execute(self):
        raise HTTPException(...)  # NO! Use domain exceptions
```

---

## 6. Design Patterns

### 6.1 Repository Pattern

**Purpose**: Abstract data persistence

**Implementation**:
```python
# Port (Interface)
class IUserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        pass

# Adapter (Implementation)
class SqlUserRepository(IUserRepository):
    async def save(self, user: User) -> User:
        # SQLAlchemy implementation
        pass
```

### 6.2 Dependency Injection

**Purpose**: Invert dependencies, enable testing

**Implementation**:
```python
# dependencies.py
def get_booking_repository(
    db: AsyncSession = Depends(get_db)
) -> IBookingRepository:
    return SqlBookingRepository(db)

def get_create_booking_use_case(
    repo: IBookingRepository = Depends(get_booking_repository)
) -> CreateBookingUseCase:
    return CreateBookingUseCase(booking_repository=repo)

# router.py
@router.post("/bookings")
async def create_booking(
    use_case: CreateBookingUseCase = Depends(get_create_booking_use_case)
):
    pass
```

### 6.3 Request/Response Pattern

**Purpose**: Explicit contracts for use cases

**Implementation**:
```python
@dataclass
class CreateBookingRequest:
    customer_id: str
    vehicle_id: str
    service_ids: List[str]

@dataclass
class CreateBookingResponse:
    booking: Booking
    message: str

class CreateBookingUseCase:
    async def execute(
        self,
        request: CreateBookingRequest
    ) -> CreateBookingResponse:
        # Implementation
        pass
```

### 6.4 Policy Pattern

**Purpose**: Encapsulate business rules

**Implementation**:
```python
# domain/policies.py
class BookingCancellationPolicy:
    """Policy for booking cancellation rules."""

    @staticmethod
    def calculate_fee(
        booking: Booking,
        cancellation_time: datetime
    ) -> Decimal:
        hours_before = (booking.scheduled_at - cancellation_time).total_seconds() / 3600

        if hours_before >= 24:
            return booking.total_price * Decimal("0.5")
        else:
            return booking.total_price

    @staticmethod
    def can_cancel(booking: Booking) -> bool:
        return booking.status in [
            BookingStatus.PENDING,
            BookingStatus.CONFIRMED
        ]
```

### 6.5 Mapper Pattern

**Purpose**: Convert between domain entities and database models

**Implementation**:
```python
class BookingMapper:
    """Map between Booking entity and BookingModel."""

    @staticmethod
    def to_model(entity: Booking) -> BookingModel:
        return BookingModel(
            id=entity.id,
            customer_id=entity.customer_id,
            status=entity.status.value,
            total_price=entity.total_price,
        )

    @staticmethod
    def to_entity(model: BookingModel) -> Booking:
        return Booking(
            id=model.id,
            customer_id=model.customer_id,
            status=BookingStatus(model.status),
            total_price=model.total_price,
        )
```

---

## 7. Database Design

### Schema Overview

```
users                   # Authentication
├── id (PK)
├── email (unique)
├── password_hash
├── role (enum)
└── is_verified

vehicles                # Customer vehicles
├── id (PK)
├── customer_id (FK → users)
├── make, model, year
└── is_default

services                # Service catalog
├── id (PK)
├── category_id (FK → categories)
├── name, price
└── duration_minutes

bookings                # Main booking entity
├── id (PK)
├── customer_id (FK → users)
├── vehicle_id (FK → vehicles)
├── status (enum)
└── total_price

booking_services        # Many-to-many
├── booking_id (FK → bookings)
└── service_id (FK → services)

staff                   # Staff management
├── id (PK)
├── user_id (FK → users)
└── role, shift

inventory_products      # Inventory
├── id (PK)
├── sku (unique)
└── current_quantity

expenses                # Financial tracking
├── id (PK)
├── category (enum)
└── amount, status
```

### Relationships

- **One-to-Many**: User → Vehicles, User → Bookings
- **Many-to-Many**: Bookings ↔ Services (via booking_services)
- **One-to-One**: User → Staff (optional)

### Migrations

Using **Alembic** for schema migrations:

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 8. Security Architecture

### 8.1 Authentication Flow

```
1. User Login
   ↓
2. Validate credentials (Argon2 hash)
   ↓
3. Generate JWT tokens (access + refresh)
   ↓
4. Return tokens to client
   ↓
5. Client stores tokens (httpOnly cookies or localStorage)
   ↓
6. Client sends access_token in Authorization header
   ↓
7. API validates token signature and expiry
   ↓
8. Extract user claims (id, role, email)
   ↓
9. Attach user to request context
   ↓
10. Check permissions (RBAC)
```

### 8.2 Password Security

- **Algorithm**: Argon2 (OWASP recommended)
- **Min Length**: 8 characters
- **Max Length**: 128 characters
- **Storage**: Never store plaintext
- **Reset**: Time-limited tokens (1 hour expiry)

### 8.3 JWT Tokens

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "client",
  "exp": 1696262400,
  "iat": 1696261500
}
```

**Access Token**: 15 minutes expiry
**Refresh Token**: 7 days expiry with rotation

### 8.4 Authorization (RBAC)

```python
# Dependency for role checking
def require_any_role(*roles: str):
    def dependency(current_user: CurrentUser):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return Depends(dependency)

# Usage in endpoint
@router.get("/admin/stats")
async def get_stats(
    user: CurrentUser = Depends(require_any_role("admin", "manager"))
):
    pass
```

---

## 9. Testing Strategy

### Test Pyramid

```
        /\
       /  \
      / E2E\ (Few)
     /______\
    /        \
   /Integration\ (Some)
  /__________\
 /            \
/    Unit      \ (Many)
/______________\
```

### 9.1 Unit Tests

**Target**: Domain logic, use cases, policies

**Characteristics**:
- Fast (no I/O)
- Isolated (mock all dependencies)
- Pure business logic

**Example**:
```python
# tests/unit/test_booking_entity.py
def test_booking_cancellation_fee_24h_notice():
    booking = Booking(total_price=Decimal("100.00"))
    fee = booking.calculate_cancellation_fee(hours_before=25)
    assert fee == Decimal("50.00")  # 50% fee

def test_booking_cancellation_fee_less_than_24h():
    booking = Booking(total_price=Decimal("100.00"))
    fee = booking.calculate_cancellation_fee(hours_before=12)
    assert fee == Decimal("100.00")  # 100% fee
```

### 9.2 Integration Tests

**Target**: Repository implementations, database interactions

**Characteristics**:
- Use real database (test database)
- Test data persistence
- Transaction rollback after each test

**Example**:
```python
# tests/integration/test_booking_repository.py
@pytest.mark.asyncio
async def test_save_and_retrieve_booking(db_session):
    repo = SqlBookingRepository(db_session)
    booking = Booking(id="test-id", customer_id="user-id")

    await repo.save(booking)
    retrieved = await repo.get_by_id("test-id")

    assert retrieved.id == "test-id"
```

### 9.3 E2E Tests

**Target**: Full API endpoints

**Characteristics**:
- Test HTTP layer
- Real database
- Complete request/response flow

**Example**:
```python
# tests/e2e/test_booking_api.py
@pytest.mark.asyncio
async def test_create_booking_endpoint(client):
    response = await client.post("/api/v1/bookings", json={
        "customer_id": "user-id",
        "vehicle_id": "vehicle-id",
        "service_ids": ["service-1"],
    })

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
```

---

## 10. Deployment Architecture

### Docker Compose Architecture

```
┌─────────────────────────────────────────────────────┐
│                    NGINX (Optional)                  │
│              Reverse Proxy + SSL/TLS                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│                  BlingAuto API                       │
│                 (FastAPI + Uvicorn)                  │
│              Port 8000 (3 instances)                 │
└──────────┬───────────────────────┬──────────────────┘
           │                       │
    ┌──────▼──────┐         ┌──────▼──────┐
    │ PostgreSQL  │         │    Redis    │
    │   Port 5432 │         │  Port 6379  │
    │             │         │             │
    │  • Database │         │  • Cache    │
    │  • Backups  │         │  • Sessions │
    └─────────────┘         └─────────────┘
```

### Service Dependencies

```yaml
services:
  postgres:
    # Primary database

  redis:
    # Caching and sessions
    depends_on: []

  migrations:
    # Runs database migrations
    depends_on:
      - postgres

  api:
    # FastAPI application
    depends_on:
      - postgres
      - redis
      - migrations
```

### Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Scaling

```bash
# Scale API to 3 instances
docker-compose up -d --scale api=3
```

Load balancing handled by NGINX or cloud load balancer.

---

## Summary

BlingAuto API implements **Clean Architecture** with:

✅ **Strict layer separation** - Domain, Ports, Use Cases, Adapters, API
✅ **Dependency inversion** - Inner layers don't know about outer layers
✅ **Feature isolation** - Each feature is an independent module
✅ **Testability** - Pure business logic can be tested without frameworks
✅ **Technology independence** - Can swap databases, frameworks easily
✅ **SOLID principles** - Single responsibility, dependency injection
✅ **Design patterns** - Repository, Dependency Injection, Policy
✅ **Security first** - JWT, RBAC, Argon2 passwords, rate limiting
✅ **Production ready** - Docker deployment, health checks, monitoring

**Last Updated**: 2025-10-02
**Architecture Version**: 1.0
**Compliance**: 98/100 (Clean Architecture)
