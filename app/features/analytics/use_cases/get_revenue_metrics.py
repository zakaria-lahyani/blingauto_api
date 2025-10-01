"""Get revenue metrics use case."""

from dataclasses import dataclass
from datetime import date

from app.features.analytics.domain.entities import RevenueMetrics
from app.features.analytics.ports.repositories import IRevenueAnalyticsRepository


@dataclass
class GetRevenueMetricsRequest:
    """Request for revenue metrics."""

    start_date: date
    end_date: date


class GetRevenueMetricsUseCase:
    """Use case for retrieving revenue metrics."""

    def __init__(self, repository: IRevenueAnalyticsRepository):
        self._repository = repository

    async def execute(self, request: GetRevenueMetricsRequest) -> RevenueMetrics:
        """Execute the use case."""
        return await self._repository.get_revenue_metrics(
            request.start_date, request.end_date
        )
