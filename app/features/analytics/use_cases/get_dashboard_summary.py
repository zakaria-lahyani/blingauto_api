"""Get dashboard summary use case."""

from dataclasses import dataclass
from datetime import date

from app.features.analytics.domain.entities import DashboardSummary
from app.features.analytics.ports.repositories import IDashboardRepository


@dataclass
class GetDashboardSummaryRequest:
    """Request for dashboard summary."""

    start_date: date
    end_date: date


class GetDashboardSummaryUseCase:
    """Use case for retrieving comprehensive dashboard summary."""

    def __init__(self, repository: IDashboardRepository):
        self._repository = repository

    async def execute(self, request: GetDashboardSummaryRequest) -> DashboardSummary:
        """Execute the use case."""
        return await self._repository.get_dashboard_summary(
            request.start_date, request.end_date
        )
