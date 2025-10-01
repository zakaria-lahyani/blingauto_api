"""Delete product use case."""

from app.features.inventory.ports.repositories import IProductRepository


class DeleteProductUseCase:
    """Use case for deleting (soft delete) a product."""

    def __init__(self, repository: IProductRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, product_id: str) -> None:
        """Delete product (soft delete)."""
        product = await self._repository.get_by_id(product_id)
        if not product:
            raise LookupError(f"Product {product_id} not found")

        await self._repository.delete(product_id)
