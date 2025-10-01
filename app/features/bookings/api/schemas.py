from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class BookingServiceSchema(BaseModel):
    """Schema for booking service details."""
    service_id: str = Field(..., description="Service ID")
    name: str = Field(..., description="Service name")
    price: float = Field(..., ge=0, description="Service price")
    duration_minutes: int = Field(..., ge=1, description="Service duration in minutes")


class CreateBookingSchema(BaseModel):
    """Schema for creating a new booking."""
    customer_id: str = Field(..., description="Customer ID")
    vehicle_id: str = Field(..., description="Vehicle ID")
    service_ids: List[str] = Field(..., min_items=1, max_items=10, description="List of service IDs")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    booking_type: str = Field(..., description="Type of booking (scheduled, walk_in)")
    notes: Optional[str] = Field("", max_length=500, description="Additional notes")
    phone_number: Optional[str] = Field("", max_length=20, description="Contact phone number")
    
    @validator('scheduled_at')
    def validate_future_date(cls, v):
        """Ensure scheduled date is in the future."""
        if v <= datetime.now():
            raise ValueError('Scheduled time must be in the future')
        return v
    
    @validator('booking_type')
    def validate_booking_type(cls, v):
        """Validate booking type."""
        allowed_types = ['scheduled', 'walk_in']
        if v.lower() not in allowed_types:
            raise ValueError(f'Booking type must be one of: {", ".join(allowed_types)}')
        return v.upper()


class UpdateBookingSchema(BaseModel):
    """Schema for updating an existing booking."""
    scheduled_at: Optional[datetime] = Field(None, description="New scheduled date and time")
    service_ids: Optional[List[str]] = Field(None, min_items=1, max_items=10, description="Updated service IDs")
    notes: Optional[str] = Field(None, max_length=500, description="Updated notes")
    phone_number: Optional[str] = Field(None, max_length=20, description="Updated phone number")
    
    @validator('scheduled_at')
    def validate_future_date(cls, v):
        """Ensure scheduled date is in the future."""
        if v and v <= datetime.now():
            raise ValueError('Scheduled time must be in the future')
        return v


class CancelBookingSchema(BaseModel):
    """Schema for cancelling a booking."""
    reason: Optional[str] = Field("cancelled_by_customer", max_length=200, description="Cancellation reason")


class BookingResponseSchema(BaseModel):
    """Schema for booking response."""
    id: str = Field(..., description="Booking ID")
    customer_id: str = Field(..., description="Customer ID")
    vehicle_id: str = Field(..., description="Vehicle ID")
    status: str = Field(..., description="Booking status")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    booking_type: str = Field(..., description="Booking type")
    services: List[BookingServiceSchema] = Field(..., description="List of services")
    total_price: float = Field(..., ge=0, description="Total price")
    estimated_duration: int = Field(..., ge=1, description="Estimated duration in minutes")
    notes: str = Field(..., description="Additional notes")
    phone_number: str = Field(..., description="Contact phone number")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Resource allocation fields
    wash_bay_id: Optional[str] = Field(None, description="Assigned wash bay ID (for stationary bookings)")
    mobile_team_id: Optional[str] = Field(None, description="Assigned mobile team ID (for mobile bookings)")

    # Optional cancellation fields
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    cancelled_by: Optional[str] = Field(None, description="Who cancelled the booking")
    cancellation_reason: Optional[str] = Field(None, description="Cancellation reason")

    class Config:
        from_attributes = True


class BookingSummarySchema(BaseModel):
    """Schema for booking summary in lists."""
    id: str = Field(..., description="Booking ID")
    customer_id: str = Field(..., description="Customer ID")
    vehicle_id: str = Field(..., description="Vehicle ID")
    status: str = Field(..., description="Booking status")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    total_price: float = Field(..., ge=0, description="Total price")
    estimated_duration: int = Field(..., ge=1, description="Estimated duration in minutes")
    services_count: int = Field(..., ge=1, description="Number of services")
    booking_type: str = Field(..., description="Booking type")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class BookingListResponseSchema(BaseModel):
    """Schema for paginated booking list response."""
    bookings: List[BookingSummarySchema] = Field(..., description="List of bookings")
    total_count: int = Field(..., ge=0, description="Total number of bookings")
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    
    class Config:
        from_attributes = True


class CreateBookingResponseSchema(BaseModel):
    """Schema for create booking response."""
    booking_id: str = Field(..., description="Created booking ID")
    status: str = Field(..., description="Booking status")
    total_price: float = Field(..., ge=0, description="Total price")
    estimated_duration: int = Field(..., ge=1, description="Estimated duration in minutes")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    services: List[BookingServiceSchema] = Field(..., description="List of services")
    wash_bay_id: Optional[str] = Field(None, description="Assigned wash bay ID (for stationary bookings)")
    mobile_team_id: Optional[str] = Field(None, description="Assigned mobile team ID (for mobile bookings)")

    class Config:
        from_attributes = True


class CancelBookingResponseSchema(BaseModel):
    """Schema for cancel booking response."""
    booking_id: str = Field(..., description="Cancelled booking ID")
    status: str = Field(..., description="New booking status")
    refund_amount: Optional[float] = Field(None, ge=0, description="Refund amount if applicable")
    refund_status: str = Field(..., description="Refund processing status")
    
    class Config:
        from_attributes = True


class UpdateBookingResponseSchema(BaseModel):
    """Schema for update booking response."""
    booking_id: str = Field(..., description="Updated booking ID")
    status: str = Field(..., description="Booking status")
    total_price: float = Field(..., ge=0, description="Total price")
    estimated_duration: int = Field(..., ge=1, description="Estimated duration in minutes")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    services: List[BookingServiceSchema] = Field(..., description="List of services")
    changes_made: List[str] = Field(..., description="List of changes made")

    class Config:
        from_attributes = True


# ============================================================================
# NEW SCHEMAS - State Transition & Service Management
# ============================================================================

class ConfirmBookingSchema(BaseModel):
    """Schema for confirming a booking."""
    notes: Optional[str] = Field(None, max_length=500, description="Optional confirmation notes")


class ConfirmBookingResponseSchema(BaseModel):
    """Schema for confirm booking response."""
    booking_id: str = Field(..., description="Confirmed booking ID")
    status: str = Field(..., description="New booking status (confirmed)")
    confirmed_at: Optional[str] = Field(None, description="Confirmation timestamp")
    confirmed_by: str = Field(..., description="Staff member who confirmed")

    class Config:
        from_attributes = True


class StartBookingSchema(BaseModel):
    """Schema for starting a booking (no additional fields needed)."""
    pass


class StartBookingResponseSchema(BaseModel):
    """Schema for start booking response."""
    booking_id: str = Field(..., description="Started booking ID")
    status: str = Field(..., description="New booking status (in_progress)")
    actual_start_time: Optional[str] = Field(None, description="Actual start timestamp")
    started_by: str = Field(..., description="Staff member who started service")

    class Config:
        from_attributes = True


class CompleteBookingSchema(BaseModel):
    """Schema for completing a booking."""
    actual_end_time: Optional[datetime] = Field(None, description="Actual end time (defaults to now)")


class CompleteBookingResponseSchema(BaseModel):
    """Schema for complete booking response."""
    booking_id: str = Field(..., description="Completed booking ID")
    status: str = Field(..., description="New booking status (completed)")
    actual_end_time: Optional[str] = Field(None, description="Actual end timestamp")
    actual_duration: int = Field(..., ge=0, description="Actual duration in minutes")
    overtime_fee: float = Field(..., ge=0, description="Overtime fee charged")
    final_price: float = Field(..., ge=0, description="Final price including overtime")
    completed_by: str = Field(..., description="Staff member who completed service")

    class Config:
        from_attributes = True


class RescheduleBookingSchema(BaseModel):
    """Schema for rescheduling a booking."""
    new_scheduled_at: datetime = Field(..., description="New scheduled date and time")
    reason: Optional[str] = Field("", max_length=200, description="Reason for rescheduling")

    @validator('new_scheduled_at')
    def validate_future_date(cls, v):
        """Ensure new scheduled date is in the future."""
        if v <= datetime.now():
            raise ValueError('New scheduled time must be in the future')
        return v


class RescheduleBookingResponseSchema(BaseModel):
    """Schema for reschedule booking response."""
    booking_id: str = Field(..., description="Rescheduled booking ID")
    status: str = Field(..., description="Booking status")
    old_scheduled_at: str = Field(..., description="Previous scheduled time")
    new_scheduled_at: str = Field(..., description="New scheduled time")
    rescheduled_by: str = Field(..., description="Who rescheduled the booking")

    class Config:
        from_attributes = True


class AddServicesSchema(BaseModel):
    """Schema for adding services to a booking."""
    service_ids: List[str] = Field(..., min_items=1, description="List of service IDs to add")


class AddServicesResponseSchema(BaseModel):
    """Schema for add services response."""
    booking_id: str = Field(..., description="Booking ID")
    status: str = Field(..., description="Booking status")
    added_services: List[BookingServiceSchema] = Field(..., description="Services that were added")
    new_total_price: float = Field(..., ge=0, description="New total price")
    new_estimated_duration: int = Field(..., ge=1, description="New estimated duration")
    total_services_count: int = Field(..., ge=1, description="Total number of services")

    class Config:
        from_attributes = True


class RemoveServiceResponseSchema(BaseModel):
    """Schema for remove service response."""
    booking_id: str = Field(..., description="Booking ID")
    status: str = Field(..., description="Booking status")
    removed_services: List[BookingServiceSchema] = Field(..., description="Services that were removed")
    new_total_price: float = Field(..., ge=0, description="New total price")
    new_estimated_duration: int = Field(..., ge=1, description="New estimated duration")
    total_services_count: int = Field(..., ge=1, description="Remaining number of services")

    class Config:
        from_attributes = True


class MarkNoShowSchema(BaseModel):
    """Schema for marking a booking as no-show."""
    reason: Optional[str] = Field("customer_did_not_show", max_length=200, description="No-show reason")


class MarkNoShowResponseSchema(BaseModel):
    """Schema for mark no-show response."""
    booking_id: str = Field(..., description="Booking ID")
    status: str = Field(..., description="New booking status (no_show)")
    scheduled_at: str = Field(..., description="Originally scheduled time")
    no_show_fee: float = Field(..., ge=0, description="No-show fee charged (100%)")
    marked_by: str = Field(..., description="Staff member who marked no-show")
    grace_period_end: str = Field(..., description="When grace period ended")

    class Config:
        from_attributes = True


class RateBookingSchema(BaseModel):
    """Schema for rating a booking."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    feedback: Optional[str] = Field(None, max_length=1000, description="Optional feedback")

    @validator('rating')
    def validate_rating_range(cls, v):
        """Ensure rating is between 1 and 5."""
        if not (1 <= v <= 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class RateBookingResponseSchema(BaseModel):
    """Schema for rate booking response."""
    booking_id: str = Field(..., description="Rated booking ID")
    status: str = Field(..., description="Booking status")
    rating: int = Field(..., ge=1, le=5, description="Rating given")
    feedback: Optional[str] = Field(None, description="Feedback provided")
    rated_at: str = Field(..., description="Rating timestamp")

    class Config:
        from_attributes = True