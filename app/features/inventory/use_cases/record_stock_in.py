"""Record stock in use case."""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import uuid

from app.features.inventory.domain.entities import StockMovement
from app.features.inventory.domain.enums import StockMovementType
from app.features.inventory.domain.policies import StockMovementPolicy
from app.features.inventory.ports.repositories import IProductRepository, IStockMovementRepository


@dataclass
class RecordStockInRequest:
    """Request to record stock in (purchase, return to stock)."""

    product_id: str
    quantity: Decimal
    unit_cost: Decimal
    performed_by_id: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class RecordStockInUseCase:
    """Use case for recording stock in (receiving inventory)."""

    def __init__(
        self,
        product_repository: IProductRepository,
        movement_repository: IStockMovementRepository,
    ):
        """Initialize use case with repositories."""
        self._product_repo = product_repository
        self._movement_repo = movement_repository

    async def execute(self, request: RecordStockInRequest) -> StockMovement:
        """Record stock in."""
        # Validate
        self._validate_request(request)
        StockMovementPolicy.validate_movement_quantity(request.quantity)

        # Get product
        product = await self._product_repo.get_by_id(request.product_id)
        if not product:
            raise LookupError(f"Product {request.product_id} not found")

        # Record before quantity
        quantity_before = product.current_quantity

        # Update product quantity
        product.update_quantity(request.quantity)

        # Create movement record
        movement = StockMovement(
            id=str(uuid.uuid4()),
            product_id=request.product_id,
            movement_type=StockMovementType.IN,
            quantity=request.quantity,
            quantity_before=quantity_before,
            quantity_after=product.current_quantity,
            unit_cost=request.unit_cost,
            total_cost=request.quantity * request.unit_cost,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
            performed_by_id=request.performed_by_id,
            reason=request.reason,
            notes=request.notes,
            movement_date=datetime.now(timezone.utc),
        )

        # Validate movement
        movement.validate()

        # Save movement and update product
        created_movement = await self._movement_repo.create(movement)
        await self._product_repo.update(product)

        return created_movement

    def _validate_request(self, request: RecordStockInRequest) -> None:
        """Validate request."""
        if request.quantity <= Decimal("0"):
            raise ValueError("Stock in quantity must be positive")
        if request.unit_cost < Decimal("0"):
            raise ValueError("Unit cost cannot be negative")
