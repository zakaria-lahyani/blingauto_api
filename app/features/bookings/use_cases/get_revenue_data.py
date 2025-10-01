"""Get revenue data for analytics - Public use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from app.features.bookings.ports.repositories import IBookingRepository


@dataclass
class BookingRevenueData:
    """Revenue data for a booking."""

    booking_id: str
    booking_date: date
    total_amount: Decimal
    status: str
    customer_id: str
    service_id: str


@dataclass
class GetRevenueDataRequest:
    """Request for revenue data."""

    start_date: date
    end_date: date


class GetRevenueDataUseCase:
    """Public use case for analytics to get booking revenue data."""

    def __init__(self, booking_repository: IBookingRepository):
        self._repository = booking_repository

    async def execute(
        self, request: GetRevenueDataRequest
    ) -> List[BookingRevenueData]:
        """Get revenue data for confirmed/completed bookings in period."""
        bookings = await self._repository.list_all()

        # Filter by date range and status
        revenue_data = []
        for booking in bookings:
            if (
                booking.booking_date >= request.start_date
                and booking.booking_date <= request.end_date
                and booking.status in ["confirmed", "completed"]
            ):
                revenue_data.append(
                    BookingRevenueData(
                        booking_id=booking.id,
                        booking_date=booking.booking_date,
                        total_amount=booking.total_amount,
                        status=booking.status,
                        customer_id=booking.customer_id,
                        service_id=booking.service_id,
                    )
                )

        return revenue_data
