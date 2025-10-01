"""Complete walk-in service use case."""

from datetime import datetime

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus, PaymentStatus
from app.features.walkins.ports.repositories import IWalkInRepository


class CompleteWalkInUseCase:
    """Use case for completing walk-in service."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, walkin_id: str, completed_by_id: str) -> WalkInService:
        """
        Complete walk-in service.

        Args:
            walkin_id: Walk-in service ID
            completed_by_id: Staff ID who completed the service

        Returns:
            Updated walk-in service

        Raises:
            ValueError: If validation fails
            LookupError: If walk-in not found
        """
        # Get walk-in
        walkin = await self._repository.get_by_id(walkin_id)
        if not walkin:
            raise LookupError(f"Walk-in service {walkin_id} not found")

        # Validate walk-in state
        if walkin.status == WalkInStatus.COMPLETED:
            raise ValueError("Walk-in service is already completed")

        if walkin.status == WalkInStatus.CANCELLED:
            raise ValueError("Cannot complete cancelled walk-in")

        if not walkin.services:
            raise ValueError("Cannot complete walk-in without any services")

        # Check payment status - require full payment before completion
        if walkin.payment_status != PaymentStatus.PAID:
            raise ValueError(
                "Cannot complete walk-in - payment must be completed first"
            )

        # Complete the walk-in
        walkin.complete(completed_by_id, datetime.utcnow())

        # Update in repository
        updated = await self._repository.update(walkin)

        return updated
