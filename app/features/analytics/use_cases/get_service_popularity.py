"""Get service popularity use case."""

from dataclasses import dataclass
from datetime import date
from typing import List

from app.features.analytics.domain.entities import ServicePopularity
from app.features.analytics.ports.repositories import IServiceAnalyticsRepository


@dataclass
class GetServicePopularityRequest:
    """Request for service popularity metrics."""

    start_date: date
    end_date: date


class GetServicePopularityUseCase:
    """Use case for retrieving service popularity metrics."""

    def __init__(self, repository: IServiceAnalyticsRepository):
        self._repository = repository

    async def execute(
        self, request: GetServicePopularityRequest
    ) -> List[ServicePopularity]:
        """Execute the use case."""
        return await self._repository.get_service_popularity(
            request.start_date, request.end_date
        )
