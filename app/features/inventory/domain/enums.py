"""Inventory domain enums."""

from enum import Enum


class ProductCategory(str, Enum):
    """Product categories."""

    CLEANING_CHEMICAL = "CLEANING_CHEMICAL"  # Soaps, detergents, wax
    EQUIPMENT = "EQUIPMENT"  # Brushes, sponges, towels, buckets
    PROTECTIVE = "PROTECTIVE"  # Gloves, aprons, masks
    ACCESSORY = "ACCESSORY"  # Air fresheners, tire shine
    CONSUMABLE = "CONSUMABLE"  # Paper towels, trash bags
    SPARE_PART = "SPARE_PART"  # Equipment replacement parts
    OTHER = "OTHER"


class ProductUnit(str, Enum):
    """Product measurement units."""

    LITER = "LITER"  # L
    MILLILITER = "MILLILITER"  # ML
    KILOGRAM = "KILOGRAM"  # KG
    GRAM = "GRAM"  # G
    PIECE = "PIECE"  # Individual items
    PACK = "PACK"  # Package/bundle
    BOX = "BOX"  # Box
    BOTTLE = "BOTTLE"  # Bottle
    GALLON = "GALLON"  # Gallon


class StockMovementType(str, Enum):
    """Stock movement types."""

    IN = "IN"  # Stock received (purchase, return)
    OUT = "OUT"  # Stock used/sold
    ADJUSTMENT = "ADJUSTMENT"  # Manual correction
    RETURN = "RETURN"  # Return to supplier
    WASTE = "WASTE"  # Damaged/expired
    TRANSFER = "TRANSFER"  # Transfer between locations


class StockStatus(str, Enum):
    """Stock status based on quantity levels."""

    IN_STOCK = "IN_STOCK"  # quantity >= reorder_point
    LOW_STOCK = "LOW_STOCK"  # quantity < reorder_point
    OUT_OF_STOCK = "OUT_OF_STOCK"  # quantity = 0
    OVERSTOCKED = "OVERSTOCKED"  # quantity > maximum_level (if set)
