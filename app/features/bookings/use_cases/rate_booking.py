"""
Rate Booking Use Case
Implements RG-BOK-016: Quality rating system (1-5 stars, one-time only)
"""

from dataclasses import dataclass
from typing import Optional

from app.core.errors import NotFoundError, BusinessRuleViolationError, ValidationError
from app.features.bookings.domain import Booking, BookingStatus
from app.features.bookings.ports import (
    IBookingRepository,
    INotificationService,
    IEventService,
    ICacheService,
)


@dataclass
class RateBookingRequest:
    """Request to rate a completed booking."""
    booking_id: str
    customer_id: str
    rating: int  # 1-5 stars
    feedback: Optional[str] = None  # Optional feedback, max 1000 chars


@dataclass
class RateBookingResponse:
    """Response after rating a booking."""
    booking_id: str
    status: str
    rating: int
    feedback: Optional[str]
    rated_at: str


class RateBookingUseCase:
    """
    Use case for rating a completed booking.

    Business Rules:
    - RG-BOK-016: Rating scale 1-5 stars
    - RG-BOK-016: Only COMPLETED bookings can be rated
    - RG-BOK-016: One-time rating per booking (immutable once submitted)
    - RG-BOK-016: Optional feedback with 1000 character limit
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

    def execute(self, request: RateBookingRequest) -> RateBookingResponse:
        """Execute the rate booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Validate customer owns this booking
        if booking.customer_id != request.customer_id:
            raise BusinessRuleViolationError(
                "You can only rate your own bookings"
            )

        # Step 3: Validate booking status (only COMPLETED allowed)
        if booking.status != BookingStatus.COMPLETED:
            raise BusinessRuleViolationError(
                "Only completed bookings can be rated",
                rule="RG-BOK-016"
            )

        # Step 4: Validate rating has not been submitted already
        if getattr(booking, 'quality_rating', None) is not None:
            raise BusinessRuleViolationError(
                "This booking has already been rated. Ratings are immutable once submitted.",
                rule="RG-BOK-016"
            )

        # Step 5: Validate rating value (1-5)
        if not (1 <= request.rating <= 5):
            raise ValidationError(
                "Rating must be between 1 and 5 stars",
                field="rating"
            )

        # Step 6: Validate feedback length if provided
        if request.feedback and len(request.feedback) > 1000:
            raise ValidationError(
                "Feedback cannot exceed 1000 characters",
                field="feedback"
            )

        # Step 7: Rate the booking
        booking.rate_quality(request.rating, request.feedback)

        # Step 8: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 9: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 10: Publish domain event
        self._event_service.publish_booking_rated(
            updated_booking,
            request.rating,
            request.feedback
        )

        # Step 11: Send thank you notification
        try:
            self._notification_service.send_rating_thank_you(
                booking.customer_id,
                updated_booking,
                request.rating
            )
        except Exception:
            # Log but don't fail - notification is non-critical
            pass

        # Step 12: If rating is low (1-2 stars), notify management for follow-up
        if request.rating <= 2:
            try:
                self._notification_service.notify_management_low_rating(
                    updated_booking,
                    request.rating,
                    request.feedback
                )
            except Exception:
                # Log but don't fail
                pass

        return RateBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            rating=request.rating,
            feedback=request.feedback,
            rated_at=getattr(updated_booking, 'rated_at', updated_booking.updated_at).isoformat()
        )
