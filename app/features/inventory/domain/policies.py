"""Inventory domain policies - Business rules."""

from decimal import Decimal
from typing import Optional


class InventoryManagementPolicy:
    """Business rules for inventory management."""

    # SKU generation
    SKU_PREFIX = "PRD"
    SKU_LENGTH = 5  # PRD-00001

    # Stock level rules
    MIN_REORDER_POINT_MULTIPLIER = Decimal("1.5")  # Reorder point should be 1.5x minimum
    DEFAULT_BUFFER_STOCK_MULTIPLIER = Decimal("0.2")  # 20% buffer above minimum

    # Quantity rules
    MIN_QUANTITY = Decimal("0")
    MAX_QUANTITY_DIGITS = 10  # Max 9999999999.99

    # Cost rules
    MIN_UNIT_COST = Decimal("0.01")
    MAX_UNIT_COST = Decimal("999999.99")

    @staticmethod
    def generate_sku(product_count: int) -> str:
        """
        Generate SKU for product.

        Args:
            product_count: Current number of products

        Returns:
            SKU in format PRD-00001, PRD-00002, etc.
        """
        return f"{InventoryManagementPolicy.SKU_PREFIX}-{product_count + 1:05d}"

    @staticmethod
    def validate_stock_levels(
        minimum_quantity: Decimal,
        reorder_point: Decimal,
        maximum_quantity: Optional[Decimal] = None,
    ) -> None:
        """
        Validate stock level configuration.

        Args:
            minimum_quantity: Minimum stock level
            reorder_point: Reorder threshold
            maximum_quantity: Maximum stock level (optional)

        Raises:
            ValueError: If validation fails
        """
        if minimum_quantity < InventoryManagementPolicy.MIN_QUANTITY:
            raise ValueError("Minimum quantity cannot be negative")

        if reorder_point < minimum_quantity:
            raise ValueError("Reorder point must be >= minimum quantity")

        # Recommended: reorder point should be 1.5x minimum
        recommended_reorder = (
            minimum_quantity * InventoryManagementPolicy.MIN_REORDER_POINT_MULTIPLIER
        )
        if reorder_point < recommended_reorder:
            # Warning, not error
            pass

        if maximum_quantity is not None:
            if maximum_quantity <= reorder_point:
                raise ValueError("Maximum quantity must be > reorder point")

    @staticmethod
    def validate_unit_cost(unit_cost: Decimal) -> None:
        """
        Validate product unit cost.

        Args:
            unit_cost: Cost per unit

        Raises:
            ValueError: If validation fails
        """
        if unit_cost < InventoryManagementPolicy.MIN_UNIT_COST:
            raise ValueError(
                f"Unit cost must be >= {InventoryManagementPolicy.MIN_UNIT_COST}"
            )

        if unit_cost > InventoryManagementPolicy.MAX_UNIT_COST:
            raise ValueError(
                f"Unit cost cannot exceed {InventoryManagementPolicy.MAX_UNIT_COST}"
            )

    @staticmethod
    def calculate_recommended_reorder_point(minimum_quantity: Decimal) -> Decimal:
        """
        Calculate recommended reorder point based on minimum quantity.

        Args:
            minimum_quantity: Minimum stock level

        Returns:
            Recommended reorder point (1.5x minimum)
        """
        return minimum_quantity * InventoryManagementPolicy.MIN_REORDER_POINT_MULTIPLIER

    @staticmethod
    def calculate_recommended_maximum(minimum_quantity: Decimal) -> Decimal:
        """
        Calculate recommended maximum quantity.

        Args:
            minimum_quantity: Minimum stock level

        Returns:
            Recommended maximum (3x minimum)
        """
        return minimum_quantity * Decimal("3")


class StockMovementPolicy:
    """Business rules for stock movements."""

    # Movement quantity rules
    MAX_MOVEMENT_QUANTITY = Decimal("999999.99")

    # Adjustment rules
    MAX_ADJUSTMENT_PERCENT = Decimal("50")  # Max 50% adjustment without approval

    @staticmethod
    def validate_movement_quantity(quantity: Decimal) -> None:
        """
        Validate movement quantity.

        Args:
            quantity: Movement quantity (can be negative)

        Raises:
            ValueError: If validation fails
        """
        if abs(quantity) > StockMovementPolicy.MAX_MOVEMENT_QUANTITY:
            raise ValueError(
                f"Movement quantity cannot exceed {StockMovementPolicy.MAX_MOVEMENT_QUANTITY}"
            )

        if abs(quantity) == Decimal("0"):
            raise ValueError("Movement quantity cannot be zero")

    @staticmethod
    def requires_approval(
        movement_type: str, quantity_before: Decimal, quantity_change: Decimal
    ) -> bool:
        """
        Check if movement requires manager approval.

        Large adjustments (>50% change) require approval.

        Args:
            movement_type: Type of movement
            quantity_before: Quantity before movement
            quantity_change: Quantity change

        Returns:
            True if approval required
        """
        if movement_type != "ADJUSTMENT":
            return False

        if quantity_before == Decimal("0"):
            return True  # Adjustments from zero always need approval

        # Calculate percent change
        percent_change = abs(quantity_change / quantity_before * Decimal("100"))

        return percent_change > StockMovementPolicy.MAX_ADJUSTMENT_PERCENT


class SupplierManagementPolicy:
    """Business rules for supplier management."""

    # Validation rules
    MIN_RATING = 1
    MAX_RATING = 5

    @staticmethod
    def validate_rating(rating: Optional[int]) -> None:
        """
        Validate supplier rating.

        Args:
            rating: Rating value (1-5)

        Raises:
            ValueError: If validation fails
        """
        if rating is None:
            return

        if rating < SupplierManagementPolicy.MIN_RATING:
            raise ValueError(
                f"Rating must be >= {SupplierManagementPolicy.MIN_RATING}"
            )

        if rating > SupplierManagementPolicy.MAX_RATING:
            raise ValueError(
                f"Rating cannot exceed {SupplierManagementPolicy.MAX_RATING}"
            )

    @staticmethod
    def validate_contact_info(
        email: Optional[str], phone: Optional[str]
    ) -> None:
        """
        Validate supplier contact information.

        At least one contact method required.

        Args:
            email: Email address
            phone: Phone number

        Raises:
            ValueError: If validation fails
        """
        if not email and not phone:
            raise ValueError("At least one contact method (email or phone) is required")
