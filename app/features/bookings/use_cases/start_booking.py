"""
Start Booking Use Case
Implements RG-BOK-008: State transition CONFIRMED → IN_PROGRESS
"""

from dataclasses import dataclass
from datetime import datetime

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.bookings.domain import Booking, BookingStatus
from app.features.bookings.domain.policies import BookingStateTransitionPolicy
from app.features.bookings.ports import (
    IBookingRepository,
    INotificationService,
    IEventService,
    ICacheService,
)


@dataclass
class StartBookingRequest:
    """Request to start a booking."""
    booking_id: str
    started_by: str  # staff member ID (admin/manager/washer)


@dataclass
class StartBookingResponse:
    """Response after starting a booking."""
    booking_id: str
    status: str
    actual_start_time: str
    started_by: str


class StartBookingUseCase:
    """
    Use case for starting a confirmed booking.
    Marks the booking as IN_PROGRESS and records actual start time.

    Business Rules:
    - RG-BOK-008: Booking states
    - RG-BOK-009: Only CONFIRMED → IN_PROGRESS transition allowed
    """

    def __init__(
        self,
        booking_repository: IBookingRepository,
        notification_service: INotificationService,
        event_service: IEventService,
        cache_service: ICacheService,
    ):
        self._booking_repository = booking_repository
        self._notification_service = notification_service
        self._event_service = event_service
        self._cache_service = cache_service

    def execute(self, request: StartBookingRequest) -> StartBookingResponse:
        """Execute the start booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Validate state transition (CONFIRMED → IN_PROGRESS)
        BookingStateTransitionPolicy.validate_transition(
            booking.status,
            BookingStatus.IN_PROGRESS
        )

        # Step 3: Start the service
        booking.start_service()

        # Step 4: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 5: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 6: Publish domain event
        self._event_service.publish_booking_started(
            updated_booking,
            request.started_by
        )

        # Step 7: Send notification to customer
        try:
            self._notification_service.send_booking_status_update(
                booking.customer_id,
                updated_booking,
                "Your service has started"
            )
        except Exception:
            # Log but don't fail - notification is non-critical
            pass

        return StartBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            actual_start_time=updated_booking.actual_start_time.isoformat() if updated_booking.actual_start_time else None,
            started_by=request.started_by
        )
