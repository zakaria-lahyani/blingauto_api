from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

from app.core.errors import ValidationError, BusinessRuleViolationError, NotFoundError
from app.features.bookings.domain import Booking, BookingService, BookingType, BookingStatus
from app.features.bookings.domain.policies import BookingValidationPolicy, BookingSchedulingPolicy
from app.features.bookings.ports import (
    IBookingRepository,
    INotificationService,
    IEventService,
    ILockService,
)
from app.features.bookings.ports.external_services import (
    IExternalServiceValidator,
    IExternalVehicleValidator,
)


@dataclass
class CreateBookingRequest:
    customer_id: str
    vehicle_id: str
    service_ids: List[str]
    scheduled_at: datetime
    booking_type: str
    notes: str = ""
    phone_number: str = ""


@dataclass
class CreateBookingResponse:
    booking_id: str
    status: str
    total_price: float
    estimated_duration: int
    scheduled_at: datetime
    services: List[Dict[str, Any]]


class CreateBookingUseCase:
    """Use case for creating a new booking."""
    
    def __init__(
        self,
        booking_repository: IBookingRepository,
        notification_service: INotificationService,
        event_service: IEventService,
        lock_service: ILockService,
        service_validator: IExternalServiceValidator,
        vehicle_validator: IExternalVehicleValidator,
    ):
        self._booking_repository = booking_repository
        self._notification_service = notification_service
        self._event_service = event_service
        self._lock_service = lock_service
        self._service_validator = service_validator
        self._vehicle_validator = vehicle_validator
    
    def execute(self, request: CreateBookingRequest) -> CreateBookingResponse:
        """Execute the create booking use case."""
        
        # Step 1: Validate customer exists
        customer_exists = self._service_validator.validate_customer_exists(request.customer_id)
        if not customer_exists:
            raise NotFoundError(f"Customer {request.customer_id} not found")
        
        # Step 2: Validate vehicle belongs to customer
        vehicle_valid = self._vehicle_validator.validate_customer_vehicle(
            request.customer_id, request.vehicle_id
        )
        if not vehicle_valid:
            raise ValidationError("Vehicle does not belong to customer")
        
        # Step 3: Validate and retrieve services
        services_data = self._service_validator.get_services_data(request.service_ids)
        if len(services_data) != len(request.service_ids):
            raise ValidationError("One or more services not found")
        
        # Step 4: Create booking services with pricing
        booking_services = []
        total_price = 0.0
        total_duration = 0
        
        for service_data in services_data:
            booking_service = BookingService(
                service_id=service_data["id"],
                name=service_data["name"],
                price=service_data["price"],
                duration_minutes=service_data["duration_minutes"],
            )
            booking_services.append(booking_service)
            total_price += booking_service.price
            total_duration += booking_service.duration_minutes
        
        # Step 5: Validate booking type
        try:
            booking_type = BookingType(request.booking_type.upper())
        except ValueError:
            raise ValidationError(f"Invalid booking type: {request.booking_type}")
        
        # Step 6: Acquire time slot lock to prevent double booking
        lock_id = self._lock_service.acquire_time_slot_lock(
            request.scheduled_at,
            total_duration,
            request.booking_type,
            timeout=30,
        )
        
        if not lock_id:
            raise BusinessRuleViolationError(
                "Time slot is being booked by another customer. Please try again."
            )
        
        try:
            # Step 7: Check for scheduling conflicts
            conflicting_bookings = self._booking_repository.find_conflicting_bookings(
                request.scheduled_at,
                total_duration,
                request.booking_type,
            )
            
            if conflicting_bookings:
                raise BusinessRuleViolationError(
                    f"Time slot conflicts with existing booking at {request.scheduled_at}"
                )
            
            # Step 8: Create booking entity
            booking = Booking.create(
                customer_id=request.customer_id,
                vehicle_id=request.vehicle_id,
                services=booking_services,
                scheduled_at=request.scheduled_at,
                booking_type=booking_type,
                notes=request.notes,
                phone_number=request.phone_number,
            )
            
            # Step 9: Validate booking with business policies
            BookingSchedulingPolicy.validate_booking_creation(booking)
            BookingSchedulingPolicy.validate_scheduling_constraints(
                booking, conflicting_bookings
            )
            
            # Step 10: Save booking to repository
            saved_booking = self._booking_repository.create(booking)
            
            # Step 11: Publish domain event
            self._event_service.publish_booking_created(saved_booking)
            
            # Step 12: Send confirmation notification (async, don't block)
            customer_data = self._service_validator.get_customer_data(request.customer_id)
            vehicle_data = self._vehicle_validator.get_vehicle_data(request.vehicle_id)
            
            if customer_data and vehicle_data:
                self._notification_service.send_booking_confirmation(
                    customer_data["email"],
                    saved_booking,
                    customer_data,
                    services_data,
                    vehicle_data,
                )
            
            # Step 13: Prepare response
            return CreateBookingResponse(
                booking_id=saved_booking.id,
                status=saved_booking.status.value,
                total_price=saved_booking.total_price,
                estimated_duration=saved_booking.estimated_duration_minutes,
                scheduled_at=saved_booking.scheduled_at,
                services=[
                    {
                        "id": service.service_id,
                        "name": service.name,
                        "price": service.price,
                        "duration_minutes": service.duration_minutes,
                    }
                    for service in saved_booking.services
                ],
            )
        
        finally:
            # Always release the lock
            if lock_id:
                self._lock_service.release_lock(lock_id)