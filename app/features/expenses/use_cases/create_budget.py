"""Create budget use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from app.features.expenses.domain.entities import Budget
from app.features.expenses.domain.enums import ExpenseCategory
from app.features.expenses.domain.policies import BudgetManagementPolicy
from app.features.expenses.ports.repositories import IBudgetRepository


@dataclass
class CreateBudgetRequest:
    """Request to create budget."""

    category: ExpenseCategory
    month: date  # First day of month
    budgeted_amount: Decimal
    created_by_id: str
    alert_threshold_percent: Decimal = Decimal("80.00")
    notes: Optional[str] = None


class CreateBudgetUseCase:
    """Use case for creating a budget."""

    def __init__(self, repository: IBudgetRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: CreateBudgetRequest) -> Budget:
        """Create budget."""
        # Validate
        BudgetManagementPolicy.validate_budget_amount(request.budgeted_amount)
        BudgetManagementPolicy.validate_alert_threshold(request.alert_threshold_percent)

        # Check if budget already exists for this category/month
        existing = await self._repository.get_by_category_and_month(
            request.category, request.month
        )
        if existing:
            raise ValueError(f"Budget already exists for {request.category} in {request.month}")

        budget = Budget(
            id=str(uuid.uuid4()),
            category=request.category,
            month=request.month,
            budgeted_amount=request.budgeted_amount,
            alert_threshold_percent=request.alert_threshold_percent,
            created_by_id=request.created_by_id,
            notes=request.notes,
        )

        return await self._repository.create(budget)
