"""Reject expense use case."""

from dataclasses import dataclass

from app.features.expenses.domain.entities import Expense
from app.features.expenses.ports.repositories import IExpenseRepository


@dataclass
class RejectExpenseRequest:
    """Request to reject expense."""

    expense_id: str
    rejected_by_id: str
    rejection_reason: str


class RejectExpenseUseCase:
    """Use case for rejecting an expense."""

    def __init__(self, repository: IExpenseRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: RejectExpenseRequest) -> Expense:
        """Reject expense."""
        expense = await self._repository.get_by_id(request.expense_id)
        if not expense:
            raise LookupError(f"Expense {request.expense_id} not found")

        expense.reject(request.rejected_by_id, request.rejection_reason)
        return await self._repository.update(expense)
