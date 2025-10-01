"""Approve expense use case."""

from dataclasses import dataclass
from typing import Optional

from app.features.expenses.domain.entities import Expense
from app.features.expenses.ports.repositories import IExpenseRepository, IBudgetRepository


@dataclass
class ApproveExpenseRequest:
    """Request to approve expense."""

    expense_id: str
    approved_by_id: str
    approval_notes: Optional[str] = None


class ApproveExpenseUseCase:
    """Use case for approving an expense."""

    def __init__(self, expense_repo: IExpenseRepository, budget_repo: IBudgetRepository):
        """Initialize use case with repositories."""
        self._expense_repo = expense_repo
        self._budget_repo = budget_repo

    async def execute(self, request: ApproveExpenseRequest) -> Expense:
        """Approve expense."""
        expense = await self._expense_repo.get_by_id(request.expense_id)
        if not expense:
            raise LookupError(f"Expense {request.expense_id} not found")

        expense.approve(request.approved_by_id, request.approval_notes)

        updated = await self._expense_repo.update(expense)

        # Update budget
        month = expense.expense_date.replace(day=1)
        budget = await self._budget_repo.get_by_category_and_month(expense.category, month)
        if budget:
            budget.add_expense(expense.amount)
            await self._budget_repo.update(budget)

        return updated
