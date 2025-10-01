"""Remove service from walk-in use case."""

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus
from app.features.walkins.ports.repositories import IWalkInRepository


class RemoveServiceUseCase:
    """Use case for removing a service from walk-in."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, walkin_id: str, service_item_id: str) -> WalkInService:
        """
        Remove a service from walk-in.

        Args:
            walkin_id: Walk-in service ID
            service_item_id: Service item ID to remove

        Returns:
            Updated walk-in service

        Raises:
            ValueError: If validation fails
            LookupError: If walk-in or service item not found
        """
        # Get walk-in
        walkin = await self._repository.get_by_id(walkin_id)
        if not walkin:
            raise LookupError(f"Walk-in service {walkin_id} not found")

        # Validate walk-in state
        if walkin.status == WalkInStatus.COMPLETED:
            raise ValueError("Cannot remove services from completed walk-in")

        if walkin.status == WalkInStatus.CANCELLED:
            raise ValueError("Cannot remove services from cancelled walk-in")

        # Find service item
        service_item = next(
            (item for item in walkin.services if item.id == service_item_id), None
        )
        if not service_item:
            raise LookupError(
                f"Service item {service_item_id} not found in walk-in {walkin_id}"
            )

        # Remove service from walk-in
        walkin.remove_service(service_item_id)

        # Update in repository
        updated = await self._repository.update(walkin)

        return updated
