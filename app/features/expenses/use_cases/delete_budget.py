"""Delete budget use case."""

from app.features.expenses.ports.repositories import IBudgetRepository


class DeleteBudgetUseCase:
    """Use case for deleting a budget."""

    def __init__(self, repository: IBudgetRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, budget_id: str) -> None:
        """Delete budget."""
        budget = await self._repository.get_by_id(budget_id)
        if not budget:
            raise LookupError(f"Budget {budget_id} not found")

        await self._repository.delete(budget_id)
