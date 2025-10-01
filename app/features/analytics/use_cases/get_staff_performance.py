"""Get staff performance use case."""

from dataclasses import dataclass
from datetime import date

from app.features.analytics.domain.entities import StaffPerformanceMetrics
from app.features.analytics.ports.repositories import IStaffAnalyticsRepository


@dataclass
class GetStaffPerformanceRequest:
    """Request for staff performance metrics."""

    staff_id: str
    start_date: date
    end_date: date


class GetStaffPerformanceUseCase:
    """Use case for retrieving staff performance metrics."""

    def __init__(self, repository: IStaffAnalyticsRepository):
        self._repository = repository

    async def execute(
        self, request: GetStaffPerformanceRequest
    ) -> StaffPerformanceMetrics:
        """Execute the use case."""
        return await self._repository.get_staff_performance(
            request.staff_id, request.start_date, request.end_date
        )
