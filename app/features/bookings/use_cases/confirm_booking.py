"""
Confirm Booking Use Case
Implements RG-BOK-008: State transition PENDING → CONFIRMED
"""

from dataclasses import dataclass
from typing import Optional

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
class ConfirmBookingRequest:
    """Request to confirm a booking."""
    booking_id: str
    confirmed_by: str  # staff member ID (admin/manager/washer)
    notes: Optional[str] = None


@dataclass
class ConfirmBookingResponse:
    """Response after confirming a booking."""
    booking_id: str
    status: str
    confirmed_at: str
    confirmed_by: str


class ConfirmBookingUseCase:
    """
    Use case for confirming a pending booking.
    Only staff members (admin, manager, washer) can confirm bookings.

    Business Rules:
    - RG-BOK-008: Booking states
    - RG-BOK-009: Only PENDING → CONFIRMED transition allowed
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

    def execute(self, request: ConfirmBookingRequest) -> ConfirmBookingResponse:
        """Execute the confirm booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Validate state transition (PENDING → CONFIRMED)
        BookingStateTransitionPolicy.validate_transition(
            booking.status,
            BookingStatus.CONFIRMED
        )

        # Step 3: Confirm the booking
        booking.confirm()

        # Add confirmation notes if provided
        if request.notes:
            booking.notes = f"{booking.notes or ''}\nConfirmation notes: {request.notes}".strip()

        # Step 4: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 5: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 6: Publish domain event
        self._event_service.publish_booking_confirmed(
            updated_booking,
            request.confirmed_by
        )

        # Step 7: Send confirmation notification to customer
        try:
            self._notification_service.send_booking_status_update(
                booking.customer_id,
                updated_booking,
                "Your booking has been confirmed"
            )
        except Exception as e:
            # Log but don't fail - notification is non-critical
            pass

        return ConfirmBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            confirmed_at=updated_booking.confirmed_at.isoformat() if updated_booking.confirmed_at else None,
            confirmed_by=request.confirmed_by
        )
