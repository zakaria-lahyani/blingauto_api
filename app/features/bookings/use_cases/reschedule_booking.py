"""
Reschedule Booking Use Case
Implements RG-BOK-012: Booking rescheduling with minimum notice
"""

from dataclasses import dataclass
from datetime import datetime

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.bookings.domain import Booking, BookingStatus
from app.features.bookings.ports import (
    IBookingRepository,
    INotificationService,
    IEventService,
    ICacheService,
    ILockService,
)


@dataclass
class RescheduleBookingRequest:
    """Request to reschedule a booking."""
    booking_id: str
    new_scheduled_at: datetime
    rescheduled_by: str  # customer_id or staff_id
    reason: str = ""


@dataclass
class RescheduleBookingResponse:
    """Response after rescheduling a booking."""
    booking_id: str
    status: str
    old_scheduled_at: str
    new_scheduled_at: str
    rescheduled_by: str


class RescheduleBookingUseCase:
    """
    Use case for rescheduling a booking.

    Business Rules:
    - RG-BOK-012: Minimum 2 hours notice required
    - RG-BOK-012: Only PENDING or CONFIRMED bookings can be rescheduled
    - Must check availability for new time slot
    """

    def __init__(
        self,
        booking_repository: IBookingRepository,
        notification_service: INotificationService,
        event_service: IEventService,
        cache_service: ICacheService,
        lock_service: ILockService,
    ):
        self._booking_repository = booking_repository
        self._notification_service = notification_service
        self._event_service = event_service
        self._cache_service = cache_service
        self._lock_service = lock_service

    def execute(self, request: RescheduleBookingRequest) -> RescheduleBookingResponse:
        """Execute the reschedule booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Save old scheduled time for response
        old_scheduled_at = booking.scheduled_at

        # Step 3: Acquire lock for new time slot
        lock_id = self._lock_service.acquire_time_slot_lock(
            request.new_scheduled_at,
            booking.estimated_duration_minutes,
            booking.booking_type.value,
            timeout=30,
        )

        if not lock_id:
            raise BusinessRuleViolationError(
                "New time slot is being booked by another customer. Please try again."
            )

        try:
            # Step 4: Check for scheduling conflicts at new time
            conflicting_bookings = self._booking_repository.find_conflicting_bookings(
                request.new_scheduled_at,
                booking.estimated_duration_minutes,
                booking.booking_type.value,
            )

            if conflicting_bookings:
                raise BusinessRuleViolationError(
                    f"New time slot conflicts with existing booking at {request.new_scheduled_at}"
                )

            # Step 5: Reschedule the booking (validates state and minimum notice)
            booking.reschedule(request.new_scheduled_at)

            # Add reschedule reason if provided
            if request.reason:
                booking.notes = f"{booking.notes or ''}\nRescheduled: {request.reason}".strip()

            # Step 6: Save the updated booking
            updated_booking = self._booking_repository.update(booking)

            # Step 7: Invalidate cache
            self._cache_service.delete_booking(booking.id)
            self._cache_service.invalidate_customer_cache(booking.customer_id)

            # Step 8: Publish domain event
            self._event_service.publish_booking_rescheduled(
                updated_booking,
                old_scheduled_at,
                request.new_scheduled_at,
                request.rescheduled_by
            )

            # Step 9: Send rescheduling notification
            try:
                self._notification_service.send_booking_reschedule(
                    booking.customer_id,
                    updated_booking,
                    old_scheduled_at,
                    request.new_scheduled_at
                )
            except Exception:
                # Log but don't fail - notification is non-critical
                pass

            return RescheduleBookingResponse(
                booking_id=updated_booking.id,
                status=updated_booking.status.value,
                old_scheduled_at=old_scheduled_at.isoformat(),
                new_scheduled_at=updated_booking.scheduled_at.isoformat(),
                rescheduled_by=request.rescheduled_by
            )

        finally:
            # Always release the lock
            if lock_id:
                self._lock_service.release_lock(lock_id)
