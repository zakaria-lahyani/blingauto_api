"""Get monthly expense summary use case."""

from datetime import date
from typing import List

from app.features.expenses.domain.entities import ExpenseSummary
from app.features.expenses.ports.repositories import IExpenseRepository


class GetMonthlySummaryUseCase:
    """Use case for getting monthly expense summary."""

    def __init__(self, repository: IExpenseRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, month: date) -> List[ExpenseSummary]:
        """Get monthly summary by category."""
        return await self._repository.get_monthly_summary(month)
