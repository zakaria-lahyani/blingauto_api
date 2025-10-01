"""Get low stock alerts use case."""

from typing import List

from app.features.inventory.domain.entities import LowStockAlert
from app.features.inventory.ports.repositories import IProductRepository


class GetLowStockAlertsUseCase:
    """Use case for getting low stock alerts."""

    def __init__(self, repository: IProductRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self) -> List[LowStockAlert]:
        """Get all low stock alerts."""
        # Get low stock products
        products = await self._repository.list_low_stock()

        # Convert to alerts
        alerts = [
            LowStockAlert(
                product_id=p.id,
                product_name=p.name,
                current_quantity=p.current_quantity,
                reorder_point=p.reorder_point,
                recommended_order_quantity=p.calculate_reorder_quantity(),
                stock_status=p.get_stock_status(),
            )
            for p in products
        ]

        return alerts
