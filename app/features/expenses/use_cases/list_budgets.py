"""List budgets use case."""

from datetime import date
from typing import List

from app.features.expenses.domain.entities import Budget
from app.features.expenses.ports.repositories import IBudgetRepository


class ListBudgetsUseCase:
    """Use case for listing budgets by month."""

    def __init__(self, repository: IBudgetRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, month: date) -> List[Budget]:
        """List all budgets for a month."""
        return await self._repository.list_by_month(month)
