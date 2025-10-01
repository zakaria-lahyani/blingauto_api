"""Get customer statistics for analytics - Public use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from app.features.bookings.ports.repositories import IBookingRepository


@dataclass
class CustomerBookingStats:
    """Booking statistics for a customer."""

    customer_id: str
    booking_count: int
    total_spent: Decimal
    first_booking_date: date
    last_booking_date: date


@dataclass
class GetCustomerStatsRequest:
    """Request for customer statistics."""

    customer_id: str


@dataclass
class GetTopCustomersRequest:
    """Request for top customers."""

    start_date: date
    end_date: date
    limit: int


class GetCustomerStatsUseCase:
    """Public use case for analytics to get customer booking statistics."""

    def __init__(self, booking_repository: IBookingRepository):
        self._repository = booking_repository

    async def execute(
        self, request: GetCustomerStatsRequest
    ) -> Optional[CustomerBookingStats]:
        """Get booking statistics for a customer."""
        bookings = await self._repository.list_all()

        # Filter bookings for this customer
        customer_bookings = [
            b for b in bookings if b.customer_id == request.customer_id
        ]

        if not customer_bookings:
            return None

        # Calculate statistics
        total_spent = sum(b.total_amount for b in customer_bookings)
        first_date = min(b.booking_date for b in customer_bookings)
        last_date = max(b.booking_date for b in customer_bookings)

        return CustomerBookingStats(
            customer_id=request.customer_id,
            booking_count=len(customer_bookings),
            total_spent=total_spent,
            first_booking_date=first_date,
            last_booking_date=last_date,
        )


class GetTopCustomersUseCase:
    """Public use case for analytics to get top customers by spending."""

    def __init__(self, booking_repository: IBookingRepository):
        self._repository = booking_repository

    async def execute(
        self, request: GetTopCustomersRequest
    ) -> List[CustomerBookingStats]:
        """Get top customers by spending in period."""
        bookings = await self._repository.list_all()

        # Filter by date range
        period_bookings = [
            b
            for b in bookings
            if request.start_date <= b.booking_date <= request.end_date
        ]

        # Group by customer
        customer_map = {}
        for booking in period_bookings:
            cid = booking.customer_id
            if cid not in customer_map:
                customer_map[cid] = {
                    "bookings": [],
                    "total": Decimal("0"),
                }
            customer_map[cid]["bookings"].append(booking)
            customer_map[cid]["total"] += booking.total_amount

        # Create stats list
        stats_list = []
        for cid, data in customer_map.items():
            customer_bookings = data["bookings"]
            stats_list.append(
                CustomerBookingStats(
                    customer_id=cid,
                    booking_count=len(customer_bookings),
                    total_spent=data["total"],
                    first_booking_date=min(b.booking_date for b in customer_bookings),
                    last_booking_date=max(b.booking_date for b in customer_bookings),
                )
            )

        # Sort by total spent and limit
        stats_list.sort(key=lambda x: x.total_spent, reverse=True)
        return stats_list[: request.limit]
