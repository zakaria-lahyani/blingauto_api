"""
Booking API schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field, validator
from pydantic.types import conint, condecimal

from src.features.bookings.domain.enums import BookingStatus, BookingType, QualityRating, BookingSortBy, CancellationPolicy


class BookingServiceSchema(BaseModel):
    """Schema for booking service"""
    id: UUID
    service_id: UUID
    service_name: str
    price: Decimal
    duration: int  # minutes
    
    class Config:
        from_attributes = True


class VehicleInfoSchema(BaseModel):
    """Vehicle information schema for booking responses"""
    id: UUID
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    is_default: bool
    display_name: str
    
    class Config:
        from_attributes = True


class CreateBookingRequest(BaseModel):
    """Request schema for creating a booking"""
    vehicle_id: UUID
    scheduled_at: datetime
    service_ids: List[UUID] = Field(..., min_items=1, max_items=10)
    booking_type: str = Field(..., description="Booking type: 'in_home' or 'mobile'")
    vehicle_size: str = Field("standard", description="Vehicle size: compact, standard, large, oversized")
    customer_location: Optional[Dict[str, float]] = Field(None, description="Customer location for mobile bookings")
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('service_ids')
    def validate_service_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate service IDs are not allowed')
        return v
    
    @validator('booking_type')
    def validate_booking_type(cls, v):
        valid_types = ["in_home", "mobile"]
        if v not in valid_types:
            raise ValueError(f"Booking type must be one of: {valid_types}")
        return v
    
    @validator('vehicle_size')
    def validate_vehicle_size(cls, v):
        valid_sizes = ["compact", "standard", "large", "oversized"]
        if v not in valid_sizes:
            raise ValueError(f"Vehicle size must be one of: {valid_sizes}")
        return v
    
    @validator('customer_location')
    def validate_customer_location(cls, v, values):
        booking_type = values.get('booking_type')
        if booking_type == 'mobile':
            if not v:
                raise ValueError("Customer location is required for mobile bookings")
            if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
                raise ValueError("Customer location must contain 'lat' and 'lng' keys")
            if not isinstance(v['lat'], (int, float)) or not isinstance(v['lng'], (int, float)):
                raise ValueError("Latitude and longitude must be numbers")
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class CreateBookingWithCapacityRequest(BaseModel):
    """Request schema for creating a booking with wash facility capacity management"""
    vehicle_id: UUID
    scheduled_at: datetime
    service_ids: List[UUID] = Field(..., min_items=1, max_items=10)
    notes: Optional[str] = Field(None, max_length=1000)
    wash_type: str = Field(..., description="Type of wash: 'stationary' or 'mobile'")
    vehicle_size: str = Field("standard", description="Vehicle size: compact, standard, large, oversized")
    customer_location: Optional[Dict[str, float]] = Field(None, description="Customer location for mobile wash")
    
    @validator('service_ids')
    def validate_service_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('Duplicate service IDs are not allowed')
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v
    
    @validator('wash_type')
    def validate_wash_type(cls, v):
        valid_types = ["stationary", "mobile"]
        if v not in valid_types:
            raise ValueError(f"Wash type must be one of: {valid_types}")
        return v
    
    @validator('vehicle_size')
    def validate_vehicle_size(cls, v):
        valid_sizes = ["compact", "standard", "large", "oversized"]
        if v not in valid_sizes:
            raise ValueError(f"Vehicle size must be one of: {valid_sizes}")
        return v
    
    @validator('customer_location')
    def validate_customer_location(cls, v):
        if v is not None:
            if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
                raise ValueError("Customer location must contain 'lat' and 'lng' keys")
            if not isinstance(v['lat'], (int, float)) or not isinstance(v['lng'], (int, float)):
                raise ValueError("Latitude and longitude must be numbers")
        return v


class UpdateBookingRequest(BaseModel):
    """Request schema for updating a booking"""
    notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v


class RescheduleBookingRequest(BaseModel):
    """Request schema for rescheduling a booking"""
    new_scheduled_at: datetime
    
    @validator('new_scheduled_at')
    def validate_new_scheduled_at(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('New scheduled time must be in the future')
        return v


class CancelBookingRequest(BaseModel):
    """Request schema for cancelling a booking"""
    reason: Optional[str] = Field(None, max_length=500)
    
    @validator('reason')
    def validate_reason(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v


class QualityRatingRequest(BaseModel):
    """Request schema for rating service quality"""
    rating: conint(ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)
    
    @validator('feedback')
    def validate_feedback(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v


class AddServiceRequest(BaseModel):
    """Request schema for adding a service to booking"""
    service_id: UUID


class BookingResponse(BaseModel):
    """Response schema for booking"""
    id: UUID
    customer_id: UUID
    vehicle_id: UUID
    vehicle: Optional[VehicleInfoSchema]
    scheduled_at: datetime
    booking_type: str
    vehicle_size: str
    customer_location: Optional[Dict[str, float]]
    status: BookingStatus
    notes: Optional[str]
    total_price: Decimal
    total_duration: int
    cancellation_fee: Decimal
    quality_rating: Optional[int]
    quality_feedback: Optional[str]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    services: List[BookingServiceSchema]
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    can_be_modified: bool
    can_be_cancelled: bool
    can_be_rescheduled: bool
    can_be_rated: bool
    is_overdue: bool
    expected_end_time: datetime
    
    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Response schema for booking list"""
    bookings: List[BookingResponse]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool


class CancellationInfoResponse(BaseModel):
    """Response schema for cancellation information"""
    policy: CancellationPolicy
    fee: Decimal
    notice_hours: float
    total_price: Decimal
    can_cancel: bool
    message: str


class BookingAnalyticsResponse(BaseModel):
    """Response schema for booking analytics"""
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    no_show_bookings: int
    completion_rate: float
    cancellation_rate: float
    no_show_rate: float
    total_revenue: Decimal
    total_fees: Decimal
    average_rating: Optional[float]
    rated_bookings_count: int
    date_range: List[datetime]  # [start_date, end_date]


class BookingEventResponse(BaseModel):
    """Response schema for booking events"""
    id: UUID
    booking_id: UUID
    event_type: str
    event_data: Optional[str]
    customer_id: UUID
    occurred_at: datetime
    processed: bool
    
    class Config:
        from_attributes = True


class BookingFilters(BaseModel):
    """Query parameters for filtering bookings"""
    customer_id: Optional[UUID] = None
    vehicle_id: Optional[UUID] = None
    status: Optional[BookingStatus] = None
    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = Field(None, max_length=100)
    sort_by: BookingSortBy = BookingSortBy.CREATED_AT
    sort_desc: bool = True
    page: conint(ge=1) = 1
    size: conint(ge=1, le=100) = 20
    
    @validator('search')
    def validate_search(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('End date must be after start date')
        return v


class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    details: Optional[str] = None
    success: bool = False