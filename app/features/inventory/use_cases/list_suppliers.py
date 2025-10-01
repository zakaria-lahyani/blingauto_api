"""List suppliers use case."""

from dataclasses import dataclass
from typing import List, Optional

from app.features.inventory.domain.entities import Supplier
from app.features.inventory.ports.repositories import ISupplierRepository


@dataclass
class ListSuppliersRequest:
    """Request to list suppliers."""

    is_active: Optional[bool] = None
    limit: int = 100
    offset: int = 0


class ListSuppliersUseCase:
    """Use case for listing suppliers with filters."""

    def __init__(self, repository: ISupplierRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: ListSuppliersRequest) -> List[Supplier]:
        """List suppliers."""
        if request.limit < 1 or request.limit > 200:
            raise ValueError("Limit must be between 1 and 200")
        if request.offset < 0:
            raise ValueError("Offset cannot be negative")

        suppliers = await self._repository.list_all(
            is_active=request.is_active, limit=request.limit, offset=request.offset
        )
        return suppliers
