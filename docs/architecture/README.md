# Architecture Documentation

## Overview

BlingAuto API is built using **Clean Architecture** principles, ensuring maintainability, testability, and scalability. The system is organized into isolated features that communicate through well-defined contracts.

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [System Structure](#system-structure)
3. [Layer Responsibilities](#layer-responsibilities)
4. [Dependency Rules](#dependency-rules)
5. [Feature Communication](#feature-communication)
6. [Design Patterns](#design-patterns)
7. [Data Flow](#data-flow)

---

## Architecture Principles

### 1. Clean Architecture

The system follows Uncle Bob's Clean Architecture:

```
┌─────────────────────────────────────────┐
│           External World                 │
│  (HTTP, DB, Redis, Email, etc.)         │
└───────────────┬─────────────────────────┘
                │
        ┌───────▼────────┐
        │   API Layer    │  ← HTTP I/O, Schemas, RBAC
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │  Use Cases     │  ← Application Logic
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │    Domain      │  ← Business Rules (Pure)
        └────────────────┘
                ▲
                │
        ┌───────┴────────┐
        │     Ports      │  ← Interfaces
        └────────────────┘
                ▲
                │
        ┌───────┴────────┐
        │   Adapters     │  ← Technical Implementations
        └────────────────┘
```

### 2. Dependency Inversion

Dependencies point **inward** toward the domain:
- Domain depends on **nothing**
- Use cases depend on **domain** and **ports**
- Adapters depend on **ports**
- API depends on **use cases**

### 3. Feature Isolation

Each feature is a **self-contained vertical slice**:
- Owns its domain logic
- Defines its own ports
- Implements its own adapters
- Exposes its own API

**No feature imports another feature's internals.**

---

## System Structure

### Directory Organization

```
app/
├── core/                    # Shared infrastructure (NO business logic)
│   ├── config/             # Settings, environment
│   ├── db/                 # SQLAlchemy, sessions, UoW
│   ├── cache/              # Redis client
│   ├── security/           # JWT, password hashing
│   ├── middleware/         # Request ID, logging, CORS, rate limit
│   ├── errors/             # Exception classes, handlers
│   ├── observability/      # Health checks, metrics
│   └── events.py           # Event bus
│
├── features/               # Business features (isolated)
│   ├── auth/
│   │   ├── domain/        # User, Token entities + policies
│   │   ├── ports/         # IUserRepository, ITokenService
│   │   ├── use_cases/     # RegisterUser, LoginUser, etc.
│   │   ├── adapters/      # UserRepository, TokenService
│   │   ├── api/           # Auth endpoints, schemas
│   │   └── tests/         # Unit, integration, API tests
│   │
│   ├── bookings/          # Same structure
│   ├── services/          # Same structure
│   ├── vehicles/          # Same structure
│   ├── pricing/           # Same structure
│   └── scheduling/        # Same structure
│
├── interfaces/            # Application composition
│   ├── http_api.py       # FastAPI app factory
│   ├── health.py         # Health endpoints
│   └── openapi.py        # API documentation
│
├── shared/                # Cross-cutting contracts
│   └── auth/             # Shared auth dependencies
│
└── migrations/            # Database migrations
    └── seeds/            # Initial data
```

---

## Layer Responsibilities

### 1. Domain Layer (`domain/`)

**Purpose**: Pure business logic, independent of frameworks

**Contains**:
- Entities (User, Booking, Service)
- Value Objects (Email, Money, Duration)
- Policies (cancellation fees, rating rules)
- Business rules validation
- State machines
- Domain events

**Rules**:
- ✅ Only Python stdlib imports (typing, dataclasses, datetime, enum)
- ❌ NO framework dependencies (FastAPI, Pydantic, SQLAlchemy)
- ❌ NO imports from other layers
- ❌ NO I/O operations

**Example**:
```python
# app/features/bookings/domain/entities.py
@dataclass
class Booking:
    id: str
    customer_id: str
    status: BookingStatus
    services: List[BookingService]

    MIN_SERVICES = 1
    MAX_SERVICES = 10

    def confirm(self):
        """Confirm a pending booking - RG-BOK-008"""
        if self.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Can only confirm pending bookings"
            )
        self.status = BookingStatus.CONFIRMED
        self.updated_at = datetime.utcnow()
```

### 2. Ports Layer (`ports/`)

**Purpose**: Interface definitions (contracts)

**Contains**:
- Repository interfaces
- Service interfaces
- External feature interfaces
- DTOs for inter-layer communication

**Rules**:
- ✅ Can import domain entities
- ✅ Abstract base classes (ABC)
- ❌ NO implementations
- ❌ NO framework dependencies

**Example**:
```python
# app/features/bookings/ports/repositories.py
class IBookingRepository(ABC):
    @abstractmethod
    def get_by_id(self, booking_id: str) -> Optional[Booking]:
        pass

    @abstractmethod
    def save(self, booking: Booking) -> Booking:
        pass
```

### 3. Use Cases Layer (`use_cases/`)

**Purpose**: Application orchestration, coordinates domain logic

**Contains**:
- Use case classes (one per business operation)
- Request/Response dataclasses
- Workflow coordination
- Transaction management

**Rules**:
- ✅ Imports domain and ports
- ✅ Orchestrates domain entities
- ✅ Uses ports for external dependencies
- ❌ NO direct framework usage
- ❌ NO business rules (delegates to domain)

**Example**:
```python
# app/features/bookings/use_cases/create_booking.py
class CreateBookingUseCase:
    def __init__(
        self,
        booking_repository: IBookingRepository,
        service_validator: IExternalServiceValidator,
        vehicle_validator: IExternalVehicleValidator,
    ):
        self._booking_repo = booking_repository
        self._service_validator = service_validator
        self._vehicle_validator = vehicle_validator

    async def execute(self, request: CreateBookingRequest) -> CreateBookingResponse:
        # 1. Validate services exist
        services = await self._service_validator.get_services_details(
            request.service_ids
        )

        # 2. Validate vehicle ownership
        if not await self._vehicle_validator.validate_vehicle_belongs_to_customer(
            request.vehicle_id, request.customer_id
        ):
            raise ValidationError("Vehicle not found or not owned by customer")

        # 3. Create domain entity (business rules applied here)
        booking = Booking.create(
            customer_id=request.customer_id,
            vehicle_id=request.vehicle_id,
            scheduled_at=request.scheduled_at,
            services=services,
            booking_type=request.booking_type,
        )

        # 4. Persist
        saved_booking = self._booking_repo.save(booking)

        return CreateBookingResponse(booking_id=saved_booking.id)
```

### 4. Adapters Layer (`adapters/`)

**Purpose**: Technical implementations of ports

**Contains**:
- Repository implementations (SQLAlchemy)
- Service implementations (Redis, SMTP, HTTP)
- Cross-feature adapters (calls to other features)
- Data mapping

**Rules**:
- ✅ Implements port interfaces
- ✅ Uses core infrastructure (DB, cache)
- ✅ Can call public use cases from OTHER features
- ❌ NO business logic
- ❌ NO use case imports from SAME feature

**Example**:
```python
# app/features/bookings/adapters/repositories.py
class SqlBookingRepository(IBookingRepository):
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, booking_id: str) -> Optional[Booking]:
        model = self._session.query(BookingModel).filter_by(id=booking_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def save(self, booking: Booking) -> Booking:
        model = self._to_model(booking)
        self._session.add(model)
        self._session.flush()
        return self._to_entity(model)
```

### 5. API Layer (`api/`)

**Purpose**: HTTP I/O, request validation, response formatting

**Contains**:
- FastAPI routers
- Pydantic schemas (request/response)
- Dependency injection
- RBAC guards
- Error mapping

**Rules**:
- ✅ Imports use cases and schemas
- ✅ Uses Pydantic for validation
- ✅ Handles HTTP concerns
- ❌ NO business logic
- ❌ NO direct domain imports

**Example**:
```python
# app/features/bookings/api/router.py
@router.post("/", response_model=CreateBookingResponseSchema)
async def create_booking(
    booking_data: CreateBookingSchema,
    current_user: CurrentUser,
    create_use_case: CreateBookingUseCase = Depends(get_create_booking_use_case),
):
    """Create a new booking."""

    # Convert Pydantic schema to use case request
    request = CreateBookingRequest(
        customer_id=current_user.id,
        vehicle_id=booking_data.vehicle_id,
        scheduled_at=booking_data.scheduled_at,
        service_ids=booking_data.service_ids,
        booking_type=booking_data.booking_type,
    )

    # Execute use case
    response = await create_use_case.execute(request)

    # Convert use case response to Pydantic schema
    return CreateBookingResponseSchema(
        booking_id=response.booking_id,
        status=response.status,
    )
```

---

## Dependency Rules

### Allowed Dependencies

```
✅ api → use_cases (call business operations)
✅ api → schemas (use Pydantic models)
✅ api → shared (use auth contracts)

✅ use_cases → domain (orchestrate entities)
✅ use_cases → ports (depend on interfaces)

✅ adapters → ports (implement interfaces)
✅ adapters → core (use infrastructure)
✅ adapters → OTHER features' use_cases (cross-feature calls)

✅ ports → domain (use domain types)

✅ domain → stdlib only (typing, dataclasses, etc.)
```

### Forbidden Dependencies

```
❌ domain → anything (must be pure)
❌ use_cases → adapters (depends on interfaces, not implementations)
❌ use_cases → api (business logic doesn't know about HTTP)
❌ ports → use_cases (interfaces don't depend on implementations)
❌ adapters → use_cases from SAME feature (except in factories)
❌ core → features (infrastructure doesn't know about business)
❌ features → other features' internals (only via public use cases)
```

### Import Rules Matrix

| From ↓ To → | domain | ports | use_cases | adapters | api | core | other features |
|-------------|--------|-------|-----------|----------|-----|------|----------------|
| **domain** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **ports** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **use_cases** | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ (UoW only) | ❌ |
| **adapters** | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ | ⚠️ (public use cases) |
| **api** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ |
| **core** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

---

## Feature Communication

### Problem: How do features interact without direct imports?

### Solution: Consumer-Owned Ports + Local Adapters

#### Pattern

1. **Consumer defines a port** (interface for its needs)
2. **Consumer implements an adapter** (calls provider's public use case)
3. **Provider exposes public use cases** (documented API surface)

#### Example: Bookings needs to validate Services

```python
# Step 1: Bookings defines its port
# app/features/bookings/ports/external_services.py
class IExternalServiceValidator(ABC):
    @abstractmethod
    async def validate_service_exists(self, service_id: str) -> bool:
        pass

# Step 2: Bookings implements adapter
# app/features/bookings/adapters/external_services.py
class ExternalServiceValidatorAdapter(IExternalServiceValidator):
    def __init__(self, get_service_use_case: GetServiceUseCase):
        self._get_service = get_service_use_case

    async def validate_service_exists(self, service_id: str) -> bool:
        try:
            service = await self._get_service.execute(service_id)
            return service is not None and service.is_active
        except Exception:
            return False

# Step 3: Services exposes public use case
# app/features/services/use_cases/get_service.py (already exists)
class GetServiceUseCase:
    async def execute(self, service_id: str) -> Optional[Service]:
        # Implementation
        pass
```

#### Benefits
- ✅ Bookings doesn't depend on Services' internals
- ✅ Services can change implementation without breaking Bookings
- ✅ Clear contract (port) owned by consumer
- ✅ Testable (mock the port)
- ✅ Unidirectional dependency (Bookings → Services)

---

## Design Patterns

### 1. Repository Pattern
- Abstracts data access
- Port: `IBookingRepository`
- Adapter: `SqlBookingRepository`

### 2. Dependency Injection
- Dependencies injected via constructors
- FastAPI `Depends()` at API layer
- Manual injection in use cases

### 3. Unit of Work
- Transaction management
- `UnitOfWork` context manager
- Ensures atomic operations

### 4. Factory Pattern
- Entity creation via factory methods
- `Booking.create(...)`
- Enforces business rules at creation

### 5. Strategy Pattern
- Different implementations of ports
- Example: `SqlBookingRepository` vs `InMemoryBookingRepository`

### 6. Adapter Pattern
- Cross-feature communication
- Example: `ExternalServiceValidatorAdapter`

### 7. Event-Driven
- Domain events published
- In-memory event bus
- Decoupled side effects

---

## Data Flow

### 1. Create Booking Flow

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ HTTP POST /api/v1/bookings
     ▼
┌─────────────────┐
│   API Layer     │  1. Validate request (Pydantic)
│  (router.py)    │  2. Check RBAC
└────┬────────────┘  3. Convert to use case request
     │
     ▼
┌─────────────────┐
│  Use Case       │  4. Validate services exist (via port)
│ CreateBooking   │  5. Validate vehicle ownership (via port)
└────┬────────────┘  6. Create Booking entity (business rules apply)
     │                7. Save via repository
     ▼
┌─────────────────┐
│  Domain         │  8. Apply business rules
│  Booking.create │     - 1-10 services
└────┬────────────┘     - 30-240 min duration
     │                  - Future scheduling
     ▼                  - Mobile requires location
┌─────────────────┐
│  Repository     │  9. Map entity to SQLAlchemy model
│ (adapter)       │  10. Persist to database
└────┬────────────┘  11. Return saved entity
     │
     ▼
┌─────────────────┐
│  Database       │  12. Transaction committed
└─────────────────┘
```

### 2. Cross-Feature Call Flow (Bookings → Services)

```
┌──────────────────┐
│ Bookings         │
│ Use Case         │
└────┬─────────────┘
     │ needs to validate service
     ▼
┌──────────────────┐
│ IExternalService │  (port owned by Bookings)
│ Validator        │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ ExternalService  │  (adapter in Bookings)
│ ValidatorAdapter │
└────┬─────────────┘
     │ calls public use case
     ▼
┌──────────────────┐
│ Services Feature │
│ GetServiceUseCase│  (public API of Services)
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Service Domain   │
│ Entity           │
└──────────────────┘
```

---

## Architecture Enforcement

### Automated Checks

**Import Linter** configuration enforces rules:

```bash
# Install
pip install import-linter

# Run checks
lint-imports

# Expected output
✅ All 12 contracts passed
```

### Manual Reviews

Every PR should verify:
- [ ] No cross-feature internal imports
- [ ] No business logic in API/adapters
- [ ] No framework imports in domain
- [ ] Dependency direction correct
- [ ] Tests follow same structure

---

## Best Practices

### DO ✅
- Keep domain logic pure (no frameworks)
- Use factory methods for entity creation
- Inject dependencies via constructors
- Test domain logic without frameworks
- Document public use cases (cross-feature API)
- Use descriptive names (CreateBookingUseCase)
- One use case = one business operation
- Keep use cases thin (orchestration only)

### DON'T ❌
- Put business logic in API layer
- Import other features' internals
- Make use cases depend on adapters
- Skip validation in domain layer
- Create god classes
- Share transactions across features
- Use `now()` directly in domain (inject Clock)

---

## Migration Guide

### From Legacy Code

If migrating from non-clean architecture:

1. **Extract domain entities** from models
2. **Define ports** for external dependencies
3. **Create use cases** to orchestrate
4. **Implement adapters** for ports
5. **Move API logic** to routers
6. **Write tests** at each layer

### Adding a New Feature

1. Create feature directory structure
2. Define domain entities with business rules
3. Create ports for external dependencies
4. Implement use cases
5. Create adapters (repositories, services)
6. Add API layer (routers, schemas)
7. Register router in `interfaces/http_api.py`
8. Write tests (unit → integration → API)

---

## References

- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

**Next**: [Feature Documentation](../features/README.md)
