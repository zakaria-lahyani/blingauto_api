"""Get budget use case."""

from app.features.expenses.domain.entities import Budget
from app.features.expenses.ports.repositories import IBudgetRepository


class GetBudgetUseCase:
    """Use case for getting a single budget."""

    def __init__(self, repository: IBudgetRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, budget_id: str) -> Budget:
        """Get budget by ID."""
        budget = await self._repository.get_by_id(budget_id)
        if not budget:
            raise LookupError(f"Budget {budget_id} not found")
        return budget
