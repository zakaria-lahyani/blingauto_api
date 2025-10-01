"""Get customer behavior use case."""

from dataclasses import dataclass
from typing import Optional

from app.features.analytics.domain.entities import CustomerBehavior
from app.features.analytics.ports.repositories import ICustomerAnalyticsRepository


@dataclass
class GetCustomerBehaviorRequest:
    """Request for customer behavior analysis."""

    customer_id: str


class GetCustomerBehaviorUseCase:
    """Use case for retrieving customer behavior analysis."""

    def __init__(self, repository: ICustomerAnalyticsRepository):
        self._repository = repository

    async def execute(
        self, request: GetCustomerBehaviorRequest
    ) -> Optional[CustomerBehavior]:
        """Execute the use case."""
        return await self._repository.get_customer_behavior(request.customer_id)
