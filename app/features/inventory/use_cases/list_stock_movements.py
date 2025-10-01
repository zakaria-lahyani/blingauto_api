"""List stock movements use case."""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.features.inventory.domain.entities import StockMovement
from app.features.inventory.domain.enums import StockMovementType
from app.features.inventory.ports.repositories import IStockMovementRepository


@dataclass
class ListStockMovementsRequest:
    """Request to list stock movements."""

    product_id: Optional[str] = None
    movement_type: Optional[StockMovementType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = 100
    offset: int = 0


class ListStockMovementsUseCase:
    """Use case for listing stock movements with filters."""

    def __init__(self, repository: IStockMovementRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: ListStockMovementsRequest) -> List[StockMovement]:
        """List stock movements."""
        # Validate
        if request.limit < 1 or request.limit > 200:
            raise ValueError("Limit must be between 1 and 200")
        if request.offset < 0:
            raise ValueError("Offset cannot be negative")
        if request.start_date and request.end_date:
            if request.start_date > request.end_date:
                raise ValueError("Start date cannot be after end date")

        # Get movements
        if request.product_id:
            movements = await self._repository.list_by_product(
                product_id=request.product_id,
                movement_type=request.movement_type,
                start_date=request.start_date,
                end_date=request.end_date,
                limit=request.limit,
                offset=request.offset,
            )
        else:
            movements = await self._repository.list_all(
                movement_type=request.movement_type,
                start_date=request.start_date,
                end_date=request.end_date,
                limit=request.limit,
                offset=request.offset,
            )

        return movements
