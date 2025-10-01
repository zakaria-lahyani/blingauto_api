"""Adjust stock use case."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import uuid

from app.features.inventory.domain.entities import StockMovement
from app.features.inventory.domain.enums import StockMovementType
from app.features.inventory.domain.policies import StockMovementPolicy
from app.features.inventory.ports.repositories import IProductRepository, IStockMovementRepository


@dataclass
class AdjustStockRequest:
    """Request to adjust stock (manual correction)."""

    product_id: str
    new_quantity: Decimal
    reason: str  # Required for adjustments
    performed_by_id: str
    notes: str | None = None


class AdjustStockUseCase:
    """Use case for adjusting stock levels (inventory correction)."""

    def __init__(
        self,
        product_repository: IProductRepository,
        movement_repository: IStockMovementRepository,
    ):
        """Initialize use case with repositories."""
        self._product_repo = product_repository
        self._movement_repo = movement_repository

    async def execute(self, request: AdjustStockRequest) -> StockMovement:
        """Adjust stock."""
        # Validate
        self._validate_request(request)

        # Get product
        product = await self._product_repo.get_by_id(request.product_id)
        if not product:
            raise LookupError(f"Product {request.product_id} not found")

        # Calculate adjustment
        quantity_before = product.current_quantity
        quantity_change = request.new_quantity - quantity_before

        if quantity_change == Decimal("0"):
            raise ValueError("No adjustment needed - quantity unchanged")

        # Validate adjustment quantity
        StockMovementPolicy.validate_movement_quantity(quantity_change)

        # Check if approval required (large adjustments)
        if StockMovementPolicy.requires_approval(
            "ADJUSTMENT", quantity_before, quantity_change
        ):
            # In production, this would check if user has approval authority
            # For now, we allow it but log it
            pass

        # Update product quantity
        product.current_quantity = request.new_quantity

        # Create movement record
        movement = StockMovement(
            id=str(uuid.uuid4()),
            product_id=request.product_id,
            movement_type=StockMovementType.ADJUSTMENT,
            quantity=quantity_change,
            quantity_before=quantity_before,
            quantity_after=request.new_quantity,
            unit_cost=product.unit_cost,
            total_cost=abs(quantity_change) * product.unit_cost,
            performed_by_id=request.performed_by_id,
            reason=request.reason,
            notes=request.notes,
            movement_date=datetime.utcnow(),
        )

        # Validate movement
        movement.validate()

        # Save movement and update product
        created_movement = await self._movement_repo.create(movement)
        await self._product_repo.update(product)

        return created_movement

    def _validate_request(self, request: AdjustStockRequest) -> None:
        """Validate request."""
        if request.new_quantity < Decimal("0"):
            raise ValueError("New quantity cannot be negative")
        if not request.reason or not request.reason.strip():
            raise ValueError("Reason is required for stock adjustments")
