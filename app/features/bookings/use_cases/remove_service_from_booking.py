"""
Remove Service from Booking Use Case
Implements RG-BOK-014: Remove services from pending bookings only
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from app.core.errors import NotFoundError, BusinessRuleViolationError, ValidationError
from app.features.bookings.domain import Booking, BookingStatus
from app.features.bookings.ports import (
    IBookingRepository,
    INotificationService,
    IEventService,
    ICacheService,
)


@dataclass
class RemoveServiceFromBookingRequest:
    """Request to remove services from a booking."""
    booking_id: str
    service_ids: List[str]  # List of service IDs to remove
    removed_by: str  # customer_id or staff_id


@dataclass
class RemoveServiceFromBookingResponse:
    """Response after removing services from a booking."""
    booking_id: str
    status: str
    removed_services: List[Dict[str, Any]]
    new_total_price: float
    new_estimated_duration: int
    total_services_count: int


class RemoveServiceFromBookingUseCase:
    """
    Use case for removing services from an existing booking.

    Business Rules:
    - RG-BOK-014: Only PENDING bookings can have services removed
    - RG-BOK-001: Minimum 1 service must remain
    - Recalculates total price and duration
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

    def execute(self, request: RemoveServiceFromBookingRequest) -> RemoveServiceFromBookingResponse:
        """Execute the remove service from booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Validate booking state (only PENDING allowed)
        if booking.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Can only remove services from pending bookings, current status: {booking.status.value}",
                rule="RG-BOK-014"
            )

        # Step 3: Find services to remove
        removed_services = []
        for service_id in request.service_ids:
            # Find the service in the booking
            service_found = None
            for service in booking.services:
                if service.service_id == service_id:
                    service_found = service
                    break

            if not service_found:
                raise ValidationError(f"Service {service_id} not found in booking")

            removed_services.append({
                "id": service_found.service_id,
                "name": service_found.name,
                "price": service_found.price,
                "duration_minutes": service_found.duration_minutes,
            })

        # Step 4: Remove services from booking (validates minimum services)
        for service_id in request.service_ids:
            booking.remove_service(service_id)

        # Step 5: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 6: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 7: Publish domain event
        self._event_service.publish_booking_services_updated(
            updated_booking,
            request.removed_by,
            "services_removed"
        )

        # Step 8: Send notification
        try:
            self._notification_service.send_booking_modified(
                booking.customer_id,
                updated_booking,
                f"{len(removed_services)} service(s) removed from your booking"
            )
        except Exception:
            # Log but don't fail - notification is non-critical
            pass

        return RemoveServiceFromBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            removed_services=removed_services,
            new_total_price=updated_booking.total_price,
            new_estimated_duration=updated_booking.estimated_duration_minutes,
            total_services_count=len(updated_booking.services)
        )
