"""Create product use case."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
import uuid

from app.features.inventory.domain.entities import Product
from app.features.inventory.domain.enums import ProductCategory, ProductUnit
from app.features.inventory.domain.policies import InventoryManagementPolicy
from app.features.inventory.ports.repositories import IProductRepository


@dataclass
class CreateProductRequest:
    """Request to create product."""

    name: str
    description: Optional[str]
    category: ProductCategory
    unit: ProductUnit
    minimum_quantity: Decimal
    reorder_point: Decimal
    maximum_quantity: Optional[Decimal]
    unit_cost: Decimal
    unit_price: Optional[Decimal]
    supplier_id: Optional[str]
    supplier_sku: Optional[str]
    initial_quantity: Decimal = Decimal("0")
    notes: Optional[str] = None


class CreateProductUseCase:
    """Use case for creating a new product."""

    def __init__(self, repository: IProductRepository):
        """Initialize use case with repository."""
        self._repository = repository

    async def execute(self, request: CreateProductRequest) -> Product:
        """
        Create a new product.

        Args:
            request: Create product request

        Returns:
            Created product

        Raises:
            ValueError: If validation fails
        """
        # Validate request
        self._validate_request(request)

        # Validate stock levels using policy
        InventoryManagementPolicy.validate_stock_levels(
            request.minimum_quantity, request.reorder_point, request.maximum_quantity
        )

        # Validate unit cost using policy
        InventoryManagementPolicy.validate_unit_cost(request.unit_cost)

        # Generate SKU
        product_count = await self._repository.get_next_product_count()
        sku = InventoryManagementPolicy.generate_sku(product_count)

        # Create product entity
        product = Product(
            id=str(uuid.uuid4()),
            sku=sku,
            name=request.name,
            description=request.description,
            category=request.category,
            unit=request.unit,
            current_quantity=request.initial_quantity,
            minimum_quantity=request.minimum_quantity,
            reorder_point=request.reorder_point,
            maximum_quantity=request.maximum_quantity,
            unit_cost=request.unit_cost,
            unit_price=request.unit_price,
            supplier_id=request.supplier_id,
            supplier_sku=request.supplier_sku,
            is_active=True,
            notes=request.notes,
        )

        # Save to repository
        created = await self._repository.create(product)

        return created

    def _validate_request(self, request: CreateProductRequest) -> None:
        """Validate create request."""
        if not request.name or not request.name.strip():
            raise ValueError("Product name is required")

        if request.initial_quantity < Decimal("0"):
            raise ValueError("Initial quantity cannot be negative")

        if request.unit_price is not None and request.unit_price < Decimal("0"):
            raise ValueError("Unit price cannot be negative")
