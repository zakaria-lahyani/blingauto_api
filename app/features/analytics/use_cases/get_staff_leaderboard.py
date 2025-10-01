"""Get staff leaderboard use case."""

from dataclasses import dataclass
from datetime import date

from app.features.analytics.domain.entities import StaffLeaderboard
from app.features.analytics.ports.repositories import IStaffAnalyticsRepository


@dataclass
class GetStaffLeaderboardRequest:
    """Request for staff leaderboard."""

    start_date: date
    end_date: date
    limit: int = 10


class GetStaffLeaderboardUseCase:
    """Use case for retrieving staff leaderboard."""

    def __init__(self, repository: IStaffAnalyticsRepository):
        self._repository = repository

    async def execute(
        self, request: GetStaffLeaderboardRequest
    ) -> StaffLeaderboard:
        """Execute the use case."""
        return await self._repository.get_staff_leaderboard(
            request.start_date, request.end_date, request.limit
        )
