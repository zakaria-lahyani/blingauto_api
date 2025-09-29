"""
Wash facility API schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Set
from uuid import UUID

from pydantic import BaseModel, Field, validator


# ============= REQUEST SCHEMAS =============

class CreateWashBayRequest(BaseModel):
    """Request schema for creating a wash bay"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the wash bay")
    bay_number: int = Field(..., ge=1, description="Bay number (must be unique)")
    equipment_types: Optional[Set[str]] = Field(None, description="Set of equipment types available")
    max_vehicle_size: str = Field("standard", description="Maximum vehicle size (compact, standard, large, oversized)")
    has_covered_area: bool = Field(True, description="Whether the bay has covered area")
    has_power_supply: bool = Field(True, description="Whether the bay has power supply")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @validator('max_vehicle_size')
    def validate_vehicle_size(cls, v):
        valid_sizes = ["compact", "standard", "large", "oversized"]
        if v not in valid_sizes:
            raise ValueError(f"Vehicle size must be one of: {valid_sizes}")
        return v


class UpdateWashBayRequest(BaseModel):
    """Request schema for updating a wash bay"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    equipment_types: Optional[Set[str]] = None
    max_vehicle_size: Optional[str] = None
    has_covered_area: Optional[bool] = None
    has_power_supply: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    
    @validator('max_vehicle_size')
    def validate_vehicle_size(cls, v):
        if v is not None:
            valid_sizes = ["compact", "standard", "large", "oversized"]
            if v not in valid_sizes:
                raise ValueError(f"Vehicle size must be one of: {valid_sizes}")
        return v


class CreateMobileTeamRequest(BaseModel):
    """Request schema for creating a mobile wash team"""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the mobile team")
    team_size: int = Field(..., ge=1, le=10, description="Number of team members")
    equipment_types: Optional[Set[str]] = Field(None, description="Set of equipment types available")
    service_radius_km: float = Field(50.0, ge=1, le=200, description="Service radius in kilometers")
    max_vehicles_per_day: int = Field(8, ge=1, le=20, description="Maximum vehicles per day")
    hourly_rate: Optional[float] = Field(None, ge=0, description="Hourly rate in dollars")
    base_location: Optional[Dict[str, float]] = Field(None, description="Base location coordinates")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @validator('base_location')
    def validate_base_location(cls, v):
        if v is not None:
            if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
                raise ValueError("Base location must contain 'lat' and 'lng' keys")
            if not isinstance(v['lat'], (int, float)) or not isinstance(v['lng'], (int, float)):
                raise ValueError("Latitude and longitude must be numbers")
        return v


class UpdateMobileTeamRequest(BaseModel):
    """Request schema for updating a mobile wash team"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    team_size: Optional[int] = Field(None, ge=1, le=10)
    equipment_types: Optional[Set[str]] = None
    service_radius_km: Optional[float] = Field(None, ge=1, le=200)
    max_vehicles_per_day: Optional[int] = Field(None, ge=1, le=20)
    hourly_rate: Optional[float] = Field(None, ge=0)
    base_location: Optional[Dict[str, float]] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    
    @validator('base_location')
    def validate_base_location(cls, v):
        if v is not None:
            if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
                raise ValueError("Base location must contain 'lat' and 'lng' keys")
            if not isinstance(v['lat'], (int, float)) or not isinstance(v['lng'], (int, float)):
                raise ValueError("Latitude and longitude must be numbers")
        return v


class UpdateFacilityConfigRequest(BaseModel):
    """Request schema for updating facility configuration"""
    facility_name: str = Field(..., min_length=1, max_length=200, description="Name of the facility")
    operating_hours: Optional[Dict] = Field(None, description="Operating hours configuration")
    default_service_duration_minutes: int = Field(60, ge=15, le=480, description="Default service duration in minutes")
    buffer_between_services_minutes: int = Field(15, ge=0, le=60, description="Buffer time between services in minutes")
    max_advance_booking_days: int = Field(30, ge=1, le=365, description="Maximum days in advance for booking")


# ============= RESPONSE SCHEMAS =============

class WashBayResponse(BaseModel):
    """Response schema for wash bay"""
    id: UUID
    name: str
    bay_number: int
    is_active: bool
    equipment_types: List[str]
    max_vehicle_size: str
    has_covered_area: bool
    has_power_supply: bool
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MobileTeamResponse(BaseModel):
    """Response schema for mobile team"""
    id: UUID
    name: str
    team_size: int
    equipment_types: List[str]
    service_radius_km: float
    max_vehicles_per_day: int
    hourly_rate: Optional[float]
    is_active: bool
    base_location: Optional[Dict[str, float]]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FacilityConfigResponse(BaseModel):
    """Response schema for facility configuration"""
    id: UUID
    facility_name: str
    total_wash_bays: int
    total_mobile_teams: int
    operating_hours: Optional[Dict]
    default_service_duration_minutes: int
    buffer_between_services_minutes: int
    max_advance_booking_days: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CapacityInfo(BaseModel):
    """Capacity information for a specific wash type"""
    total_capacity: int
    allocated: int
    available: int


class CapacitySummaryResponse(BaseModel):
    """Response schema for capacity summary"""
    date: str
    stationary: CapacityInfo
    mobile: CapacityInfo


class FacilityOverviewResponse(BaseModel):
    """Response schema for facility overview"""
    total_wash_bays: int
    active_wash_bays: int
    total_mobile_teams: int
    active_mobile_teams: int
    facility_name: str
    max_advance_booking_days: int
    default_service_duration: int
    buffer_between_services: int


# ============= UTILITY SCHEMAS =============

class ResourceAvailabilityRequest(BaseModel):
    """Request schema for checking resource availability"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    wash_type: str = Field(..., description="Type of wash (stationary or mobile)")
    vehicle_size: str = Field("standard", description="Vehicle size requirement")
    required_equipment: Optional[Set[str]] = Field(None, description="Required equipment")
    customer_location: Optional[Dict[str, float]] = Field(None, description="Customer location for mobile wash")
    
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


class ResourceAvailabilityResponse(BaseModel):
    """Response schema for resource availability"""
    date: str
    wash_type: str
    available_resources: List[Dict]
    total_available: int
    recommended_resource: Optional[Dict] = None