"""Inventory repository interfaces."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional

from app.features.inventory.domain.entities import (
    Product,
    StockMovement,
    Supplier,
    LowStockAlert,
)
from app.features.inventory.domain.enums import (
    ProductCategory,
    StockMovementType,
    StockStatus,
)


class IProductRepository(ABC):
    """Product repository interface."""

    @abstractmethod
    async def create(self, product: Product) -> Product:
        """Create new product."""
        pass

    @abstractmethod
    async def update(self, product: Product) -> Product:
        """Update existing product."""
        pass

    @abstractmethod
    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        pass

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        pass

    @abstractmethod
    async def list_all(
        self,
        category: Optional[ProductCategory] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Product]:
        """List products with filters."""
        pass

    @abstractmethod
    async def list_low_stock(self) -> List[Product]:
        """List products with low stock (quantity <= reorder_point)."""
        pass

    @abstractmethod
    async def list_out_of_stock(self) -> List[Product]:
        """List products that are out of stock."""
        pass

    @abstractmethod
    async def get_next_product_count(self) -> int:
        """Get count of products for SKU generation."""
        pass

    @abstractmethod
    async def delete(self, product_id: str) -> None:
        """Soft delete product."""
        pass


class IStockMovementRepository(ABC):
    """Stock movement repository interface."""

    @abstractmethod
    async def create(self, movement: StockMovement) -> StockMovement:
        """Create stock movement."""
        pass

    @abstractmethod
    async def get_by_id(self, movement_id: str) -> Optional[StockMovement]:
        """Get movement by ID."""
        pass

    @abstractmethod
    async def list_by_product(
        self,
        product_id: str,
        movement_type: Optional[StockMovementType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StockMovement]:
        """List movements for a product."""
        pass

    @abstractmethod
    async def list_all(
        self,
        movement_type: Optional[StockMovementType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StockMovement]:
        """List all movements with filters."""
        pass

    @abstractmethod
    async def get_total_usage_by_product(
        self, product_id: str, start_date: date, end_date: date
    ) -> dict:
        """Get total usage (OUT movements) for a product in date range."""
        pass


class ISupplierRepository(ABC):
    """Supplier repository interface."""

    @abstractmethod
    async def create(self, supplier: Supplier) -> Supplier:
        """Create supplier."""
        pass

    @abstractmethod
    async def update(self, supplier: Supplier) -> Supplier:
        """Update supplier."""
        pass

    @abstractmethod
    async def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID."""
        pass

    @abstractmethod
    async def list_all(
        self, is_active: Optional[bool] = None, limit: int = 100, offset: int = 0
    ) -> List[Supplier]:
        """List suppliers with filters."""
        pass

    @abstractmethod
    async def delete(self, supplier_id: str) -> None:
        """Soft delete supplier."""
        pass
