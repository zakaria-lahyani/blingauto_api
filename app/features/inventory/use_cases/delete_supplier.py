"""Delete supplier use case."""

from app.features.inventory.ports.repositories import ISupplierRepository


class DeleteSupplierUseCase:
    """Use case for deleting (soft delete) a supplier."""

    def __init__(self, repository: ISupplierRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, supplier_id: str) -> None:
        """Delete supplier (soft delete)."""
        supplier = await self._repository.get_by_id(supplier_id)
        if not supplier:
            raise LookupError(f"Supplier {supplier_id} not found")

        await self._repository.delete(supplier_id)
