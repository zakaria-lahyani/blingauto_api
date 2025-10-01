from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.core.errors import ValidationError
from app.features.bookings.domain import Booking
from app.features.bookings.ports import (
    IBookingRepository,
    ICacheService,
)


@dataclass
class ListBookingsRequest:
    customer_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    limit: int = 20


@dataclass
class BookingSummary:
    id: str
    customer_id: str
    vehicle_id: str
    status: str
    scheduled_at: datetime
    total_price: float
    estimated_duration: int
    services_count: int
    booking_type: str
    created_at: datetime


@dataclass
class ListBookingsResponse:
    bookings: List[BookingSummary]
    total_count: int
    page: int
    limit: int
    has_next: bool


class ListBookingsUseCase:
    """Use case for listing bookings with filtering and pagination."""
    
    def __init__(
        self,
        booking_repository: IBookingRepository,
        cache_service: ICacheService,
    ):
        self._booking_repository = booking_repository
        self._cache_service = cache_service
    
    def execute(self, request: ListBookingsRequest) -> ListBookingsResponse:
        """Execute the list bookings use case."""
        
        # Step 1: Validate pagination parameters
        if request.page < 1:
            raise ValidationError("Page must be greater than 0")
        if request.limit < 1 or request.limit > 100:
            raise ValidationError("Limit must be between 1 and 100")
        
        # Step 2: Calculate offset
        offset = (request.page - 1) * request.limit
        
        # Step 3: Try to get from cache for customer-specific requests
        cached_data = None
        if request.customer_id and not request.status and not request.start_date:
            cached_data = self._cache_service.get_customer_bookings(
                request.customer_id, request.page, request.limit
            )
        
        if cached_data:
            return ListBookingsResponse(
                bookings=[
                    BookingSummary(**booking_data) for booking_data in cached_data["bookings"]
                ],
                total_count=cached_data["total_count"],
                page=request.page,
                limit=request.limit,
                has_next=cached_data["has_next"],
            )
        
        # Step 4: Query repository based on filters
        bookings = []
        
        if request.customer_id:
            bookings = self._booking_repository.list_by_customer(
                customer_id=request.customer_id,
                offset=offset,
                limit=request.limit,
                status=request.status,
            )
        elif request.start_date and request.end_date:
            bookings = self._booking_repository.list_by_date_range(
                start_date=request.start_date,
                end_date=request.end_date,
                offset=offset,
                limit=request.limit,
                status=request.status,
            )
        elif request.status:
            bookings = self._booking_repository.list_by_status(
                status=request.status,
                offset=offset,
                limit=request.limit,
            )
        else:
            # Default: get recent bookings
            bookings = self._booking_repository.list_by_date_range(
                start_date=datetime.now().replace(day=1),  # Start of current month
                end_date=datetime.now(),
                offset=offset,
                limit=request.limit,
                status=request.status,
            )
        
        # Step 5: Convert to summary format
        booking_summaries = [
            BookingSummary(
                id=booking.id,
                customer_id=booking.customer_id,
                vehicle_id=booking.vehicle_id,
                status=booking.status.value,
                scheduled_at=booking.scheduled_at,
                total_price=booking.total_price,
                estimated_duration=booking.estimated_duration_minutes,
                services_count=len(booking.services),
                booking_type=booking.booking_type.value,
                created_at=booking.created_at,
            )
            for booking in bookings
        ]
        
        # Step 6: Get total count for pagination
        total_count = 0
        if request.customer_id:
            total_count = self._booking_repository.count_by_customer(
                request.customer_id, request.status
            )
        else:
            # For other queries, estimate based on current page results
            total_count = len(booking_summaries) + offset
            if len(booking_summaries) == request.limit:
                total_count += 1  # Indicate there might be more
        
        has_next = len(booking_summaries) == request.limit
        
        # Step 7: Cache customer-specific results
        if request.customer_id and not request.status and not request.start_date:
            cache_data = {
                "bookings": [
                    {
                        "id": summary.id,
                        "customer_id": summary.customer_id,
                        "vehicle_id": summary.vehicle_id,
                        "status": summary.status,
                        "scheduled_at": summary.scheduled_at.isoformat(),
                        "total_price": summary.total_price,
                        "estimated_duration": summary.estimated_duration,
                        "services_count": summary.services_count,
                        "booking_type": summary.booking_type,
                        "created_at": summary.created_at.isoformat(),
                    }
                    for summary in booking_summaries
                ],
                "total_count": total_count,
                "has_next": has_next,
            }
            self._cache_service.set_customer_bookings(
                request.customer_id, cache_data, request.page, request.limit
            )
        
        return ListBookingsResponse(
            bookings=booking_summaries,
            total_count=total_count,
            page=request.page,
            limit=request.limit,
            has_next=has_next,
        )