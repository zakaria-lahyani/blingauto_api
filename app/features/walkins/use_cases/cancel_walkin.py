"""Cancel walk-in service use case."""

from datetime import datetime, timezone
from typing import Optional

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus, PaymentStatus
from app.features.walkins.ports.repositories import IWalkInRepository


class CancelWalkInUseCase:
    """Use case for cancelling walk-in service."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(
        self, walkin_id: str, cancelled_by_id: str, reason: Optional[str] = None
    ) -> WalkInService:
        """
        Cancel walk-in service.

        Args:
            walkin_id: Walk-in service ID
            cancelled_by_id: Staff ID who cancelled
            reason: Cancellation reason

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
            raise ValueError("Cannot cancel completed walk-in service")

        if walkin.status == WalkInStatus.CANCELLED:
            raise ValueError("Walk-in service is already cancelled")

        # Cannot cancel if payment has been made
        if walkin.payment_status == PaymentStatus.PAID:
            raise ValueError(
                "Cannot cancel walk-in with completed payment. Process refund first."
            )

        if walkin.payment_status == PaymentStatus.PARTIAL:
            raise ValueError(
                "Cannot cancel walk-in with partial payment. Process refund first."
            )

        # Cancel the walk-in
        walkin.cancel(cancelled_by_id, datetime.now(timezone.utc), reason)

        # Update in repository
        updated = await self._repository.update(walkin)

        return updated
