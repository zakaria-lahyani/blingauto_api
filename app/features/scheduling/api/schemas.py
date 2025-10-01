"""
Scheduling API schemas for request/response validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from ..domain.entities import VehicleSize, ResourceType


class LocationSchema(BaseModel):
    """Schema for GPS location."""
    latitude: Decimal = Field(..., ge=-90, le=90, description="Latitude")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Longitude")


class AvailabilityCheckRequest(BaseModel):
    """Schema for availability check request."""
    requested_time: datetime = Field(..., description="Requested booking time")
    duration_minutes: int = Field(..., gt=0, le=240, description="Service duration in minutes")
    vehicle_size: VehicleSize = Field(..., description="Vehicle size")
    service_type: ResourceType = Field(..., description="Service type (wash_bay or mobile_team)")
    customer_location: Optional[LocationSchema] = Field(None, description="Customer location for mobile service")
    required_equipment: List[str] = Field(default_factory=list, description="Required equipment types")
    
    @validator('customer_location')
    def validate_mobile_location(cls, v, values):
        """Validate that mobile service has customer location."""
        service_type = values.get('service_type')
        if service_type == ResourceType.MOBILE_TEAM and not v:
            raise ValueError('Customer location is required for mobile service')
        return v


class AvailabilityCheckResponse(BaseModel):
    """Schema for availability check response."""
    available: bool = Field(..., description="Whether slot is available")
    resource_id: Optional[str] = Field(None, description="Available resource ID")
    resource_type: Optional[str] = Field(None, description="Resource type")
    confirmed_time: Optional[datetime] = Field(None, description="Confirmed booking time")
    duration_minutes: Optional[int] = Field(None, description="Service duration")
    estimated_travel_time: Optional[int] = Field(None, description="Travel time for mobile service")
    reason: Optional[str] = Field(None, description="Reason if not available")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative options")


class GetSlotsRequest(BaseModel):
    """Schema for getting available slots request."""
    start_date: datetime = Field(..., description="Start date for search")
    end_date: datetime = Field(..., description="End date for search")
    service_type: ResourceType = Field(..., description="Service type")
    duration_minutes: int = Field(default=60, gt=0, le=240, description="Service duration")
    vehicle_size: VehicleSize = Field(default=VehicleSize.STANDARD, description="Vehicle size")
    customer_location: Optional[LocationSchema] = Field(None, description="Customer location")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that end date is after start date."""
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('End date must be after start date')
        
        # Limit search range to prevent excessive queries
        if start_date and (v - start_date).days > 30:
            raise ValueError('Search range cannot exceed 30 days')
        
        return v


class TimeSlotSchema(BaseModel):
    """Schema for time slot."""
    resource_id: str = Field(..., description="Resource ID")
    resource_type: str = Field(..., description="Resource type")
    start_time: datetime = Field(..., description="Slot start time")
    end_time: datetime = Field(..., description="Slot end time")
    duration_minutes: int = Field(..., description="Slot duration")
    capacity_utilization: float = Field(..., description="Resource capacity utilization %")


class GetSlotsResponse(BaseModel):
    """Schema for available slots response."""
    slots: List[TimeSlotSchema] = Field(..., description="Available time slots")
    total_count: int = Field(..., description="Total number of slots")
    search_criteria: Dict[str, Any] = Field(..., description="Search criteria used")


class WashBaySchema(BaseModel):
    """Schema for wash bay information."""
    id: str = Field(..., description="Wash bay ID")
    bay_number: str = Field(..., description="Bay number")
    max_vehicle_size: VehicleSize = Field(..., description="Maximum vehicle size")
    equipment_types: List[str] = Field(..., description="Available equipment")
    status: str = Field(..., description="Bay status")
    current_utilization: float = Field(..., description="Current utilization %")


class MobileTeamSchema(BaseModel):
    """Schema for mobile team information."""
    id: str = Field(..., description="Team ID")
    team_name: str = Field(..., description="Team name")
    base_location: LocationSchema = Field(..., description="Base location")
    service_radius_km: Decimal = Field(..., description="Service radius in km")
    daily_capacity: int = Field(..., description="Daily booking capacity")
    equipment_types: List[str] = Field(..., description="Available equipment")
    status: str = Field(..., description="Team status")
    current_utilization: float = Field(..., description="Current utilization %")


class ResourceListResponse(BaseModel):
    """Schema for resource list response."""
    wash_bays: List[WashBaySchema] = Field(default_factory=list, description="Available wash bays")
    mobile_teams: List[MobileTeamSchema] = Field(default_factory=list, description="Available mobile teams")
    total_wash_bays: int = Field(..., description="Total wash bays")
    total_mobile_teams: int = Field(..., description="Total mobile teams")


class BookingSlotRequest(BaseModel):
    """Schema for booking a time slot."""
    resource_id: str = Field(..., description="Resource ID to book")
    start_time: datetime = Field(..., description="Booking start time")
    duration_minutes: int = Field(..., gt=0, le=240, description="Service duration")
    booking_id: str = Field(..., description="Booking ID")
    customer_id: str = Field(..., description="Customer ID")


class BookingSlotResponse(BaseModel):
    """Schema for booking slot response."""
    success: bool = Field(..., description="Whether booking was successful")
    slot_id: Optional[str] = Field(None, description="Created slot ID")
    confirmed_time: Optional[datetime] = Field(None, description="Confirmed booking time")
    resource_id: Optional[str] = Field(None, description="Booked resource ID")
    message: str = Field(..., description="Success or error message")