"""Inventory domain entities."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.features.inventory.domain.enums import (
    ProductCategory,
    ProductUnit,
    StockMovementType,
    StockStatus,
)


@dataclass
class Product:
    """Product entity - items used in car wash services."""

    # Required fields
    id: str
    sku: str  # Stock Keeping Unit (auto-generated: PRD-00001)
    name: str
    category: ProductCategory
    unit: ProductUnit
    current_quantity: Decimal
    minimum_quantity: Decimal  # Alert threshold
    reorder_point: Decimal  # Reorder when stock reaches this level
    unit_cost: Decimal  # Cost per unit

    # Optional fields with defaults
    description: Optional[str] = None
    maximum_quantity: Optional[Decimal] = None  # Max storage capacity
    unit_price: Optional[Decimal] = None  # Selling price (if sold separately)
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_stock_status(self) -> StockStatus:
        """Get current stock status based on quantity levels."""
        if self.current_quantity == Decimal("0"):
            return StockStatus.OUT_OF_STOCK

        if self.current_quantity < self.reorder_point:
            return StockStatus.LOW_STOCK

        if self.maximum_quantity and self.current_quantity > self.maximum_quantity:
            return StockStatus.OVERSTOCKED

        return StockStatus.IN_STOCK

    def needs_reorder(self) -> bool:
        """Check if product needs to be reordered."""
        return self.current_quantity <= self.reorder_point

    def calculate_reorder_quantity(self) -> Decimal:
        """Calculate recommended reorder quantity."""
        if not self.needs_reorder():
            return Decimal("0")

        # Reorder to maximum if set, otherwise to minimum + buffer
        target = self.maximum_quantity if self.maximum_quantity else (
            self.minimum_quantity * Decimal("2")
        )

        return max(Decimal("0"), target - self.current_quantity)

    def calculate_stock_value(self) -> Decimal:
        """Calculate total value of current stock."""
        return self.current_quantity * self.unit_cost

    def update_quantity(self, quantity_change: Decimal) -> None:
        """Update stock quantity with validation."""
        new_quantity = self.current_quantity + quantity_change

        if new_quantity < Decimal("0"):
            raise ValueError(
                f"Insufficient stock. Current: {self.current_quantity}, "
                f"Requested: {abs(quantity_change)}"
            )

        self.current_quantity = new_quantity
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class StockMovement:
    """Stock movement entity - tracks all inventory changes."""

    # Required fields
    id: str
    product_id: str
    movement_type: StockMovementType
    quantity: Decimal  # Positive for IN, negative for OUT
    quantity_before: Decimal
    quantity_after: Decimal
    unit_cost: Decimal  # Cost at time of movement
    total_cost: Decimal  # quantity * unit_cost
    performed_by_id: str  # Staff who performed the movement

    # Optional fields with defaults
    reference_type: Optional[str] = None  # "PURCHASE_ORDER", "WALK_IN_SERVICE", etc.
    reference_id: Optional[str] = None  # ID of related entity
    reason: Optional[str] = None
    notes: Optional[str] = None
    movement_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def validate(self) -> None:
        """Validate stock movement data."""
        # Quantity should match movement type
        if self.movement_type in (StockMovementType.IN, StockMovementType.RETURN):
            if self.quantity <= Decimal("0"):
                raise ValueError(f"IN/RETURN movements must have positive quantity")

        elif self.movement_type in (StockMovementType.OUT, StockMovementType.WASTE):
            if self.quantity >= Decimal("0"):
                raise ValueError(f"OUT/WASTE movements must have negative quantity")

        # Verify quantity_after calculation
        expected_after = self.quantity_before + self.quantity
        if abs(self.quantity_after - expected_after) > Decimal("0.001"):
            raise ValueError(
                f"Quantity mismatch. Before: {self.quantity_before}, "
                f"Change: {self.quantity}, Expected After: {expected_after}, "
                f"Actual After: {self.quantity_after}"
            )

        # Unit cost should be positive
        if self.unit_cost < Decimal("0"):
            raise ValueError("Unit cost cannot be negative")

        # Total cost should match
        expected_total = abs(self.quantity) * self.unit_cost
        if abs(self.total_cost - expected_total) > Decimal("0.01"):
            raise ValueError(
                f"Total cost mismatch. Expected: {expected_total}, "
                f"Actual: {self.total_cost}"
            )


@dataclass
class Supplier:
    """Supplier entity - vendors who supply products."""

    id: str
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    # Payment terms
    payment_terms: Optional[str] = None  # "Net 30", "COD", etc.

    # Status
    is_active: bool = True

    # Ratings and notes
    rating: Optional[int] = None  # 1-5 stars
    notes: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def validate_rating(self) -> None:
        """Validate supplier rating."""
        if self.rating is not None:
            if self.rating < 1 or self.rating > 5:
                raise ValueError("Rating must be between 1 and 5")


@dataclass
class LowStockAlert:
    """Low stock alert entity - tracks products needing reorder."""

    product_id: str
    product_name: str
    current_quantity: Decimal
    reorder_point: Decimal
    recommended_order_quantity: Decimal
    stock_status: StockStatus
    alert_generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
