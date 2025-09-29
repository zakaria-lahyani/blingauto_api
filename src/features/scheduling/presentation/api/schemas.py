"""
Scheduling API schemas
"""
from datetime import datetime, time
from typing import List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.features.scheduling.domain.enums import (
    DayOfWeek, ResourceType, ResourceStatus, ConflictType, SuggestionStrategy
)


class BusinessHoursSchema(BaseModel):
    """Business hours schema"""
    day_of_week: DayOfWeek
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_closed: bool = False
    break_periods: List[dict] = Field(default_factory=list)  # [{"start": "12:00", "end": "13:00"}]
    
    class Config:
        from_attributes = True


class BusinessHoursRequest(BaseModel):
    """Request to update business hours"""
    day_of_week: DayOfWeek
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_closed: bool = False
    break_periods: List[dict] = Field(default_factory=list)
    
    @validator('break_periods')
    def validate_break_periods(cls, v):
        for period in v:
            if 'start' not in period or 'end' not in period:
                raise ValueError('Break periods must have start and end times')
        return v


class ResourceSchema(BaseModel):
    """Resource schema"""
    id: UUID
    name: str
    resource_type: ResourceType
    capacity: int
    status: ResourceStatus
    skills: Set[str] = Field(default_factory=set)
    hourly_rate: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateResourceRequest(BaseModel):
    """Request to create a resource"""
    name: str = Field(..., min_length=2, max_length=100)
    resource_type: ResourceType
    capacity: int = Field(default=1, ge=1, le=10)
    skills: Set[str] = Field(default_factory=set)
    hourly_rate: Optional[float] = Field(None, ge=0)


class UpdateResourceRequest(BaseModel):
    """Request to update a resource"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[ResourceStatus] = None
    skills: Optional[Set[str]] = None
    hourly_rate: Optional[float] = Field(None, ge=0)


class TimeSlotSchema(BaseModel):
    """Time slot schema"""
    id: UUID
    start_time: datetime
    end_time: datetime
    resource_id: Optional[UUID] = None
    status: str
    booking_id: Optional[UUID] = None
    duration_minutes: int
    
    class Config:
        from_attributes = True


class AvailabilityRequest(BaseModel):
    """Request for checking availability"""
    start_date: datetime
    end_date: datetime
    duration_minutes: int = Field(..., ge=15, le=480)  # 15 minutes to 8 hours
    service_ids: List[UUID] = Field(..., min_items=1)
    preferred_resources: List[UUID] = Field(default_factory=list)
    exclude_times: List[dict] = Field(default_factory=list)  # [{"start": "2024-01-01T10:00", "end": "2024-01-01T12:00"}]
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('exclude_times')
    def validate_exclude_times(cls, v):
        for period in v:
            if 'start' not in period or 'end' not in period:
                raise ValueError('Exclude times must have start and end')
        return v


class SchedulingPreferencesRequest(BaseModel):
    """Customer scheduling preferences"""
    preferred_days: Set[DayOfWeek] = Field(default_factory=set)
    preferred_times: List[dict] = Field(default_factory=list)  # [{"start": "09:00", "end": "12:00"}]
    avoid_times: List[dict] = Field(default_factory=list)
    preferred_resources: List[UUID] = Field(default_factory=list)
    buffer_time: int = Field(default=15, ge=0, le=60)
    strategy: SuggestionStrategy = SuggestionStrategy.EARLIEST_AVAILABLE


class ConflictSchema(BaseModel):
    """Scheduling conflict schema"""
    conflict_type: ConflictType
    message: str
    requested_time: datetime
    conflicting_booking_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    suggested_alternatives: List[datetime] = Field(default_factory=list)


class AvailabilityResponse(BaseModel):
    """Response for availability check"""
    available_slots: List[TimeSlotSchema]
    conflicts: List[ConflictSchema]
    suggested_times: List[datetime]
    total_available_slots: int
    search_period: dict  # {"start": "2024-01-01T00:00", "end": "2024-01-07T23:59"}
    
    class Config:
        from_attributes = True


class ConflictCheckRequest(BaseModel):
    """Request to check for booking conflicts"""
    start_time: datetime
    duration_minutes: int = Field(..., ge=15, le=480)
    service_ids: List[UUID] = Field(..., min_items=1)
    exclude_booking_id: Optional[UUID] = None


class ConflictCheckResponse(BaseModel):
    """Response for conflict check"""
    has_conflicts: bool
    conflicts: List[ConflictSchema]
    is_bookable: bool
    suggested_alternatives: List[datetime] = Field(default_factory=list)


class TimeSuggestionRequest(BaseModel):
    """Request for time suggestions"""
    preferred_date: Optional[datetime] = None
    duration_minutes: int = Field(..., ge=15, le=480)
    service_ids: List[UUID] = Field(..., min_items=1)
    preferences: Optional[SchedulingPreferencesRequest] = None
    max_suggestions: int = Field(default=5, ge=1, le=10)


class TimeSuggestionResponse(BaseModel):
    """Response with suggested times"""
    suggestions: List[dict]  # [{"time": "2024-01-01T10:00", "resource_name": "Bay 1", "confidence": 0.9}]
    total_suggestions: int
    search_period: dict
    preferences_applied: bool


class BusinessConfigurationSchema(BaseModel):
    """Business configuration schema"""
    slot_duration_minutes: int
    buffer_between_bookings: int
    max_advance_booking_days: int
    min_advance_booking_hours: int
    allow_same_day_booking: bool
    timezone: str


class UpdateBusinessConfigurationRequest(BaseModel):
    """Request to update business configuration"""
    slot_duration_minutes: Optional[int] = Field(None, ge=15, le=120)
    buffer_between_bookings: Optional[int] = Field(None, ge=0, le=60)
    max_advance_booking_days: Optional[int] = Field(None, ge=1, le=365)
    min_advance_booking_hours: Optional[int] = Field(None, ge=0, le=72)
    allow_same_day_booking: Optional[bool] = None


class ResourceAvailabilityRequest(BaseModel):
    """Request to check resource availability"""
    resource_ids: List[UUID] = Field(..., min_items=1)
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ResourceAvailabilityResponse(BaseModel):
    """Response for resource availability"""
    resource_availability: List[dict]  # [{"resource_id": "uuid", "available_slots": [...], "busy_periods": [...]}]
    summary: dict  # {"total_resources": 3, "available_resources": 2, "total_slots": 100}


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None