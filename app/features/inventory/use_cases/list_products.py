"""List products use case."""

from dataclasses import dataclass
from typing import List, Optional

from app.features.inventory.domain.entities import Product
from app.features.inventory.domain.enums import ProductCategory
from app.features.inventory.ports.repositories import IProductRepository


@dataclass
class ListProductsRequest:
    """Request to list products."""

    category: Optional[ProductCategory] = None
    is_active: Optional[bool] = None
    limit: int = 100
    offset: int = 0


class ListProductsUseCase:
    """Use case for listing products with filters."""

    def __init__(self, repository: IProductRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: ListProductsRequest) -> List[Product]:
        """List products."""
        if request.limit < 1 or request.limit > 200:
            raise ValueError("Limit must be between 1 and 200")
        if request.offset < 0:
            raise ValueError("Offset cannot be negative")

        products = await self._repository.list_all(
            category=request.category,
            is_active=request.is_active,
            limit=request.limit,
            offset=request.offset,
        )
        return products
