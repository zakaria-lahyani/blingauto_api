"""Get service statistics for analytics - Public use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from app.features.bookings.ports.repositories import IBookingRepository


@dataclass
class ServiceBookingStats:
    """Booking statistics for a service."""

    service_id: str
    service_name: str
    booking_count: int
    total_revenue: Decimal
    status: str  # aggregated status (e.g., "active")


@dataclass
class GetServiceStatsRequest:
    """Request for service statistics."""

    start_date: date
    end_date: date


class GetServiceStatsUseCase:
    """Public use case for analytics to get service booking statistics."""

    def __init__(self, booking_repository: IBookingRepository):
        self._repository = booking_repository

    async def execute(
        self, request: GetServiceStatsRequest
    ) -> List[ServiceBookingStats]:
        """Get booking statistics by service."""
        bookings = await self._repository.list_all()

        # Filter by date range
        period_bookings = [
            b
            for b in bookings
            if request.start_date <= b.booking_date <= request.end_date
        ]

        # Group by service
        service_map = {}
        for booking in period_bookings:
            sid = booking.service_id
            if sid not in service_map:
                service_map[sid] = {
                    "count": 0,
                    "revenue": Decimal("0"),
                }
            service_map[sid]["count"] += 1
            service_map[sid]["revenue"] += booking.total_amount

        # Create stats list
        stats_list = []
        for sid, data in service_map.items():
            stats_list.append(
                ServiceBookingStats(
                    service_id=sid,
                    service_name="",  # Will be populated by analytics
                    booking_count=data["count"],
                    total_revenue=data["revenue"],
                    status="active",
                )
            )

        return stats_list
