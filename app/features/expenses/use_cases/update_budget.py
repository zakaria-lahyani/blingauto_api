"""Update budget use case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.features.expenses.domain.entities import Budget
from app.features.expenses.domain.policies import BudgetManagementPolicy
from app.features.expenses.ports.repositories import IBudgetRepository


@dataclass
class UpdateBudgetRequest:
    """Request to update budget."""

    budget_id: str
    budgeted_amount: Optional[Decimal] = None
    alert_threshold_percent: Optional[Decimal] = None
    notes: Optional[str] = None


class UpdateBudgetUseCase:
    """Use case for updating budget."""

    def __init__(self, repository: IBudgetRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: UpdateBudgetRequest) -> Budget:
        """Update budget."""
        budget = await self._repository.get_by_id(request.budget_id)
        if not budget:
            raise LookupError(f"Budget {request.budget_id} not found")

        if request.budgeted_amount:
            BudgetManagementPolicy.validate_budget_amount(request.budgeted_amount)
            budget.budgeted_amount = request.budgeted_amount

        if request.alert_threshold_percent:
            BudgetManagementPolicy.validate_alert_threshold(request.alert_threshold_percent)
            budget.alert_threshold_percent = request.alert_threshold_percent

        if request.notes:
            budget.notes = request.notes

        return await self._repository.update(budget)
