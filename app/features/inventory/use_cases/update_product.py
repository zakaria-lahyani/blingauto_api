"""Update product use case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.features.inventory.domain.entities import Product
from app.features.inventory.domain.enums import ProductCategory, ProductUnit
from app.features.inventory.domain.policies import InventoryManagementPolicy
from app.features.inventory.ports.repositories import IProductRepository


@dataclass
class UpdateProductRequest:
    """Request to update product."""

    product_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    unit: Optional[ProductUnit] = None
    minimum_quantity: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    maximum_quantity: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class UpdateProductUseCase:
    """Use case for updating existing product."""

    def __init__(self, repository: IProductRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: UpdateProductRequest) -> Product:
        """Update product."""
        # Get existing product
        product = await self._repository.get_by_id(request.product_id)
        if not product:
            raise LookupError(f"Product {request.product_id} not found")

        # Update fields if provided
        if request.name is not None:
            product.name = request.name
        if request.description is not None:
            product.description = request.description
        if request.category is not None:
            product.category = request.category
        if request.unit is not None:
            product.unit = request.unit
        if request.minimum_quantity is not None:
            product.minimum_quantity = request.minimum_quantity
        if request.reorder_point is not None:
            product.reorder_point = request.reorder_point
        if request.maximum_quantity is not None:
            product.maximum_quantity = request.maximum_quantity
        if request.unit_cost is not None:
            InventoryManagementPolicy.validate_unit_cost(request.unit_cost)
            product.unit_cost = request.unit_cost
        if request.unit_price is not None:
            product.unit_price = request.unit_price
        if request.supplier_id is not None:
            product.supplier_id = request.supplier_id
        if request.supplier_sku is not None:
            product.supplier_sku = request.supplier_sku
        if request.is_active is not None:
            product.is_active = request.is_active
        if request.notes is not None:
            product.notes = request.notes

        # Validate stock levels
        InventoryManagementPolicy.validate_stock_levels(
            product.minimum_quantity, product.reorder_point, product.maximum_quantity
        )

        # Update in repository
        updated = await self._repository.update(product)
        return updated
