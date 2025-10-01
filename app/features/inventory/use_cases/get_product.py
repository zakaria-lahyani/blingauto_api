"""Get product use case."""

from app.features.inventory.domain.entities import Product
from app.features.inventory.ports.repositories import IProductRepository


class GetProductUseCase:
    """Use case for getting a single product."""

    def __init__(self, repository: IProductRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, product_id: str) -> Product:
        """Get product by ID."""
        product = await self._repository.get_by_id(product_id)
        if not product:
            raise LookupError(f"Product {product_id} not found")
        return product
