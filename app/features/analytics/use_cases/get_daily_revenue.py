"""Get daily revenue use case."""

from dataclasses import dataclass
from datetime import date
from typing import List

from app.features.analytics.domain.entities import DailyRevenue
from app.features.analytics.ports.repositories import IRevenueAnalyticsRepository


@dataclass
class GetDailyRevenueRequest:
    """Request for daily revenue."""

    start_date: date
    end_date: date


class GetDailyRevenueUseCase:
    """Use case for retrieving daily revenue breakdown."""

    def __init__(self, repository: IRevenueAnalyticsRepository):
        self._repository = repository

    async def execute(self, request: GetDailyRevenueRequest) -> List[DailyRevenue]:
        """Execute the use case."""
        return await self._repository.get_daily_revenue(
            request.start_date, request.end_date
        )
