"""
Mark No-Show Use Case
Implements RG-BOK-011: No-show handling with 30-minute grace period and 100% fee
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
    IPaymentService,
)


@dataclass
class MarkNoShowRequest:
    """Request to mark a booking as no-show."""
    booking_id: str
    marked_by: str  # staff member ID (admin/manager/washer)
    reason: str = "customer_did_not_show"


@dataclass
class MarkNoShowResponse:
    """Response after marking booking as no-show."""
    booking_id: str
    status: str
    scheduled_at: str
    no_show_fee: float  # 100% of total price
    marked_by: str
    grace_period_end: str


class MarkNoShowUseCase:
    """
    Use case for marking a booking as no-show.

    Business Rules:
    - RG-BOK-011: 30-minute grace period after scheduled time
    - RG-BOK-011: 100% fee charged for no-show
    - Only CONFIRMED bookings can be marked as no-show
    """

    def __init__(
        self,
        booking_repository: IBookingRepository,
        notification_service: INotificationService,
        event_service: IEventService,
        cache_service: ICacheService,
        payment_service: IPaymentService,
    ):
        self._booking_repository = booking_repository
        self._notification_service = notification_service
        self._event_service = event_service
        self._cache_service = cache_service
        self._payment_service = payment_service

    def execute(self, request: MarkNoShowRequest) -> MarkNoShowResponse:
        """Execute the mark no-show use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Calculate grace period end
        from datetime import timedelta
        grace_period_minutes = getattr(booking, 'GRACE_PERIOD_MINUTES', 30)
        grace_period_end = booking.scheduled_at + timedelta(minutes=grace_period_minutes)

        # Step 3: Mark as no-show (validates state and grace period)
        booking.mark_no_show()

        # Add no-show reason
        booking.notes = f"{booking.notes or ''}\nNo-show reason: {request.reason}".strip()

        # Step 4: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 5: Process no-show fee (100% of total price)
        no_show_fee = updated_booking.total_price
        if updated_booking.payment_intent_id:
            try:
                self._payment_service.charge_no_show_fee(
                    updated_booking.payment_intent_id,
                    updated_booking.id,
                    no_show_fee,
                    request.reason
                )
            except Exception:
                # Log error but don't fail - payment can be processed later
                pass

        # Step 6: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 7: Publish domain event
        self._event_service.publish_booking_no_show(
            updated_booking,
            request.marked_by,
            request.reason
        )

        # Step 8: Send no-show notification to customer
        try:
            self._notification_service.send_no_show_notification(
                booking.customer_id,
                updated_booking,
                no_show_fee
            )
        except Exception:
            # Log but don't fail - notification is non-critical
            pass

        return MarkNoShowResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            scheduled_at=updated_booking.scheduled_at.isoformat(),
            no_show_fee=no_show_fee,
            marked_by=request.marked_by,
            grace_period_end=grace_period_end.isoformat()
        )
