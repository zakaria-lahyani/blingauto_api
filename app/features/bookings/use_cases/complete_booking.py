"""
Complete Booking Use Case
Implements RG-BOK-008: State transition IN_PROGRESS → COMPLETED
Implements RG-BOK-015: Overtime calculation
"""

from dataclasses import dataclass
from datetime import datetime
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
class CompleteBookingRequest:
    """Request to complete a booking."""
    booking_id: str
    completed_by: str  # staff member ID (admin/manager/washer)
    actual_end_time: Optional[datetime] = None  # If not provided, uses current time


@dataclass
class CompleteBookingResponse:
    """Response after completing a booking."""
    booking_id: str
    status: str
    actual_end_time: str
    actual_duration: int  # Actual duration in minutes
    overtime_fee: float  # RG-BOK-015: Overtime charges
    final_price: float
    completed_by: str


class CompleteBookingUseCase:
    """
    Use case for completing an in-progress booking.
    Records actual end time and calculates overtime fees if applicable.

    Business Rules:
    - RG-BOK-008: Booking states
    - RG-BOK-009: Only IN_PROGRESS → COMPLETED transition allowed
    - RG-BOK-015: Overtime fee calculation
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

    def execute(self, request: CompleteBookingRequest) -> CompleteBookingResponse:
        """Execute the complete booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Validate state transition (IN_PROGRESS → COMPLETED)
        BookingStateTransitionPolicy.validate_transition(
            booking.status,
            BookingStatus.COMPLETED
        )

        # Step 3: Complete the service (calculates overtime if applicable)
        booking.complete_service(request.actual_end_time)

        # Step 4: Calculate actual duration
        actual_duration = 0
        if booking.actual_start_time and booking.actual_end_time:
            duration_delta = booking.actual_end_time - booking.actual_start_time
            actual_duration = int(duration_delta.total_seconds() / 60)

        # Step 5: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 6: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 7: Publish domain event
        self._event_service.publish_booking_completed(
            updated_booking,
            request.completed_by
        )

        # Step 8: Send completion notification to customer
        try:
            self._notification_service.send_booking_completion(
                booking.customer_id,
                updated_booking,
                "Your service has been completed. Please rate your experience!"
            )
        except Exception:
            # Log but don't fail - notification is non-critical
            pass

        # Calculate overtime fee (if any)
        overtime_fee = getattr(updated_booking, 'overtime_fee', 0.0) or 0.0
        final_price = updated_booking.total_price + overtime_fee

        return CompleteBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            actual_end_time=updated_booking.actual_end_time.isoformat() if updated_booking.actual_end_time else None,
            actual_duration=actual_duration,
            overtime_fee=overtime_fee,
            final_price=final_price,
            completed_by=request.completed_by
        )
