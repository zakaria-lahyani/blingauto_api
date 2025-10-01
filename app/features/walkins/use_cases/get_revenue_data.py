"""Get walk-in revenue data for analytics - Public use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from app.features.walkins.ports.repositories import IWalkInRepository


@dataclass
class WalkInRevenueData:
    """Revenue data for a walk-in service."""

    walkin_id: str
    service_date: date
    final_amount: Decimal
    status: str


@dataclass
class GetWalkInRevenueDataRequest:
    """Request for walk-in revenue data."""

    start_date: date
    end_date: date


class GetWalkInRevenueDataUseCase:
    """Public use case for analytics to get walk-in revenue data."""

    def __init__(self, walkin_repository: IWalkInRepository):
        self._repository = walkin_repository

    async def execute(
        self, request: GetWalkInRevenueDataRequest
    ) -> List[WalkInRevenueData]:
        """Get revenue data for walk-ins in period."""
        walkins = await self._repository.list_all()

        # Filter by date range and status
        revenue_data = []
        for walkin in walkins:
            service_date = walkin.created_at.date()
            if (
                service_date >= request.start_date
                and service_date <= request.end_date
                and walkin.status in ["in_progress", "completed"]
            ):
                revenue_data.append(
                    WalkInRevenueData(
                        walkin_id=walkin.id,
                        service_date=service_date,
                        final_amount=walkin.final_amount,
                        status=walkin.status,
                    )
                )

        return revenue_data
