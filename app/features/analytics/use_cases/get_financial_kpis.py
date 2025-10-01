"""Get financial KPIs use case."""

from dataclasses import dataclass
from datetime import date

from app.features.analytics.domain.entities import FinancialKPIs
from app.features.analytics.ports.repositories import IFinancialAnalyticsRepository


@dataclass
class GetFinancialKPIsRequest:
    """Request for financial KPIs."""

    start_date: date
    end_date: date


class GetFinancialKPIsUseCase:
    """Use case for retrieving financial KPIs."""

    def __init__(self, repository: IFinancialAnalyticsRepository):
        self._repository = repository

    async def execute(self, request: GetFinancialKPIsRequest) -> FinancialKPIs:
        """Execute the use case."""
        return await self._repository.get_financial_kpis(
            request.start_date, request.end_date
        )
