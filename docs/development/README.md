# Development Guide

Complete guide for developers working on BlingAuto API.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Setup](#project-setup)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guide](#testing-guide)
6. [Adding New Features](#adding-new-features)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **Git**: Latest version
- **PostgreSQL**: 14+ (or SQLite for local dev)
- **Redis**: 6+ (optional for local dev)
- **IDE**: VS Code or PyCharm recommended

### Clone Repository

```bash
git clone https://github.com/your-org/blingauto-api.git
cd blingauto-api
```

---

## Project Setup

### 1. Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### 3. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your local settings
# Minimal config for local development:
DATABASE_URL=sqlite:///./carwash.db
SECRET_KEY=dev-secret-key-not-for-production
DEBUG=True
ENVIRONMENT=development
```

### 4. Database Setup

```bash
# Run migrations
alembic upgrade head

# Seed initial data (optional)
python -m scripts.seed_data
```

### 5. Verify Installation

```bash
# Run tests
pytest

# Start development server
python main.py
```

Visit: http://localhost:8000/docs

---

## Development Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b fix/bug-description

# Create hotfix branch (production issues)
git checkout -b hotfix/critical-issue
```

### Daily Workflow

```bash
# 1. Update your branch
git checkout main
git pull origin main

# 2. Start your work
git checkout -b feature/my-feature

# 3. Make changes and commit frequently
git add .
git commit -m "feat: add booking cancellation logic"

# 4. Push and create PR
git push origin feature/my-feature
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples**:
```bash
feat(bookings): add walk-in booking support
fix(auth): resolve token refresh race condition
docs(api): update booking endpoints documentation
refactor(services): extract pricing calculator
test(bookings): add state machine transition tests
```

---

## Coding Standards

### Architecture Rules

**MUST FOLLOW** - See [Architecture Guide](../architecture/README.md) for details:

1. **Layer Structure** - Every feature MUST have:
   ```
   feature/
   ├── domain/          # Entities, value objects, policies
   ├── ports/           # Interfaces (repositories, services)
   ├── use_cases/       # Application logic
   ├── adapters/        # Implementations (DB, external)
   └── api/            # FastAPI routes, schemas
   ```

2. **Dependency Direction** - ALWAYS:
   ```
   api → use_cases → domain
           ↓
         ports
           ↑
       adapters
   ```

3. **Domain Purity** - Domain layer MUST NOT import:
   - FastAPI
   - Pydantic
   - SQLAlchemy
   - Redis
   - Any framework/library

4. **No Cross-Feature Imports** - EXCEPT:
   - Adapters may call other features' public use cases
   - Use consumer-owned port pattern

5. **One Transaction Per Use Case**:
   ```python
   async def execute(self, request: Request) -> Response:
       async with self._uow:
           # All database operations here
           await self._uow.commit()
   ```

### Python Style Guide

Follow **PEP 8** with these additions:

#### File Naming
- Use `snake_case` for all files: `booking_service.py`
- Use `PascalCase` for classes: `class BookingService`
- Use `UPPER_CASE` for constants: `MAX_BOOKINGS = 10`

#### Code Structure

```python
# 1. Standard library imports
from datetime import datetime
from typing import Optional, List

# 2. Third-party imports
from fastapi import HTTPException

# 3. Local application imports
from app.features.bookings.domain import Booking
from app.core.errors import BusinessRuleViolationError
```

#### Type Hints

**ALWAYS** use type hints:

```python
# Good
def create_booking(
    self,
    customer_id: str,
    scheduled_at: datetime,
    services: List[str],
) -> Booking:
    pass

# Bad
def create_booking(self, customer_id, scheduled_at, services):
    pass
```

#### Docstrings

Use **Google-style docstrings**:

```python
def calculate_price(
    self,
    services: List[Service],
    vehicle_type: VehicleType,
) -> Decimal:
    """Calculate total booking price.

    Args:
        services: List of services to include
        vehicle_type: Type of vehicle for pricing tier

    Returns:
        Total price including all services and fees

    Raises:
        BusinessRuleViolationError: If pricing rules are violated
    """
    pass
```

#### Error Handling

```python
# Domain errors - Use custom exceptions
from app.core.errors import BusinessRuleViolationError

if booking.status != BookingStatus.PENDING:
    raise BusinessRuleViolationError(
        message="Cannot confirm non-pending booking",
        code="INVALID_STATUS_TRANSITION"
    )

# API errors - Convert to HTTP exceptions
from fastapi import HTTPException

try:
    booking = await use_case.execute(request)
except BusinessRuleViolationError as e:
    raise HTTPException(status_code=400, detail=e.message)
```

---

## Testing Guide

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests (fast, isolated)
│   ├── test_booking_entity.py
│   └── test_price_calculator.py
├── integration/          # Integration tests (DB, external services)
│   ├── test_booking_use_cases.py
│   └── test_auth_flow.py
└── e2e/                  # End-to-end tests (full API)
    └── test_booking_api.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_booking_entity.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only fast tests (exclude integration)
pytest -m "not integration"

# Run with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_booking_entity.py::test_confirm_booking
```

### Writing Unit Tests

**Test Domain Entities** (no dependencies):

```python
# tests/unit/test_booking_entity.py
import pytest
from datetime import datetime, timedelta
from app.features.bookings.domain import Booking, BookingStatus
from app.core.errors import BusinessRuleViolationError

def test_confirm_booking_success():
    """Should successfully confirm a pending booking."""
    # Arrange
    booking = Booking(
        id="test-123",
        status=BookingStatus.PENDING,
        scheduled_at=datetime.utcnow() + timedelta(hours=24),
    )

    # Act
    booking.confirm()

    # Assert
    assert booking.status == BookingStatus.CONFIRMED

def test_confirm_booking_invalid_status():
    """Should raise error when confirming non-pending booking."""
    # Arrange
    booking = Booking(
        id="test-123",
        status=BookingStatus.CONFIRMED,
        scheduled_at=datetime.utcnow() + timedelta(hours=24),
    )

    # Act & Assert
    with pytest.raises(BusinessRuleViolationError) as exc:
        booking.confirm()
    assert "INVALID_STATUS_TRANSITION" in str(exc.value)
```

### Writing Integration Tests

**Test Use Cases** (with database):

```python
# tests/integration/test_booking_use_cases.py
import pytest
from app.features.bookings.use_cases import CreateBookingUseCase
from app.features.bookings.use_cases.dtos import CreateBookingRequest

@pytest.mark.integration
async def test_create_booking_success(db_session, test_customer, test_service):
    """Should create booking with valid data."""
    # Arrange
    repository = SQLAlchemyBookingRepository(db_session)
    use_case = CreateBookingUseCase(repository)

    request = CreateBookingRequest(
        customer_id=test_customer.id,
        service_ids=[test_service.id],
        scheduled_at=datetime.utcnow() + timedelta(hours=24),
    )

    # Act
    response = await use_case.execute(request)

    # Assert
    assert response.booking_id is not None
    assert response.status == "PENDING"
```

### Writing E2E Tests

**Test Full API** (HTTP requests):

```python
# tests/e2e/test_booking_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.e2e
async def test_booking_flow(client: AsyncClient, auth_headers):
    """Should complete full booking flow."""
    # Create booking
    response = await client.post(
        "/api/v1/bookings",
        json={
            "customer_id": "customer-123",
            "service_ids": ["service-1"],
            "scheduled_at": "2025-10-02T10:00:00Z",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    booking_id = response.json()["id"]

    # Confirm booking
    response = await client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def db_session():
    """Provide clean database session for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.fixture
def test_customer():
    """Provide test customer."""
    return User(
        id="customer-123",
        email="test@example.com",
        role=UserRole.CLIENT,
    )
```

### Test Coverage Goals

- **Domain entities**: 100% coverage
- **Use cases**: 90%+ coverage
- **API endpoints**: 80%+ coverage
- **Overall project**: 85%+ coverage

```bash
# Check coverage
pytest --cov=app --cov-report=term-missing

# Generate HTML report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Adding New Features

### Step-by-Step Guide

#### 1. Create Feature Structure

```bash
mkdir -p app/features/new_feature/{domain,ports,use_cases,adapters,api}
touch app/features/new_feature/__init__.py
touch app/features/new_feature/domain/__init__.py
touch app/features/new_feature/ports/__init__.py
touch app/features/new_feature/use_cases/__init__.py
touch app/features/new_feature/adapters/__init__.py
touch app/features/new_feature/api/__init__.py
```

#### 2. Define Domain Entities

```python
# app/features/new_feature/domain/entities.py
from dataclasses import dataclass
from datetime import datetime
from app.core.errors import BusinessRuleViolationError

@dataclass
class MyEntity:
    """Domain entity with business rules."""
    id: str
    name: str
    created_at: datetime

    # Business rules as constants
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100

    def validate_name(self) -> None:
        """Validate name against business rules."""
        if len(self.name) < self.MIN_NAME_LENGTH:
            raise BusinessRuleViolationError(
                message=f"Name must be at least {self.MIN_NAME_LENGTH} characters",
                code="NAME_TOO_SHORT"
            )
```

#### 3. Define Ports (Interfaces)

```python
# app/features/new_feature/ports/repositories.py
from abc import ABC, abstractmethod
from typing import Optional, List
from app.features.new_feature.domain import MyEntity

class IMyEntityRepository(ABC):
    """Repository interface for MyEntity."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[MyEntity]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def create(self, entity: MyEntity) -> MyEntity:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, entity: MyEntity) -> MyEntity:
        """Update existing entity."""
        pass
```

#### 4. Implement Use Cases

```python
# app/features/new_feature/use_cases/create_entity.py
from dataclasses import dataclass
from app.features.new_feature.domain import MyEntity
from app.features.new_feature.ports import IMyEntityRepository

@dataclass
class CreateEntityRequest:
    """Request DTO."""
    name: str
    user_id: str

@dataclass
class CreateEntityResponse:
    """Response DTO."""
    entity_id: str
    name: str

class CreateEntityUseCase:
    """Use case for creating new entity."""

    def __init__(self, repository: IMyEntityRepository):
        self._repository = repository

    async def execute(self, request: CreateEntityRequest) -> CreateEntityResponse:
        """Execute use case."""
        # Create domain entity
        entity = MyEntity(
            id=generate_id(),
            name=request.name,
            created_at=datetime.utcnow(),
        )

        # Validate business rules
        entity.validate_name()

        # Persist
        saved_entity = await self._repository.create(entity)

        # Return response
        return CreateEntityResponse(
            entity_id=saved_entity.id,
            name=saved_entity.name,
        )
```

#### 5. Implement Adapters

```python
# app/features/new_feature/adapters/repositories.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.new_feature.domain import MyEntity
from app.features.new_feature.ports import IMyEntityRepository
from app.features.new_feature.adapters.models import MyEntityModel

class SQLAlchemyMyEntityRepository(IMyEntityRepository):
    """SQLAlchemy implementation of repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: str) -> Optional[MyEntity]:
        """Get entity by ID."""
        result = await self._session.execute(
            select(MyEntityModel).where(MyEntityModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, entity: MyEntity) -> MyEntity:
        """Create new entity."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return self._to_domain(model)

    def _to_domain(self, model: MyEntityModel) -> MyEntity:
        """Convert DB model to domain entity."""
        return MyEntity(
            id=model.id,
            name=model.name,
            created_at=model.created_at,
        )

    def _to_model(self, entity: MyEntity) -> MyEntityModel:
        """Convert domain entity to DB model."""
        return MyEntityModel(
            id=entity.id,
            name=entity.name,
            created_at=entity.created_at,
        )
```

#### 6. Create API Layer

```python
# app/features/new_feature/api/router.py
from fastapi import APIRouter, Depends, HTTPException
from app.features.new_feature.api.schemas import CreateEntitySchema, EntitySchema
from app.features.new_feature.use_cases import CreateEntityUseCase
from app.features.new_feature.api.dependencies import get_create_entity_use_case

router = APIRouter()

@router.post("/", response_model=EntitySchema, status_code=201)
async def create_entity(
    data: CreateEntitySchema,
    use_case: CreateEntityUseCase = Depends(get_create_entity_use_case),
):
    """Create new entity."""
    try:
        request = CreateEntityRequest(
            name=data.name,
            user_id=current_user.id,
        )
        response = await use_case.execute(request)
        return EntitySchema(
            id=response.entity_id,
            name=response.name,
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=400, detail=e.message)
```

#### 7. Register Router

```python
# app/interfaces/http_api.py
from app.features.new_feature.api.router import router as new_feature_router

app.include_router(
    new_feature_router,
    prefix=f"{API_V1_PREFIX}/new-feature",
    tags=["New Feature"]
)
```

#### 8. Create Migration

```bash
# Create migration
alembic revision --autogenerate -m "Add new_feature tables"

# Review migration file
# Edit if needed

# Apply migration
alembic upgrade head
```

#### 9. Write Tests

```python
# tests/unit/test_my_entity.py
def test_validate_name_too_short():
    """Should raise error for short name."""
    entity = MyEntity(id="1", name="ab", created_at=datetime.utcnow())
    with pytest.raises(BusinessRuleViolationError):
        entity.validate_name()

# tests/integration/test_create_entity_use_case.py
@pytest.mark.integration
async def test_create_entity_success(db_session):
    """Should create entity successfully."""
    repository = SQLAlchemyMyEntityRepository(db_session)
    use_case = CreateEntityUseCase(repository)

    request = CreateEntityRequest(name="Test Entity", user_id="user-1")
    response = await use_case.execute(request)

    assert response.entity_id is not None
```

#### 10. Verify Architecture Compliance

```bash
# Run import linter
lint-imports

# Should pass all contracts
```

---

## Common Tasks

### Add New Endpoint

```python
# 1. Define use case DTOs
@dataclass
class UpdateBookingRequest:
    booking_id: str
    new_date: datetime

# 2. Implement use case
class UpdateBookingUseCase:
    async def execute(self, request: UpdateBookingRequest):
        # Logic here
        pass

# 3. Create API schema
class UpdateBookingSchema(BaseModel):
    new_date: datetime

# 4. Add router endpoint
@router.patch("/{booking_id}")
async def update_booking(
    booking_id: str,
    data: UpdateBookingSchema,
    use_case: UpdateBookingUseCase = Depends(...),
):
    request = UpdateBookingRequest(
        booking_id=booking_id,
        new_date=data.new_date,
    )
    return await use_case.execute(request)
```

### Add New Business Rule

```python
# 1. Add to domain entity
@dataclass
class Booking:
    MAX_ADVANCE_DAYS = 90

    def validate_not_too_far_in_future(self) -> None:
        """RG-BOK-017: Cannot book more than 90 days in advance."""
        max_date = datetime.utcnow() + timedelta(days=self.MAX_ADVANCE_DAYS)
        if self.scheduled_at > max_date:
            raise BusinessRuleViolationError(
                message=f"Cannot book more than {self.MAX_ADVANCE_DAYS} days in advance",
                code="BOOKING_TOO_FAR_FUTURE"
            )

# 2. Call in use case
async def execute(self, request: CreateBookingRequest):
    booking = Booking(...)
    booking.validate_not_too_far_in_future()
    # ... rest of logic

# 3. Add test
def test_booking_too_far_future():
    booking = Booking(
        scheduled_at=datetime.utcnow() + timedelta(days=91)
    )
    with pytest.raises(BusinessRuleViolationError, match="BOOKING_TOO_FAR_FUTURE"):
        booking.validate_not_too_far_in_future()
```

### Add Database Migration

```bash
# 1. Modify SQLAlchemy model
# app/features/bookings/adapters/models.py
class BookingModel(Base):
    __tablename__ = "bookings"
    # Add new column
    notes = Column(String(500), nullable=True)

# 2. Generate migration
alembic revision --autogenerate -m "Add notes to bookings"

# 3. Review generated migration
# migrations/versions/xxx_add_notes_to_bookings.py

# 4. Apply migration
alembic upgrade head

# 5. Rollback if needed
alembic downgrade -1
```

### Add Cross-Feature Communication

```python
# 1. Define port in CONSUMER feature (bookings)
# app/features/bookings/ports/external_services.py
class ICustomerValidator(ABC):
    @abstractmethod
    async def validate_customer_exists(self, customer_id: str) -> bool:
        pass

# 2. Implement adapter in CONSUMER feature
# app/features/bookings/adapters/external_services.py
class CustomerValidatorAdapter(ICustomerValidator):
    def __init__(self, get_user_use_case: GetUserUseCase):  # From auth feature
        self._get_user = get_user_use_case

    async def validate_customer_exists(self, customer_id: str) -> bool:
        user = await self._get_user.execute(customer_id)
        return user is not None

# 3. Wire in dependencies
# app/features/bookings/api/dependencies.py
async def get_customer_validator() -> ICustomerValidator:
    get_user_use_case = await get_get_user_use_case()  # From auth
    return CustomerValidatorAdapter(get_user_use_case)
```

---

## Troubleshooting

### Import Linter Failures

```bash
# Run linter
lint-imports

# If violation found:
# ERROR: Contract broken: Domain layer independence
#   app.features.bookings.domain.entities imports fastapi

# Fix: Remove FastAPI import from domain
# Domain should only have Python stdlib and domain code
```

### Database Connection Issues

```bash
# Check DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
python -c "from app.core.database import engine; print('Connected!')"

# Reset database
alembic downgrade base
alembic upgrade head
```

### Test Failures

```bash
# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Run specific test
pytest tests/unit/test_booking.py::test_confirm_booking -vv

# Debug with pdb
pytest --pdb
```

### Circular Import Errors

```python
# Bad: Circular dependency
# file_a.py
from file_b import ClassB

# file_b.py
from file_a import ClassA  # Circular!

# Fix: Use TYPE_CHECKING
# file_a.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from file_b import ClassB

# Or: Move shared code to separate module
```

---

## IDE Configuration

### VS Code Settings

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.rulers": [88, 120]
}
```

### Recommended Extensions

- Python (Microsoft)
- Pylance
- Black Formatter
- autoDocstring
- GitLens
- Better Comments

---

## Resources

- [Architecture Guide](../architecture/README.md)
- [Features Documentation](../features/README.md)
- [API Reference](../api/README.md)
- [Deployment Guide](../deployment/README.md)
- [ADRs](../ADRs/README.md)

---

**Last Updated**: 2025-10-01
