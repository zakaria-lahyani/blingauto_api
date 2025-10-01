from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.bookings.domain import Booking
from app.features.bookings.ports import (
    IBookingRepository,
    IServiceRepository,
    IVehicleRepository,
    ICustomerRepository,
    ICacheService,
)


@dataclass
class GetBookingRequest:
    booking_id: str
    requested_by: str  # customer_id or admin_id
    is_admin: bool = False


@dataclass
class BookingServiceDetail:
    service_id: str
    name: str
    price: float
    duration_minutes: int


@dataclass
class GetBookingResponse:
    id: str
    customer_id: str
    vehicle_id: str
    status: str
    scheduled_at: datetime
    booking_type: str
    services: List[BookingServiceDetail]
    total_price: float
    estimated_duration: int
    notes: str
    phone_number: str
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime = None
    cancelled_by: str = None
    cancellation_reason: str = None
    # Additional details
    customer_details: Dict[str, Any] = None
    vehicle_details: Dict[str, Any] = None


class GetBookingUseCase:
    """Use case for retrieving a specific booking with full details."""
    
    def __init__(
        self,
        booking_repository: IBookingRepository,
        service_repository: IServiceRepository,
        vehicle_repository: IVehicleRepository,
        customer_repository: ICustomerRepository,
        cache_service: ICacheService,
    ):
        self._booking_repository = booking_repository
        self._service_repository = service_repository
        self._vehicle_repository = vehicle_repository
        self._customer_repository = customer_repository
        self._cache_service = cache_service
    
    def execute(self, request: GetBookingRequest) -> GetBookingResponse:
        """Execute the get booking use case."""
        
        # Step 1: Try to get from cache first
        booking = self._cache_service.get_booking(request.booking_id)
        
        if not booking:
            # Step 2: Get from repository if not cached
            booking = self._booking_repository.get_by_id(request.booking_id)
            if not booking:
                raise NotFoundError(f"Booking {request.booking_id} not found")
            
            # Cache the booking for future requests
            self._cache_service.set_booking(booking, ttl=3600)
        
        # Step 3: Validate access permissions
        if not request.is_admin and booking.customer_id != request.requested_by:
            raise BusinessRuleViolationError(
                "You can only view your own bookings"
            )
        
        # Step 4: Get additional details for comprehensive response
        customer_details = None
        vehicle_details = None
        
        # Always get customer details for the response
        customer_details = self._customer_repository.get_by_id(booking.customer_id)
        
        # Get vehicle details
        vehicle_details = self._vehicle_repository.get_by_id(booking.vehicle_id)
        
        # Step 5: Convert services to detailed format
        service_details = [
            BookingServiceDetail(
                service_id=service.service_id,
                name=service.name,
                price=service.price,
                duration_minutes=service.duration_minutes,
            )
            for service in booking.services
        ]
        
        # Step 6: Build comprehensive response
        response = GetBookingResponse(
            id=booking.id,
            customer_id=booking.customer_id,
            vehicle_id=booking.vehicle_id,
            status=booking.status.value,
            scheduled_at=booking.scheduled_at,
            booking_type=booking.booking_type.value,
            services=service_details,
            total_price=booking.total_price,
            estimated_duration=booking.estimated_duration_minutes,
            notes=booking.notes,
            phone_number=booking.phone_number,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            customer_details=customer_details,
            vehicle_details=vehicle_details,
        )
        
        # Add cancellation details if booking is cancelled
        if booking.cancelled_at:
            response.cancelled_at = booking.cancelled_at
            response.cancelled_by = booking.cancelled_by
            response.cancellation_reason = booking.cancellation_reason
        
        return response