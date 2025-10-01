from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from app.features.bookings.domain import Booking, BookingService, BookingType
from app.features.bookings.domain.policies import BookingValidationPolicy, BookingSchedulingPolicy
from app.features.bookings.ports import (
    IBookingRepository,
    IServiceRepository,
    IVehicleRepository,
    ICustomerRepository,
    INotificationService,
    IEventService,
    ICacheService,
    ILockService,
)


@dataclass
class UpdateBookingRequest:
    booking_id: str
    updated_by: str  # customer_id or admin_id
    is_admin: bool = False
    # Optional fields to update
    scheduled_at: Optional[datetime] = None
    service_ids: Optional[List[str]] = None
    notes: Optional[str] = None
    phone_number: Optional[str] = None


@dataclass
class UpdateBookingResponse:
    booking_id: str
    status: str
    total_price: float
    estimated_duration: int
    scheduled_at: datetime
    services: List[Dict[str, Any]]
    changes_made: List[str]


class UpdateBookingUseCase:
    """Use case for updating an existing booking."""
    
    def __init__(
        self,
        booking_repository: IBookingRepository,
        service_repository: IServiceRepository,
        vehicle_repository: IVehicleRepository,
        customer_repository: ICustomerRepository,
        notification_service: INotificationService,
        event_service: IEventService,
        cache_service: ICacheService,
        lock_service: ILockService,
    ):
        self._booking_repository = booking_repository
        self._service_repository = service_repository
        self._vehicle_repository = vehicle_repository
        self._customer_repository = customer_repository
        self._notification_service = notification_service
        self._event_service = event_service
        self._cache_service = cache_service
        self._lock_service = lock_service
    
    def execute(self, request: UpdateBookingRequest) -> UpdateBookingResponse:
        """Execute the update booking use case."""
        
        # Step 1: Retrieve existing booking
        booking = self._booking_repository.get_by_id(request.booking_id)
        if not booking:
            raise NotFoundError(f"Booking {request.booking_id} not found")
        
        # Step 2: Validate permissions
        if not request.is_admin and booking.customer_id != request.updated_by:
            raise BusinessRuleViolationError(
                "You can only update your own bookings"
            )
        
        # Step 3: Validate booking can be updated
        BookingValidationPolicy.validate_booking_update_allowed(booking)
        
        # Step 4: Acquire booking lock to prevent concurrent updates
        lock_id = self._lock_service.acquire_booking_lock(
            request.booking_id, timeout=30
        )
        
        if not lock_id:
            raise BusinessRuleViolationError(
                "Booking is being updated by another user. Please try again."
            )
        
        try:
            changes_made = []
            
            # Step 5: Update services if provided
            if request.service_ids is not None:
                services_data = self._service_repository.get_multiple_by_ids(
                    request.service_ids
                )
                if len(services_data) != len(request.service_ids):
                    raise ValidationError("One or more services not found")
                
                # Create new booking services
                new_services = []
                for service_data in services_data:
                    booking_service = BookingService(
                        service_id=service_data["id"],
                        name=service_data["name"],
                        price=service_data["price"],
                        duration_minutes=service_data["duration_minutes"],
                    )
                    new_services.append(booking_service)
                
                # Update services
                old_service_ids = [s.service_id for s in booking.services]
                new_service_ids = [s.service_id for s in new_services]
                
                if old_service_ids != new_service_ids:
                    booking.update_services(new_services)
                    changes_made.append("services")
            
            # Step 6: Update scheduled time if provided
            if request.scheduled_at is not None:
                # Check for conflicts with new time
                total_duration = booking.estimated_duration_minutes
                conflicting_bookings = self._booking_repository.find_conflicting_bookings(
                    request.scheduled_at,
                    total_duration,
                    booking.booking_type.value,
                    exclude_booking_id=booking.id,
                )
                
                if conflicting_bookings:
                    raise BusinessRuleViolationError(
                        f"New time slot conflicts with existing booking"
                    )
                
                BookingSchedulingPolicy.validate_scheduling_constraints(
                    booking, conflicting_bookings
                )
                
                if booking.scheduled_at != request.scheduled_at:
                    booking.reschedule(request.scheduled_at)
                    changes_made.append("scheduled_at")
            
            # Step 7: Update notes if provided
            if request.notes is not None and booking.notes != request.notes:
                booking.update_notes(request.notes)
                changes_made.append("notes")
            
            # Step 8: Update phone number if provided
            if request.phone_number is not None and booking.phone_number != request.phone_number:
                booking.update_phone_number(request.phone_number)
                changes_made.append("phone_number")
            
            # Step 9: Save updated booking if any changes were made
            if changes_made:
                updated_booking = self._booking_repository.update(booking)
                
                # Step 10: Invalidate cache
                self._cache_service.delete_booking(booking.id)
                self._cache_service.invalidate_customer_cache(booking.customer_id)
                
                # Step 11: Publish domain event
                changes_dict = {change: True for change in changes_made}
                self._event_service.publish_booking_updated(
                    updated_booking, changes_dict
                )
                
                # Step 12: Send update notification
                customer_data = self._customer_repository.get_by_id(booking.customer_id)
                if customer_data:
                    self._notification_service.send_booking_updated(
                        customer_data["email"],
                        updated_booking,
                        customer_data,
                        changes_dict,
                    )
            else:
                updated_booking = booking
                changes_made = ["no_changes"]
            
            # Step 13: Prepare response
            return UpdateBookingResponse(
                booking_id=updated_booking.id,
                status=updated_booking.status.value,
                total_price=updated_booking.total_price,
                estimated_duration=updated_booking.estimated_duration_minutes,
                scheduled_at=updated_booking.scheduled_at,
                services=[
                    {
                        "id": service.service_id,
                        "name": service.name,
                        "price": service.price,
                        "duration_minutes": service.duration_minutes,
                    }
                    for service in updated_booking.services
                ],
                changes_made=changes_made,
            )
        
        finally:
            # Always release the lock
            if lock_id:
                self._lock_service.release_lock(lock_id)