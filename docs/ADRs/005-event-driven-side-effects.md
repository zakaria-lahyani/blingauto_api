# ADR-005: Event-Driven Architecture for Side Effects

**Status**: Accepted

**Date**: 2025-09-25

**Authors**: Development Team

**Stakeholders**: All developers, Technical leadership

---

## Context

### Background

Use cases need to trigger side effects after core operations:

- **After booking created**: Send confirmation email, update statistics, log analytics
- **After booking cancelled**: Send cancellation email, refund payment, update availability
- **After user registered**: Send welcome email, create default preferences
- **After booking completed**: Request review, update loyalty points

### Problem Statement

Where should side effects be triggered?

**Anti-Pattern 1: In Use Case**
```python
async def execute(self, request: CreateBookingRequest):
    # Core logic
    booking = await self._booking_repo.create(booking)
    await self._uow.commit()

    # Side effects mixed with core logic
    await self._email_service.send_confirmation(booking)
    await self._analytics_service.track_booking(booking)
    await self._notification_service.notify_admins(booking)
    # What if email fails? Should booking be rolled back?
```

**Anti-Pattern 2: In API Layer**
```python
@router.post("/bookings")
async def create_booking(use_case, email_service, analytics):
    booking = await use_case.execute(request)

    # Business logic in API layer!
    await email_service.send(booking)
    await analytics.track(booking)
```

Problems:
- Use case becomes bloated
- Mixing core logic with side effects
- Hard to test
- Unclear transaction boundaries
- Difficult to add new side effects

---

## Decision

We will use **Event-Driven Architecture** where:

1. **Use cases emit domain events** after core operations
2. **Event handlers execute side effects** asynchronously
3. **Events are fire-and-forget** (do not affect core transaction)
4. **Events use in-memory bus** (for now, can upgrade to message queue)

### Architecture

```
Use Case → Emit Event → Event Bus → Event Handlers
                                    ├─ Email Handler
                                    ├─ Analytics Handler
                                    └─ Notification Handler
```

### Implementation Pattern

**Step 1: Define Domain Event**
```python
# app/features/bookings/domain/events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class BookingCreatedEvent:
    """Emitted when booking is created."""
    booking_id: str
    customer_id: str
    service_ids: list[str]
    scheduled_at: datetime
    total_price: Decimal
    occurred_at: datetime
```

**Step 2: Use Case Emits Event**
```python
# app/features/bookings/use_cases/create_booking.py
from app.core.events import EventBus
from app.features.bookings.domain.events import BookingCreatedEvent

class CreateBookingUseCase:
    def __init__(
        self,
        booking_repo: IBookingRepository,
        uow: IUnitOfWork,
        event_bus: EventBus,
    ):
        self._booking_repo = booking_repo
        self._uow = uow
        self._event_bus = event_bus

    async def execute(self, request: CreateBookingRequest):
        # Core logic with transaction
        async with self._uow:
            booking = await self._booking_repo.create(booking_entity)
            await self._uow.commit()

        # Emit event (outside transaction, fire-and-forget)
        await self._event_bus.publish(
            BookingCreatedEvent(
                booking_id=booking.id,
                customer_id=booking.customer_id,
                service_ids=booking.service_ids,
                scheduled_at=booking.scheduled_at,
                total_price=booking.total_price,
                occurred_at=datetime.utcnow(),
            )
        )

        return CreateBookingResponse(booking_id=booking.id)
```

**Step 3: Register Event Handlers**
```python
# app/features/bookings/adapters/event_handlers.py
from app.core.events import event_handler
from app.features.bookings.domain.events import BookingCreatedEvent
from app.features.bookings.ports.services import INotificationService

@event_handler(BookingCreatedEvent)
async def send_booking_confirmation(
    event: BookingCreatedEvent,
    notification_service: INotificationService,
):
    """Send confirmation email when booking created."""
    try:
        await notification_service.send_booking_confirmation(
            booking_id=event.booking_id,
            customer_id=event.customer_id,
        )
    except Exception as e:
        # Log error but don't fail
        logger.error(f"Failed to send confirmation: {e}")

@event_handler(BookingCreatedEvent)
async def track_booking_analytics(
    event: BookingCreatedEvent,
    analytics_service: IAnalyticsService,
):
    """Track booking in analytics."""
    try:
        await analytics_service.track_event(
            event_type="booking_created",
            booking_id=event.booking_id,
            properties={
                "total_price": float(event.total_price),
                "service_count": len(event.service_ids),
            },
        )
    except Exception as e:
        logger.error(f"Failed to track analytics: {e}")
```

**Step 4: Event Bus Implementation**
```python
# app/core/events/event_bus.py
from typing import Callable, Type, Any
import asyncio

class EventBus:
    """In-memory event bus for domain events."""

    def __init__(self):
        self._handlers: dict[Type, list[Callable]] = {}

    def subscribe(self, event_type: Type, handler: Callable):
        """Register event handler."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Any):
        """Publish event to all handlers."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        # Execute handlers concurrently
        tasks = [handler(event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

def event_handler(event_type: Type):
    """Decorator for event handlers."""
    def decorator(func: Callable):
        # Register handler on startup
        event_bus.subscribe(event_type, func)
        return func
    return decorator
```

### Key Principles

1. **Events Are Facts**: Events represent something that happened
   - Named in past tense: `BookingCreated`, `PaymentProcessed`
   - Immutable
   - Contain all necessary data

2. **Fire and Forget**: Event publishing doesn't block use case
   - Use case doesn't wait for handlers
   - Handler failures don't fail use case
   - Eventual consistency

3. **Handlers Are Independent**: Each handler can fail independently
   - Email fails → booking still created
   - Analytics fails → email still sent
   - Retry mechanisms in handlers

4. **No Event Loops**: Events don't trigger other events directly
   - Prevents infinite loops
   - Clear causality chain

---

## Consequences

### Positive Consequences

- **Separation of Concerns**: Core logic separated from side effects
  ```python
  # Use case: Only core logic
  async def execute(self, request):
      booking = await self._create_booking(request)
      await self._event_bus.publish(BookingCreatedEvent(...))
      return response

  # Handler: Only side effect
  @event_handler(BookingCreatedEvent)
  async def send_email(event):
      await email_service.send(...)
  ```

- **Extensibility**: Easy to add new side effects
  ```python
  # Add new handler without modifying use case
  @event_handler(BookingCreatedEvent)
  async def new_side_effect(event):
      # New functionality
  ```

- **Testability**: Test core logic without side effects
  ```python
  # Test use case
  def test_create_booking():
      use_case = CreateBookingUseCase(repo, uow, mock_event_bus)
      result = await use_case.execute(request)
      # Verify event was published
      mock_event_bus.assert_published(BookingCreatedEvent)
  ```

- **Resilience**: Side effect failures don't affect core operations
  - Booking created even if email fails
  - Can retry failed handlers
  - Monitor handler failures separately

- **Feature Isolation**: Cross-feature communication via events
  - Bookings emits `BookingCreatedEvent`
  - Services feature listens and updates availability
  - No direct dependency

### Negative Consequences

- **Eventual Consistency**: Side effects happen later
  - Email might arrive after API response
  - Brief inconsistency window
  - **Mitigation**: Acceptable for most use cases, retry mechanisms

- **Debugging Complexity**: Harder to trace event flow
  - Need to find which handlers listen to event
  - Async execution makes debugging harder
  - **Mitigation**: Logging, tracing, event monitoring

- **No Transactional Guarantees**: Events might fail
  ```python
  # Booking created but email fails
  # → Need retry or compensating action
  ```
  - **Mitigation**: Retry mechanisms, idempotency, monitoring

- **Testing Complexity**: Need to test event handlers separately
  - **Mitigation**: Reusable test fixtures, clear patterns

### Neutral Consequences

- **In-Memory Bus**: Current implementation is in-memory
  - Events lost if service crashes before handlers execute
  - Not suitable for critical events
  - **Future**: Can upgrade to message queue (RabbitMQ, Redis)

---

## Alternatives Considered

### Alternative 1: Side Effects in Use Case

**Description**: Execute side effects directly in use case

```python
async def execute(self, request):
    booking = await self._repo.create(booking)
    await self._email.send(booking)
    await self._analytics.track(booking)
    return response
```

**Pros**:
- Simple, synchronous
- Easy to trace
- Transactional guarantees

**Cons**:
- Use case becomes bloated
- Hard to test
- Core logic mixed with side effects
- Adding side effects requires modifying use case

**Why Not Chosen**: Violates single responsibility, hard to extend.

### Alternative 2: Message Queue (RabbitMQ/Kafka)

**Description**: Use external message broker for events

**Pros**:
- Persistent events
- Guaranteed delivery
- Scalable
- Cross-service communication

**Cons**:
- Infrastructure complexity
- External dependency
- Operational overhead
- Over-engineering for monolith

**Why Not Chosen**: Over-engineering for current needs. Can migrate later if needed.

### Alternative 3: Database Outbox Pattern

**Description**: Store events in database, process in background

```sql
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR,
    payload JSONB,
    processed BOOLEAN
);
```

**Pros**:
- Transactional guarantees
- Persistent events
- Guaranteed delivery
- No external dependencies

**Cons**:
- More complex
- Need background worker
- Database write overhead

**Why Not Chosen**: Good pattern but over-engineering for v1. Consider for v2.

### Alternative 4: Webhooks

**Description**: HTTP callbacks to registered endpoints

**Pros**:
- Standard pattern
- External integration friendly
- Decoupled

**Cons**:
- Network overhead
- Reliability issues
- Need retry logic
- Not for internal events

**Why Not Chosen**: Webhooks are for external integrations, not internal architecture.

---

## Implementation

### Event Types

```python
# app/features/bookings/domain/events.py

@dataclass
class BookingCreatedEvent:
    booking_id: str
    customer_id: str
    occurred_at: datetime

@dataclass
class BookingConfirmedEvent:
    booking_id: str
    confirmed_at: datetime

@dataclass
class BookingCancelledEvent:
    booking_id: str
    cancelled_by: str
    reason: str
    refund_amount: Decimal

@dataclass
class BookingCompletedEvent:
    booking_id: str
    completed_at: datetime
    actual_duration_minutes: int
```

### Event Handlers

```python
# Email notifications
@event_handler(BookingCreatedEvent)
async def send_confirmation_email(event, email_service):
    await email_service.send_booking_confirmation(event.booking_id)

@event_handler(BookingCancelledEvent)
async def send_cancellation_email(event, email_service):
    await email_service.send_booking_cancellation(event.booking_id)

# Analytics tracking
@event_handler(BookingCreatedEvent)
async def track_booking_created(event, analytics):
    await analytics.track("booking_created", event.booking_id)

# Cross-feature updates (eventual consistency)
@event_handler(BookingCreatedEvent)
async def update_service_stats(event, service_repo):
    # Services feature listens to booking events
    for service_id in event.service_ids:
        await service_repo.increment_booking_count(service_id)
```

### Error Handling

```python
@event_handler(BookingCreatedEvent)
async def send_email_with_retry(event, email_service):
    """Handler with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await email_service.send(event.booking_id)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                # Log to error tracking
                logger.error(f"Failed to send email after {max_retries} attempts: {e}")
                await error_tracker.capture(e, context={"event": event})
            else:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Testing

```python
# Test use case emits event
async def test_create_booking_emits_event():
    mock_event_bus = Mock()
    use_case = CreateBookingUseCase(repo, uow, mock_event_bus)

    await use_case.execute(request)

    # Verify event published
    mock_event_bus.publish.assert_called_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert isinstance(event, BookingCreatedEvent)
    assert event.booking_id == "test-123"

# Test handler
async def test_email_handler():
    mock_email = Mock()
    event = BookingCreatedEvent(booking_id="123", ...)

    await send_confirmation_email(event, mock_email)

    mock_email.send_booking_confirmation.assert_called_once_with("123")
```

### Migration Path

1. **Implement Event Bus** ✅
   - In-memory implementation
   - Registration mechanism
   - Async publishing

2. **Extract Side Effects** ✅
   - Move email sending to handlers
   - Move analytics to handlers
   - Move logging to handlers

3. **Add Event Types** ✅
   - Define domain events
   - Document event schemas
   - Version events

4. **Test Coverage** ✅
   - Test event emission
   - Test handlers independently
   - Integration tests

### Timeline

- Phase 1 (Event Bus): 2025-09-25 ✅
- Phase 2 (Extract Side Effects): 2025-09-26 ✅
- Phase 3 (Add Events): 2025-09-27 ✅
- Phase 4 (Testing): 2025-09-28 ✅
- Complete: 2025-09-28

### Success Criteria

- ✅ All side effects moved to event handlers
- ✅ Use cases only emit events
- ✅ Handlers tested independently
- ✅ Event bus working
- ✅ Documentation complete
- 🔄 Monitoring in place (future)

---

## Future Enhancements

### Message Queue Integration

When scale requires:

```python
# Upgrade to Redis/RabbitMQ
class MessageQueueEventBus(EventBus):
    async def publish(self, event):
        await redis.publish(
            channel=event.__class__.__name__,
            message=json.dumps(event),
        )
```

### Event Sourcing

If event history needed:

```python
# Store all events
class EventStore:
    async def append(self, event):
        await db.events.insert({
            "event_type": event.__class__.__name__,
            "payload": event.dict(),
            "timestamp": datetime.utcnow(),
        })
```

---

## Related Decisions

- [ADR-001: Clean Architecture Adoption](./001-clean-architecture-adoption.md)
- [ADR-002: Consumer-Owned Ports Pattern](./002-consumer-owned-ports-pattern.md)
- [ADR-003: No Shared Transactions](./003-no-shared-transactions.md)

---

## References

- [Domain Events by Martin Fowler](https://martinfowler.com/eaaDev/DomainEvent.html)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Implementing Domain-Driven Design by Vaughn Vernon](https://vaughnvernon.com/books/)
- [Architecture Guide: Events](../architecture/README.md#events)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-09-25 | Team | Initial draft and acceptance |
| 2025-09-28 | Team | Updated with implementation results |
| 2025-10-01 | Team | Added error handling and testing examples |
