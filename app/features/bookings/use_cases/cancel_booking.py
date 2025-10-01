from dataclasses import dataclass
from typing import Optional

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.bookings.domain import Booking
from app.features.bookings.domain.policies import BookingCancellationPolicy
from app.features.bookings.ports import (
    IBookingRepository,
    ICustomerRepository,
    INotificationService,
    IPaymentService,
    IEventService,
    ICacheService,
)


@dataclass
class CancelBookingRequest:
    booking_id: str
    cancelled_by: str  # customer_id or admin_id
    reason: str = "cancelled_by_customer"


@dataclass
class CancelBookingResponse:
    booking_id: str
    status: str
    refund_amount: Optional[float] = None
    refund_status: str = "none"


class CancelBookingUseCase:
    """Use case for cancelling an existing booking."""
    
    def __init__(
        self,
        booking_repository: IBookingRepository,
        customer_repository: ICustomerRepository,
        notification_service: INotificationService,
        payment_service: IPaymentService,
        event_service: IEventService,
        cache_service: ICacheService,
    ):
        self._booking_repository = booking_repository
        self._customer_repository = customer_repository
        self._notification_service = notification_service
        self._payment_service = payment_service
        self._event_service = event_service
        self._cache_service = cache_service
    
    def execute(self, request: CancelBookingRequest) -> CancelBookingResponse:
        """Execute the cancel booking use case."""
        
        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")
        
        # Step 2: Validate cancellation is allowed
        BookingCancellationPolicy.validate_cancellation_allowed(booking)
        
        # Step 3: Validate user can cancel this booking
        customer_data = self._customer_repository.get_by_id(request.cancelled_by)
        if customer_data:
            # Customer cancelling their own booking
            if booking.customer_id != request.cancelled_by:
                raise BusinessRuleViolationError(
                    "Customer can only cancel their own bookings"
                )
        else:
            # Admin cancellation - would need admin validation here
            # For now, assume cancelled_by is validated externally
            pass
        
        # Step 4: Calculate refund amount based on cancellation policy
        refund_amount = BookingCancellationPolicy.calculate_refund_amount(booking)
        
        # Step 5: Cancel the booking
        booking.cancel(request.cancelled_by, request.reason)
        
        # Step 6: Save the updated booking
        updated_booking = self._booking_repository.update(booking)
        
        # Step 7: Process refund if applicable
        refund_status = "none"
        if refund_amount > 0 and booking.payment_intent_id:
            try:
                refund_result = self._payment_service.refund_payment(
                    booking.payment_intent_id,
                    booking.id,
                    refund_amount,
                    request.reason,
                )
                refund_status = refund_result.get("status", "pending")
            except Exception:
                # Log error but don't fail the cancellation
                refund_status = "failed"
                refund_amount = 0.0
        
        # Step 8: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)
        
        # Step 9: Publish domain event
        self._event_service.publish_booking_cancelled(
            updated_booking, request.cancelled_by, request.reason
        )
        
        # Step 10: Send cancellation notification
        customer_data = self._customer_repository.get_by_id(booking.customer_id)
        if customer_data:
            self._notification_service.send_booking_cancellation(
                customer_data["email"],
                updated_booking,
                customer_data,
            )
        
        return CancelBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            refund_amount=refund_amount,
            refund_status=refund_status,
        )