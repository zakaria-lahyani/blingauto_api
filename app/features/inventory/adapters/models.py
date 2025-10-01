"""Inventory database models."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    Boolean,
    Text,
    Integer,
    Index,
)

from app.core.database import Base


class ProductModel(Base):
    """Product database model."""

    __tablename__ = "products"

    # Primary identification
    id = Column(String, primary_key=True)
    sku = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, index=True)
    unit = Column(String(20), nullable=False)

    # Stock levels
    current_quantity = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    minimum_quantity = Column(Numeric(10, 2), nullable=False)
    reorder_point = Column(Numeric(10, 2), nullable=False)
    maximum_quantity = Column(Numeric(10, 2), nullable=True)

    # Pricing
    unit_cost = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=True)

    # Supplier info (string-based FK)
    supplier_id = Column(String, nullable=True, index=True)
    supplier_sku = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("ix_products_sku", "sku"),
        Index("ix_products_name", "name"),
        Index("ix_products_category_active", "category", "is_active"),
        Index("ix_products_supplier", "supplier_id"),
        Index("ix_products_current_quantity", "current_quantity"),
        Index("ix_products_reorder", "current_quantity", "reorder_point"),
    )


class StockMovementModel(Base):
    """Stock movement database model."""

    __tablename__ = "stock_movements"

    # Primary identification
    id = Column(String, primary_key=True)
    product_id = Column(String, nullable=False, index=True)

    # Movement details
    movement_type = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(10, 2), nullable=False)

    # Audit trail
    quantity_before = Column(Numeric(10, 2), nullable=False)
    quantity_after = Column(Numeric(10, 2), nullable=False)

    # Cost tracking
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)

    # Reference information
    reference_type = Column(String(50), nullable=True, index=True)
    reference_id = Column(String, nullable=True, index=True)

    # User tracking
    performed_by_id = Column(String, nullable=False, index=True)

    # Details
    reason = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    movement_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("ix_stock_movements_product", "product_id"),
        Index("ix_stock_movements_type", "movement_type"),
        Index("ix_stock_movements_date", "movement_date"),
        Index("ix_stock_movements_product_date", "product_id", "movement_date"),
        Index("ix_stock_movements_type_date", "movement_type", "movement_date"),
        Index("ix_stock_movements_reference", "reference_type", "reference_id"),
        Index("ix_stock_movements_performed_by", "performed_by_id"),
    )


class SupplierModel(Base):
    """Supplier database model."""

    __tablename__ = "suppliers"

    # Primary identification
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False, index=True)

    # Contact information
    contact_person = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    address = Column(Text, nullable=True)

    # Payment terms
    payment_terms = Column(String(200), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Ratings and notes
    rating = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("ix_suppliers_name", "name"),
        Index("ix_suppliers_email", "email"),
        Index("ix_suppliers_phone", "phone"),
        Index("ix_suppliers_active", "is_active"),
        Index("ix_suppliers_rating", "rating"),
    )
