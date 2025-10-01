"""Walk-in API schemas (DTOs)."""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.features.walkins.domain.enums import (
    WalkInStatus,
    PaymentStatus,
    PaymentMethod,
    VehicleSize,
)


# ============================================================================
# Request Schemas
# ============================================================================


class CreateWalkInSchema(BaseModel):
    """Request to create walk-in service."""

    vehicle_make: str = Field(..., min_length=1, max_length=100)
    vehicle_model: str = Field(..., min_length=1, max_length=100)
    vehicle_color: str = Field(..., min_length=1, max_length=50)
    vehicle_size: VehicleSize
    license_plate: Optional[str] = Field(None, max_length=20)
    customer_name: Optional[str] = Field(None, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class AddServiceSchema(BaseModel):
    """Request to add service to walk-in."""

    service_id: str = Field(..., min_length=1)
    service_name: str = Field(..., min_length=1, max_length=200)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    product_costs: Decimal = Field(Decimal("0.00"), ge=0, decimal_places=2)
    quantity: int = Field(1, ge=1)
    notes: Optional[str] = None


class ApplyDiscountSchema(BaseModel):
    """Request to apply discount."""

    discount_percent: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    discount_reason: Optional[str] = Field(None, max_length=200)


class RecordPaymentSchema(BaseModel):
    """Request to record payment."""

    amount: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: PaymentMethod
    transaction_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class CancelWalkInSchema(BaseModel):
    """Request to cancel walk-in."""

    reason: Optional[str] = Field(None, max_length=500)


class ListWalkInsQuerySchema(BaseModel):
    """Query parameters for listing walk-ins."""

    status: Optional[WalkInStatus] = None
    payment_status: Optional[PaymentStatus] = None
    created_by_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


# ============================================================================
# Response Schemas
# ============================================================================


class WalkInServiceItemSchema(BaseModel):
    """Walk-in service item response."""

    id: str
    service_id: str
    service_name: str
    price: Decimal
    product_costs: Decimal
    quantity: int
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class WalkInServiceSchema(BaseModel):
    """Walk-in service response."""

    id: str
    service_number: str
    vehicle_make: str
    vehicle_model: str
    vehicle_color: str
    vehicle_size: VehicleSize
    license_plate: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    status: WalkInStatus
    payment_status: PaymentStatus
    services: List[WalkInServiceItemSchema]
    total_amount: Decimal
    discount_amount: Decimal
    discount_reason: Optional[str] = None
    final_amount: Decimal
    paid_amount: Decimal
    started_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_by_id: str
    completed_by_id: Optional[str] = None
    cancelled_by_id: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalkInServiceListSchema(BaseModel):
    """List of walk-in services response."""

    items: List[WalkInServiceSchema]
    total: int
    limit: int
    offset: int


class DailyReportSchema(BaseModel):
    """Daily walk-in report response."""

    report_date: date
    total_services: int
    completed_services: int
    cancelled_services: int
    in_progress_services: int
    total_revenue: Decimal
    total_costs: Decimal
    total_profit: Decimal
    total_discounts: Decimal
    avg_service_time_minutes: int

    class Config:
        from_attributes = True


# ============================================================================
# Error Response Schema
# ============================================================================


class ErrorResponseSchema(BaseModel):
    """Error response."""

    detail: str
    error_code: Optional[str] = None
