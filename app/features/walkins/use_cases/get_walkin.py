"""Get walk-in service use case."""

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.ports.repositories import IWalkInRepository


class GetWalkInUseCase:
    """Use case for getting a single walk-in service."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, walkin_id: str) -> WalkInService:
        """
        Get walk-in service by ID.

        Args:
            walkin_id: Walk-in service ID

        Returns:
            Walk-in service

        Raises:
            LookupError: If walk-in not found
        """
        walkin = await self._repository.get_by_id(walkin_id)
        if not walkin:
            raise LookupError(f"Walk-in service {walkin_id} not found")

        return walkin
