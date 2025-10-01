# ADR-003: No Shared Database Transactions Across Features

**Status**: Accepted

**Date**: 2025-09-20

**Authors**: Development Team

**Stakeholders**: All developers, Technical leadership

---

## Context

### Background

In distributed systems and microservices, shared transactions across service boundaries are an anti-pattern. Even in monoliths, maintaining transactional boundaries is important for:

- Feature independence
- Future microservices migration
- Clear ownership
- Avoiding distributed transaction complexity

### Problem Statement

When a booking is created, we need to:
1. Validate service exists (Services feature)
2. Validate customer exists (Auth feature)
3. Validate vehicle exists (Vehicles feature)
4. Create booking record (Bookings feature)
5. Potentially update service availability
6. Send confirmation email

Should all these operations be in a single database transaction?

### Example Scenario

```python
# Anti-pattern: Shared transaction across features
async with db_transaction:
    # Bookings feature writes
    booking = await booking_repo.create(booking)

    # Services feature writes (different feature!)
    await service_repo.update_availability(service_id)

    # Auth feature writes (different feature!)
    await user_repo.update_booking_count(customer_id)

    await db_transaction.commit()
```

Problems:
- Features are coupled via shared transaction
- Cannot extract to microservices
- Lock contention across features
- Unclear ownership

---

## Decision

We will enforce **one database transaction per use case**, with these rules:

1. **One Transaction Boundary**: Each use case manages exactly one transaction
2. **Single Feature Writes**: Only write to own feature's tables in transaction
3. **Read-Only External Calls**: Cross-feature calls during transaction are read-only
4. **Eventual Consistency**: Use events for cross-feature updates
5. **Compensating Actions**: Handle failures via sagas or compensating transactions

### Pattern

```python
class CreateBookingUseCase:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        service_validator: IExternalServiceValidator,  # Read-only
        uow: IUnitOfWork,
    ):
        self._booking_repo = booking_repo
        self._service_validator = service_validator
        self._uow = uow

    async def execute(self, request: CreateBookingRequest):
        # 1. Validate (read-only, outside transaction)
        if not await self._service_validator.validate_service_exists(request.service_id):
            raise BusinessRuleViolationError("Service not found")

        # 2. Single transaction for bookings feature only
        async with self._uow:
            # Create booking (write to bookings tables only)
            booking = await self._booking_repo.create(booking_entity)

            # Commit bookings feature changes
            await self._uow.commit()

        # 3. Emit event for side effects (eventual consistency)
        await event_bus.publish(BookingCreatedEvent(booking_id=booking.id))

        return CreateBookingResponse(booking_id=booking.id)
```

### Key Principles

1. **Transaction = Use Case**: One-to-one mapping
2. **Feature Ownership**: Only write to own tables
3. **Validation Before Transaction**: Read-only checks first
4. **Events for Side Effects**: Asynchronous updates via events
5. **Idempotency**: Handle event replay scenarios

---

## Consequences

### Positive Consequences

- **Feature Independence**: Each feature manages its own data
  - Clear ownership boundaries
  - No cross-feature lock contention
  - Can extract to microservices without transaction changes

- **Scalability**: Shorter transactions, less lock time
  - Better database performance
  - Reduced deadlock risk
  - Parallel processing possible

- **Microservices Ready**: Already follows distributed system patterns
  - No refactoring needed for service split
  - Events already in place
  - Compensating actions defined

- **Testability**: Transaction scope is explicit
  - Easy to test transaction boundaries
  - Clear rollback behavior
  - Predictable state changes

### Negative Consequences

- **Eventual Consistency**: Cross-feature updates are asynchronous
  - Brief inconsistency window
  - Need to handle event failures
  - **Mitigation**: Event retry, monitoring, compensating actions

- **No Atomic Cross-Feature Updates**: Cannot guarantee atomicity
  ```python
  # This scenario requires careful handling:
  # 1. Booking created successfully
  # 2. Service availability update fails
  # → Need compensating action to cancel booking
  ```
  - **Mitigation**: Saga pattern, compensating transactions

- **Complexity**: More moving parts
  - Event handlers
  - Compensating actions
  - Idempotency checks
  - **Mitigation**: Reusable patterns, clear documentation

### Neutral Consequences

- **Event-Driven**: Natural fit with event architecture
- **Monitoring**: Need to track event processing

---

## Alternatives Considered

### Alternative 1: Shared Transaction Across Features

**Description**: Allow use cases to span multiple feature transactions

```python
async with shared_transaction:
    await bookings_repo.create(booking)
    await services_repo.update_availability(service_id)
    await users_repo.update_stats(customer_id)
    await shared_transaction.commit()
```

**Pros**:
- Atomic consistency
- Simpler error handling
- No eventual consistency

**Cons**:
- Tight coupling between features
- Lock contention across features
- Cannot extract to microservices
- Violates feature independence

**Why Not Chosen**: Defeats the purpose of feature isolation and blocks microservices migration.

### Alternative 2: Two-Phase Commit (2PC)

**Description**: Use distributed transaction protocol

**Pros**:
- Atomic across features
- Strong consistency

**Cons**:
- Complex implementation
- Performance overhead
- Not supported by all databases
- Blocking protocol
- Network partition issues

**Why Not Chosen**: Over-engineering for monolith, problematic for distributed systems.

### Alternative 3: No Transaction Boundaries

**Description**: Let each repository method auto-commit

**Pros**:
- Simplest implementation
- No transaction management

**Cons**:
- Cannot rollback multiple operations
- Inconsistent state on errors
- No ACID guarantees

**Why Not Chosen**: Need atomicity within feature boundaries.

---

## Implementation

### Transaction Management

**Unit of Work Pattern**:
```python
# app/core/database/uow.py
class UnitOfWork:
    """Unit of Work for managing database transactions."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
```

**Use Case Pattern**:
```python
class CreateBookingUseCase:
    async def execute(self, request: CreateBookingRequest):
        # Validation (no transaction)
        await self._validate(request)

        # Transaction scope
        async with self._uow:
            # All writes here
            booking = await self._booking_repo.create(...)
            await self._uow.commit()

        # Post-transaction (events)
        await self._publish_events(booking)

        return response
```

### Event-Driven Updates

**Publish Events**:
```python
# After booking created
await event_bus.publish(BookingCreatedEvent(
    booking_id=booking.id,
    service_id=booking.service_id,
    customer_id=booking.customer_id,
))
```

**Handle Events**:
```python
# In services feature
@event_handler(BookingCreatedEvent)
async def on_booking_created(event: BookingCreatedEvent):
    """Update service availability after booking created."""
    async with services_uow:
        service = await service_repo.get_by_id(event.service_id)
        service.increment_booking_count()
        await service_repo.update(service)
        await services_uow.commit()
```

### Compensating Actions

**Handle Failures**:
```python
class CreateBookingUseCase:
    async def execute(self, request: CreateBookingRequest):
        try:
            # Create booking
            async with self._uow:
                booking = await self._booking_repo.create(booking)
                await self._uow.commit()

            # Publish event
            await event_bus.publish(BookingCreatedEvent(...))

        except EventPublishError:
            # Compensate: Mark booking as failed
            await self._cancel_booking(booking.id, reason="event_failed")
            raise
```

### Migration Path

1. **Audit Existing Transactions** ✅
   - Found all use cases already follow single transaction
   - No cross-feature writes detected

2. **Add Unit of Work** ✅
   - Implemented UnitOfWork class
   - Injected into all use cases

3. **Convert to Events** ✅
   - Side effects moved to event handlers
   - Email sending via events
   - Statistics updates via events

4. **Add Compensating Actions** ✅
   - Cancel booking on failure
   - Refund on cancellation
   - Rollback availability

### Timeline

- Phase 1 (Audit): 2025-09-20 ✅
- Phase 2 (UoW): 2025-09-21 ✅
- Phase 3 (Events): 2025-09-22 to 2025-09-24 ✅
- Phase 4 (Compensating): 2025-09-25 ✅
- Complete: 2025-09-25

### Success Criteria

- ✅ Each use case has exactly one transaction
- ✅ No cross-feature writes in transactions
- ✅ Events handle all side effects
- ✅ Compensating actions defined
- ✅ Tests verify transaction boundaries

---

## Related Decisions

- [ADR-001: Clean Architecture Adoption](./001-clean-architecture-adoption.md)
- [ADR-002: Consumer-Owned Ports Pattern](./002-consumer-owned-ports-pattern.md)
- [ADR-005: Event-Driven Side Effects](./005-event-driven-side-effects.md)

---

## References

- [Microservices Patterns: Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Domain-Driven Design: Aggregates and Transaction Boundaries](https://martinfowler.com/bliki/DDD_Aggregate.html)
- [Designing Data-Intensive Applications by Martin Kleppmann](https://dataintensive.net/)
- [Architecture Guide](../architecture/README.md)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-09-20 | Team | Initial draft and acceptance |
| 2025-09-25 | Team | Updated with implementation results |
| 2025-10-01 | Team | Added compensating action examples |
