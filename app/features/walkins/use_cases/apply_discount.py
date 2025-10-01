"""Apply discount to walk-in use case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.features.walkins.domain.entities import WalkInService
from app.features.walkins.domain.enums import WalkInStatus
from app.features.walkins.domain.policies import WalkInPricingPolicy
from app.features.walkins.ports.repositories import IWalkInRepository


@dataclass
class ApplyDiscountRequest:
    """Request to apply discount."""

    walkin_id: str
    discount_percent: Decimal
    discount_reason: Optional[str] = None


class ApplyDiscountUseCase:
    """Use case for applying discount to walk-in."""

    def __init__(self, repository: IWalkInRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: ApplyDiscountRequest) -> WalkInService:
        """
        Apply discount to walk-in.

        Args:
            request: Apply discount request

        Returns:
            Updated walk-in service

        Raises:
            ValueError: If validation fails
            LookupError: If walk-in not found
        """
        # Validate request
        self._validate_request(request)

        # Get walk-in
        walkin = await self._repository.get_by_id(request.walkin_id)
        if not walkin:
            raise LookupError(f"Walk-in service {request.walkin_id} not found")

        # Validate walk-in state
        if walkin.status == WalkInStatus.COMPLETED:
            raise ValueError("Cannot apply discount to completed walk-in")

        if walkin.status == WalkInStatus.CANCELLED:
            raise ValueError("Cannot apply discount to cancelled walk-in")

        # Validate discount using policy
        discount_amount = (walkin.total_amount * request.discount_percent) / Decimal(
            "100"
        )
        WalkInPricingPolicy.validate_discount(walkin.total_amount, discount_amount)

        # Apply discount
        walkin.apply_discount(request.discount_percent, request.discount_reason)

        # Update in repository
        updated = await self._repository.update(walkin)

        return updated

    def _validate_request(self, request: ApplyDiscountRequest) -> None:
        """Validate apply discount request."""
        if not request.walkin_id or not request.walkin_id.strip():
            raise ValueError("Walk-in ID is required")

        if request.discount_percent < Decimal("0"):
            raise ValueError("Discount percent cannot be negative")

        if request.discount_percent > Decimal("100"):
            raise ValueError("Discount percent cannot exceed 100%")
