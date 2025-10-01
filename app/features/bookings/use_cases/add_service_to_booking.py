"""
Add Service to Booking Use Case
Implements RG-BOK-013: Add services to pending bookings only
"""

from dataclasses import dataclass
from typing import List, Dict, Any

from app.core.errors import NotFoundError, BusinessRuleViolationError, ValidationError
from app.features.bookings.domain import Booking, BookingStatus, BookingService
from app.features.bookings.ports import (
    IBookingRepository,
    INotificationService,
    IEventService,
    ICacheService,
)
from app.features.bookings.ports.external_services import IExternalServiceValidator


@dataclass
class AddServiceToBookingRequest:
    """Request to add services to a booking."""
    booking_id: str
    service_ids: List[str]  # List of service IDs to add
    added_by: str  # customer_id or staff_id


@dataclass
class AddServiceToBookingResponse:
    """Response after adding services to a booking."""
    booking_id: str
    status: str
    added_services: List[Dict[str, Any]]
    new_total_price: float
    new_estimated_duration: int
    total_services_count: int


class AddServiceToBookingUseCase:
    """
    Use case for adding services to an existing booking.

    Business Rules:
    - RG-BOK-013: Only PENDING bookings can have services added
    - RG-BOK-001: Maximum 10 services per booking
    - Recalculates total price and duration
    """

    def __init__(
        self,
        booking_repository: IBookingRepository,
        notification_service: INotificationService,
        event_service: IEventService,
        cache_service: ICacheService,
        service_validator: IExternalServiceValidator,
    ):
        self._booking_repository = booking_repository
        self._notification_service = notification_service
        self._event_service = event_service
        self._cache_service = cache_service
        self._service_validator = service_validator

    def execute(self, request: AddServiceToBookingRequest) -> AddServiceToBookingResponse:
        """Execute the add service to booking use case."""

        # Step 1: Retrieve booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")

        # Step 2: Validate booking state (only PENDING allowed)
        if booking.status != BookingStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Can only add services to pending bookings, current status: {booking.status.value}",
                rule="RG-BOK-013"
            )

        # Step 3: Validate and retrieve services data
        services_data = self._service_validator.get_services_data(request.service_ids)
        if len(services_data) != len(request.service_ids):
            raise ValidationError("One or more services not found")

        # Step 4: Create booking services
        new_services = []
        for service_data in services_data:
            booking_service = BookingService(
                service_id=service_data["id"],
                name=service_data["name"],
                price=service_data["price"],
                duration_minutes=service_data["duration_minutes"],
            )
            new_services.append(booking_service)

        # Step 5: Add services to booking (validates max services)
        for service in new_services:
            booking.add_service(service)

        # Step 6: Save the updated booking
        updated_booking = self._booking_repository.update(booking)

        # Step 7: Invalidate cache
        self._cache_service.delete_booking(booking.id)
        self._cache_service.invalidate_customer_cache(booking.customer_id)

        # Step 8: Publish domain event
        self._event_service.publish_booking_services_updated(
            updated_booking,
            request.added_by,
            "services_added"
        )

        # Step 9: Send notification
        try:
            self._notification_service.send_booking_modified(
                booking.customer_id,
                updated_booking,
                f"{len(new_services)} service(s) added to your booking"
            )
        except Exception:
            # Log but don't fail - notification is non-critical
            pass

        return AddServiceToBookingResponse(
            booking_id=updated_booking.id,
            status=updated_booking.status.value,
            added_services=[
                {
                    "id": service.service_id,
                    "name": service.name,
                    "price": service.price,
                    "duration_minutes": service.duration_minutes,
                }
                for service in new_services
            ],
            new_total_price=updated_booking.total_price,
            new_estimated_duration=updated_booking.estimated_duration_minutes,
            total_services_count=len(updated_booking.services)
        )
