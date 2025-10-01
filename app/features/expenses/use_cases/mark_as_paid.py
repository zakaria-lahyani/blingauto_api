"""Mark expense as paid use case."""

from dataclasses import dataclass
from datetime import date

from app.features.expenses.domain.entities import Expense
from app.features.expenses.domain.enums import PaymentMethod
from app.features.expenses.ports.repositories import IExpenseRepository


@dataclass
class MarkAsPaidRequest:
    """Request to mark expense as paid."""

    expense_id: str
    paid_by_id: str
    payment_method: PaymentMethod
    paid_date: date


class MarkAsPaidUseCase:
    """Use case for marking expense as paid."""

    def __init__(self, repository: IExpenseRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: MarkAsPaidRequest) -> Expense:
        """Mark expense as paid."""
        expense = await self._repository.get_by_id(request.expense_id)
        if not expense:
            raise LookupError(f"Expense {request.expense_id} not found")

        expense.mark_as_paid(request.paid_by_id, request.payment_method, request.paid_date)
        return await self._repository.update(expense)
