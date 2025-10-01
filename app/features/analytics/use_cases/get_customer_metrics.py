"""Get customer metrics use case."""

from dataclasses import dataclass
from datetime import date

from app.features.analytics.domain.entities import CustomerMetrics
from app.features.analytics.ports.repositories import ICustomerAnalyticsRepository


@dataclass
class GetCustomerMetricsRequest:
    """Request for customer metrics."""

    start_date: date
    end_date: date


class GetCustomerMetricsUseCase:
    """Use case for retrieving customer metrics."""

    def __init__(self, repository: ICustomerAnalyticsRepository):
        self._repository = repository

    async def execute(self, request: GetCustomerMetricsRequest) -> CustomerMetrics:
        """Execute the use case."""
        return await self._repository.get_customer_metrics(
            request.start_date, request.end_date
        )
