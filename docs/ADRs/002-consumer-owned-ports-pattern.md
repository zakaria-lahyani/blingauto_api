# ADR-002: Consumer-Owned Ports for Cross-Feature Communication

**Status**: Accepted

**Date**: 2025-09-20

**Authors**: Development Team

**Stakeholders**: All developers, Technical leadership

---

## Context

### Background

With Clean Architecture adopted ([ADR-001](./001-clean-architecture-adoption.md)), we organized code into self-contained features. However, features need to communicate:

- **Bookings** needs to validate that services exist (from **Services** feature)
- **Bookings** needs to validate that customers exist (from **Auth** feature)
- **Bookings** needs to validate that vehicles exist (from **Vehicles** feature)
- **Services** needs to check if categories are active (from **Categories**)

### Problem Statement

How do we allow cross-feature communication while maintaining:
1. Feature independence (no direct feature-to-feature imports)
2. Clear dependency direction
3. Testability (easy to mock external features)
4. No circular dependencies
5. Single transaction per use case (no distributed transactions)

### Anti-Pattern Example

❌ **Bad: Direct cross-feature import**
```python
# app/features/bookings/use_cases/create_booking.py
from app.features.services.domain import Service  # BAD!
from app.features.services.adapters.repositories import ServiceRepository  # BAD!

class CreateBookingUseCase:
    def __init__(self, service_repo: ServiceRepository):  # Tight coupling!
        self._service_repo = service_repo

    async def execute(self, request):
        service = await self._service_repo.get_by_id(request.service_id)
        # Now bookings depends on services' internals
```

Problems:
- Bookings now imports Services domain
- Cannot test bookings without services feature
- Circular dependency risk
- Violates feature isolation

---

## Decision

We will use the **Consumer-Owned Port Pattern** where:

1. **Consumer defines the interface** (port) it needs in its own `ports/` directory
2. **Consumer's adapter** implements the interface by calling **Provider's public use cases**
3. **No direct access** to provider's domain or repositories

### Pattern Structure

```
bookings/                           services/
├── ports/                          ├── use_cases/
│   └── external_services.py        │   ├── get_service.py
│       # IExternalServiceValidator │   └── list_services.py
│       # (owned by bookings)       └── api/
└── adapters/                           └── dependencies.py
    └── external_services.py                # Expose use cases
        # ExternalServiceValidatorAdapter
        # (calls services' use cases)
```

### Implementation Example

**Step 1: Consumer defines port**
```python
# app/features/bookings/ports/external_services.py
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

@dataclass
class ServiceDetails:
    """DTO owned by bookings feature."""
    id: str
    name: str
    duration_minutes: int
    price: Decimal
    is_active: bool

class IExternalServiceValidator(ABC):
    """Interface owned by bookings for service validation."""

    @abstractmethod
    async def get_service_details(self, service_id: str) -> Optional[ServiceDetails]:
        """Get service details from services feature."""
        pass

    @abstractmethod
    async def validate_service_exists(self, service_id: str) -> bool:
        """Check if service exists and is active."""
        pass
```

**Step 2: Consumer implements adapter**
```python
# app/features/bookings/adapters/external_services.py
from app.features.bookings.ports.external_services import (
    IExternalServiceValidator,
    ServiceDetails
)
from app.features.services.use_cases import GetServiceUseCase  # Public API only

class ExternalServiceValidatorAdapter(IExternalServiceValidator):
    """Adapter that calls services feature's public use cases."""

    def __init__(self, get_service_use_case: GetServiceUseCase):
        self._get_service = get_service_use_case

    async def get_service_details(self, service_id: str) -> Optional[ServiceDetails]:
        """Call services feature's public use case."""
        service = await self._get_service.execute(service_id)

        if not service:
            return None

        # Convert provider's domain entity to consumer's DTO
        return ServiceDetails(
            id=service.id,
            name=service.name,
            duration_minutes=service.duration_minutes,
            price=service.price,
            is_active=service.is_active
        )

    async def validate_service_exists(self, service_id: str) -> bool:
        """Validate service exists."""
        details = await self.get_service_details(service_id)
        return details is not None and details.is_active
```

**Step 3: Consumer uses port in use case**
```python
# app/features/bookings/use_cases/create_booking.py
from app.features.bookings.ports.external_services import IExternalServiceValidator

class CreateBookingUseCase:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        service_validator: IExternalServiceValidator,  # Port, not concrete
    ):
        self._booking_repo = booking_repo
        self._service_validator = service_validator

    async def execute(self, request: CreateBookingRequest):
        # Validate services exist via port
        for service_id in request.service_ids:
            if not await self._service_validator.validate_service_exists(service_id):
                raise BusinessRuleViolationError(f"Service {service_id} not found")

        # Continue with booking creation...
```

**Step 4: Wire dependencies**
```python
# app/features/bookings/api/dependencies.py
from app.features.bookings.ports.external_services import IExternalServiceValidator
from app.features.bookings.adapters.external_services import ExternalServiceValidatorAdapter
from app.features.services.api.dependencies import get_get_service_use_case

async def get_service_validator() -> IExternalServiceValidator:
    """Provide service validator adapter."""
    get_service_use_case = await get_get_service_use_case()
    return ExternalServiceValidatorAdapter(get_service_use_case)
```

### Key Principles

1. **Consumer Ownership**: Interface defined by consumer's needs
2. **Public API Only**: Only call provider's use cases (never repositories/domain)
3. **Data Conversion**: Convert between provider's entities and consumer's DTOs
4. **No Shared Transactions**: Each use case manages its own transaction
5. **Testability**: Easy to mock port with fake implementation

---

## Consequences

### Positive Consequences

- **Feature Independence**: Features completely decoupled
  - Can test bookings without services feature running
  - Can extract features to separate microservices
  - No circular dependencies possible

- **Clear Boundaries**: Explicit interfaces define contracts
  - Consumer's needs are explicit
  - Provider can change internals without breaking consumer
  - Version compatibility clear

- **Testability**: Easy to mock external features
```python
# tests/unit/test_create_booking.py
class FakeServiceValidator(IExternalServiceValidator):
    async def validate_service_exists(self, service_id: str) -> bool:
        return service_id == "valid-service"

def test_create_booking():
    use_case = CreateBookingUseCase(
        booking_repo=FakeBookingRepo(),
        service_validator=FakeServiceValidator(),  # Mock!
    )
```

- **Parallel Development**: Teams work independently
  - Bookings team defines what they need
  - Services team implements use case
  - Integration via dependency injection

### Negative Consequences

- **More Code**: Each cross-feature dependency needs:
  - Port interface (consumer)
  - Adapter implementation (consumer)
  - Potentially DTOs for data conversion
  - **Mitigation**: Reusable patterns, code templates

- **Indirect Communication**: Not obvious where provider is called
  - Cannot grep for direct imports
  - Need to check adapter implementations
  - **Mitigation**: Naming convention (External* prefix), documentation

- **Potential Duplication**: Consumer's DTOs may duplicate provider's entities
  - ServiceDetails in bookings vs Service in services
  - **Mitigation**: Acceptable trade-off for decoupling

### Neutral Consequences

- **N+1 Query Risk**: Multiple use case calls instead of joins
  - Each validation is separate query
  - **Mitigation**: Batch operations where needed, caching

---

## Alternatives Considered

### Alternative 1: Shared Kernel (Common Domain)

**Description**: Put shared entities in `app/shared/domain/` accessed by all features

**Pros**:
- Less duplication
- Single source of truth for entities
- Simpler data flow

**Cons**:
- Creates coupling between features
- Changes to shared entity affect all features
- Violates feature isolation
- Difficult to extract to microservices

**Why Not Chosen**: Creates exactly the coupling we're trying to avoid.

### Alternative 2: Direct Repository Access

**Description**: Allow features to import other features' repositories

```python
from app.features.services.adapters.repositories import ServiceRepository
```

**Pros**:
- Fewer abstractions
- Direct database access
- Can use joins

**Cons**:
- Tight coupling to provider's implementation
- Cannot test consumer without provider's database
- Violates encapsulation
- Risk of bypassing business rules

**Why Not Chosen**: Defeats the purpose of Clean Architecture.

### Alternative 3: Event-Driven Communication Only

**Description**: Features only communicate via events (no synchronous calls)

**Pros**:
- Ultimate decoupling
- Async by nature
- Good for eventual consistency

**Cons**:
- Cannot validate synchronously (e.g., "does this service exist?")
- Complex error handling
- Harder to reason about
- Eventual consistency not acceptable for bookings

**Why Not Chosen**: Need synchronous validation for bookings. Events are complementary (see [ADR-005](./005-event-driven-side-effects.md)).

### Alternative 4: API Gateway / BFF Pattern

**Description**: All cross-feature calls go through API layer

**Pros**:
- Clear separation
- Can use HTTP/REST
- Microservices ready

**Cons**:
- Network overhead in monolith
- More complex
- Serialization overhead
- Still need to solve interface definition

**Why Not Chosen**: Over-engineering for monolith. Good for microservices split later.

---

## Implementation

### Migration Path

1. **Identify Cross-Feature Dependencies**
   - ✅ Bookings → Services (validate services exist)
   - ✅ Bookings → Auth (validate customers exist)
   - ✅ Bookings → Vehicles (validate vehicles exist)
   - Services → Categories (validate category exists)

2. **Define Ports** (Consumer-owned interfaces)
   - ✅ `IExternalServiceValidator` in bookings
   - ✅ `IExternalCustomerValidator` in bookings
   - ✅ `IExternalVehicleValidator` in bookings

3. **Implement Adapters** (Call provider use cases)
   - ✅ `ExternalServiceValidatorAdapter` in bookings
   - ✅ `ExternalCustomerValidatorAdapter` in bookings
   - ✅ `ExternalVehicleValidatorAdapter` in bookings

4. **Wire Dependencies** (Dependency injection)
   - ✅ Update dependencies.py for each feature
   - ✅ Inject adapters into use cases

5. **Remove Direct Imports**
   - ✅ Search for cross-feature imports
   - ✅ Replace with port-based calls
   - ✅ Verify with import-linter

### Timeline

- Phase 1 (Identify): 2025-09-20 ✅
- Phase 2 (Define Ports): 2025-09-21 ✅
- Phase 3 (Implement): 2025-09-22 to 2025-09-24 ✅
- Phase 4 (Wire): 2025-09-25 ✅
- Phase 5 (Cleanup): 2025-09-26 ✅
- Complete: 2025-09-26

### Success Criteria

- ✅ Zero direct cross-feature imports (except adapters → use_cases)
- ✅ Import-linter passes all contracts
- ✅ All tests pass with mocked ports
- ✅ Can test each feature in isolation
- ✅ Documentation updated

---

## Related Decisions

- [ADR-001: Clean Architecture Adoption](./001-clean-architecture-adoption.md)
- [ADR-003: No Shared Transactions](./003-no-shared-transactions.md)
- [ADR-005: Event-Driven Side Effects](./005-event-driven-side-effects.md)

---

## References

- [Hexagonal Architecture Ports & Adapters](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design: Anti-Corruption Layer](https://docs.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer)
- [Architecture Guide: Feature Communication](../architecture/README.md#feature-communication)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-09-20 | Team | Initial draft and acceptance |
| 2025-09-26 | Team | Updated with implementation results |
| 2025-10-01 | Team | Added examples and clarifications |
