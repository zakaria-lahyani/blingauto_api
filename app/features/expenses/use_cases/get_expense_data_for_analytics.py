"""Get expense data for analytics - Public use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from app.features.expenses.ports.repositories import (
    IExpenseRepository,
    IBudgetRepository,
)


@dataclass
class ExpenseData:
    """Expense data for analytics."""

    expense_id: str
    category: str
    amount: Decimal
    status: str
    expense_date: date


@dataclass
class BudgetData:
    """Budget data for analytics."""

    category: str
    month: date
    budgeted_amount: Decimal
    spent_amount: Decimal


@dataclass
class GetExpenseDataRequest:
    """Request for expense data."""

    start_date: date
    end_date: date


@dataclass
class GetBudgetDataRequest:
    """Request for budget data."""

    start_date: date
    end_date: date


class GetExpenseDataUseCase:
    """Public use case for analytics to get expense data."""

    def __init__(self, expense_repository: IExpenseRepository):
        self._repository = expense_repository

    async def execute(self, request: GetExpenseDataRequest) -> List[ExpenseData]:
        """Get expense data for approved/paid expenses in period."""
        expenses = await self._repository.list_all()

        # Filter by date range and status
        expense_data = []
        for expense in expenses:
            if (
                expense.expense_date >= request.start_date
                and expense.expense_date <= request.end_date
                and expense.status in ["approved", "paid"]
            ):
                expense_data.append(
                    ExpenseData(
                        expense_id=expense.id,
                        category=expense.category.value,
                        amount=expense.amount,
                        status=expense.status.value,
                        expense_date=expense.expense_date,
                    )
                )

        return expense_data


class GetBudgetDataUseCase:
    """Public use case for analytics to get budget data."""

    def __init__(self, budget_repository: IBudgetRepository):
        self._repository = budget_repository

    async def execute(self, request: GetBudgetDataRequest) -> List[BudgetData]:
        """Get budget data for period."""
        budgets = await self._repository.list_all()

        # Filter by date range
        budget_data = []
        for budget in budgets:
            if request.start_date <= budget.month <= request.end_date:
                budget_data.append(
                    BudgetData(
                        category=budget.category.value,
                        month=budget.month,
                        budgeted_amount=budget.budgeted_amount,
                        spent_amount=budget.spent_amount,
                    )
                )

        return budget_data
