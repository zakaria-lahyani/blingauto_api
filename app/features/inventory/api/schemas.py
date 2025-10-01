"""Inventory API schemas (DTOs)."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.features.inventory.domain.enums import (
    ProductCategory,
    ProductUnit,
    StockMovementType,
    StockStatus,
)


# ============================================================================
# Product Schemas
# ============================================================================


class CreateProductSchema(BaseModel):
    """Request to create product."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: ProductCategory
    unit: ProductUnit
    minimum_quantity: Decimal = Field(..., ge=0, decimal_places=2)
    reorder_point: Decimal = Field(..., ge=0, decimal_places=2)
    maximum_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    unit_cost: Decimal = Field(..., gt=0, decimal_places=2)
    unit_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = Field(None, max_length=100)
    initial_quantity: Decimal = Field(Decimal("0"), ge=0, decimal_places=2)
    notes: Optional[str] = None


class UpdateProductSchema(BaseModel):
    """Request to update product."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    unit: Optional[ProductUnit] = None
    minimum_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    reorder_point: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    maximum_quantity: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    unit_cost: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    unit_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    supplier_id: Optional[str] = None
    supplier_sku: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ProductSchema(BaseModel):
    """Product response."""

    id: str
    sku: str
    name: str
    description: Optional[str]
    category: ProductCategory
    unit: ProductUnit
    current_quantity: Decimal
    minimum_quantity: Decimal
    reorder_point: Decimal
    maximum_quantity: Optional[Decimal]
    unit_cost: Decimal
    unit_price: Optional[Decimal]
    supplier_id: Optional[str]
    supplier_sku: Optional[str]
    is_active: bool
    stock_status: StockStatus
    stock_value: Decimal
    needs_reorder: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListSchema(BaseModel):
    """List of products response."""

    items: List[ProductSchema]
    total: int
    limit: int
    offset: int


# ============================================================================
# Stock Movement Schemas
# ============================================================================


class RecordStockInSchema(BaseModel):
    """Request to record stock in."""

    quantity: Decimal = Field(..., gt=0, decimal_places=2)
    unit_cost: Decimal = Field(..., gt=0, decimal_places=2)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class RecordStockOutSchema(BaseModel):
    """Request to record stock out."""

    quantity: Decimal = Field(..., gt=0, decimal_places=2)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class AdjustStockSchema(BaseModel):
    """Request to adjust stock."""

    new_quantity: Decimal = Field(..., ge=0, decimal_places=2)
    reason: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = None


class StockMovementSchema(BaseModel):
    """Stock movement response."""

    id: str
    product_id: str
    movement_type: StockMovementType
    quantity: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    reference_type: Optional[str]
    reference_id: Optional[str]
    performed_by_id: str
    reason: Optional[str]
    notes: Optional[str]
    movement_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class StockMovementListSchema(BaseModel):
    """List of stock movements response."""

    items: List[StockMovementSchema]
    total: int
    limit: int
    offset: int


# ============================================================================
# Supplier Schemas
# ============================================================================


class CreateSupplierSchema(BaseModel):
    """Request to create supplier."""

    name: str = Field(..., min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    payment_terms: Optional[str] = Field(None, max_length=200)
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class UpdateSupplierSchema(BaseModel):
    """Request to update supplier."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    payment_terms: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class SupplierSchema(BaseModel):
    """Supplier response."""

    id: str
    name: str
    contact_person: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    payment_terms: Optional[str]
    is_active: bool
    rating: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListSchema(BaseModel):
    """List of suppliers response."""

    items: List[SupplierSchema]
    total: int
    limit: int
    offset: int


# ============================================================================
# Alert Schemas
# ============================================================================


class LowStockAlertSchema(BaseModel):
    """Low stock alert response."""

    product_id: str
    product_name: str
    current_quantity: Decimal
    reorder_point: Decimal
    recommended_order_quantity: Decimal
    stock_status: StockStatus
    alert_generated_at: datetime

    class Config:
        from_attributes = True


class LowStockAlertsListSchema(BaseModel):
    """List of low stock alerts."""

    items: List[LowStockAlertSchema]
    total: int


# ============================================================================
# Error Response Schema
# ============================================================================


class ErrorResponseSchema(BaseModel):
    """Error response."""

    detail: str
    error_code: Optional[str] = None
