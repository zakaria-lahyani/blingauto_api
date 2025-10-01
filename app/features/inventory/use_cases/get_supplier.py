"""Get supplier use case."""

from app.features.inventory.domain.entities import Supplier
from app.features.inventory.ports.repositories import ISupplierRepository


class GetSupplierUseCase:
    """Use case for getting a single supplier."""

    def __init__(self, repository: ISupplierRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, supplier_id: str) -> Supplier:
        """Get supplier by ID."""
        supplier = await self._repository.get_by_id(supplier_id)
        if not supplier:
            raise LookupError(f"Supplier {supplier_id} not found")
        return supplier
