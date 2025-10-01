"""Get expense use case."""

from app.features.expenses.domain.entities import Expense
from app.features.expenses.ports.repositories import IExpenseRepository


class GetExpenseUseCase:
    """Use case for getting a single expense."""

    def __init__(self, repository: IExpenseRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, expense_id: str) -> Expense:
        """Get expense by ID."""
        expense = await self._repository.get_by_id(expense_id)
        if not expense:
            raise LookupError(f"Expense {expense_id} not found")
        return expense
