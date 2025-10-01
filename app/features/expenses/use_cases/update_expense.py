"""Update expense use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from app.features.expenses.domain.entities import Expense
from app.features.expenses.domain.enums import ExpenseCategory
from app.features.expenses.ports.repositories import IExpenseRepository


@dataclass
class UpdateExpenseRequest:
    """Request to update expense."""

    expense_id: str
    category: Optional[ExpenseCategory] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    expense_date: Optional[date] = None
    due_date: Optional[date] = None
    vendor_name: Optional[str] = None
    notes: Optional[str] = None


class UpdateExpenseUseCase:
    """Use case for updating expense."""

    def __init__(self, repository: IExpenseRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: UpdateExpenseRequest) -> Expense:
        """Update expense."""
        expense = await self._repository.get_by_id(request.expense_id)
        if not expense:
            raise LookupError(f"Expense {request.expense_id} not found")

        # Only allow updates if pending
        if expense.status != ExpenseStatus.PENDING:
            raise ValueError("Can only update pending expenses")

        if request.category:
            expense.category = request.category
        if request.amount:
            expense.amount = request.amount
        if request.description:
            expense.description = request.description
        if request.expense_date:
            expense.expense_date = request.expense_date
        if request.due_date:
            expense.due_date = request.due_date
        if request.vendor_name:
            expense.vendor_name = request.vendor_name
        if request.notes:
            expense.notes = request.notes

        return await self._repository.update(expense)
