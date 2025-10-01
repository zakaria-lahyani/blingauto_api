"""Create expense use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from app.features.expenses.domain.entities import Expense
from app.features.expenses.domain.enums import ExpenseCategory, ExpenseStatus, RecurrenceType
from app.features.expenses.domain.policies import ExpenseManagementPolicy
from app.features.expenses.ports.repositories import IExpenseRepository, IBudgetRepository


@dataclass
class CreateExpenseRequest:
    """Request to create expense."""

    category: ExpenseCategory
    amount: Decimal
    description: str
    expense_date: date
    created_by_id: str
    due_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_id: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None
    recurrence_type: RecurrenceType = RecurrenceType.ONE_TIME


class CreateExpenseUseCase:
    """Use case for creating a new expense."""

    def __init__(self, expense_repo: IExpenseRepository, budget_repo: IBudgetRepository):
        """Initialize use case with repositories."""
        self._expense_repo = expense_repo
        self._budget_repo = budget_repo

    async def execute(self, request: CreateExpenseRequest) -> Expense:
        """Create expense."""
        # Validate
        self._validate_request(request)
        ExpenseManagementPolicy.validate_amount(request.amount)

        if request.due_date:
            ExpenseManagementPolicy.validate_due_date(request.expense_date, request.due_date)

        # Generate expense number
        daily_count = await self._expense_repo.get_daily_count(request.expense_date)
        expense_number = ExpenseManagementPolicy.generate_expense_number(
            request.expense_date, daily_count
        )

        # Determine initial status
        if ExpenseManagementPolicy.requires_approval(request.amount):
            status = ExpenseStatus.PENDING
        else:
            status = ExpenseStatus.APPROVED  # Auto-approve small expenses

        # Create expense
        expense = Expense(
            id=str(uuid.uuid4()),
            expense_number=expense_number,
            category=request.category,
            amount=request.amount,
            description=request.description,
            status=status,
            expense_date=request.expense_date,
            due_date=request.due_date,
            created_by_id=request.created_by_id,
            vendor_name=request.vendor_name,
            vendor_id=request.vendor_id,
            receipt_url=request.receipt_url,
            notes=request.notes,
            recurrence_type=request.recurrence_type,
        )

        created = await self._expense_repo.create(expense)

        # Update budget spent amount if approved
        if status == ExpenseStatus.APPROVED:
            await self._update_budget(created)

        return created

    async def _update_budget(self, expense: Expense) -> None:
        """Update budget spent amount."""
        month = expense.expense_date.replace(day=1)
        budget = await self._budget_repo.get_by_category_and_month(expense.category, month)

        if budget:
            budget.add_expense(expense.amount)
            await self._budget_repo.update(budget)

    def _validate_request(self, request: CreateExpenseRequest) -> None:
        """Validate request."""
        if not request.description or not request.description.strip():
            raise ValueError("Expense description is required")
