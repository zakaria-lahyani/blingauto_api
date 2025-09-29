"""
Vehicle API schemas
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from src.features.vehicles.domain.enums import VehicleStatus


class CreateVehicleRequest(BaseModel):
    """Request schema for creating a vehicle"""
    make: str = Field(..., min_length=2, max_length=50)
    model: str = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=1900, le=2030)
    license_plate: str = Field(..., min_length=2, max_length=20)
    color: str = Field(..., min_length=2, max_length=30)
    is_default: bool = False
    
    @validator('make', 'model', 'color')
    def validate_text_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @validator('license_plate')
    def validate_license_plate(cls, v):
        if not v or not v.strip():
            raise ValueError('License plate cannot be empty')
        return v.strip().upper()
    
    @validator('year')
    def validate_year(cls, v):
        current_year = datetime.now().year
        if v > current_year + 2:
            raise ValueError(f'Year cannot be more than 2 years in the future')
        return v


class UpdateVehicleRequest(BaseModel):
    """Request schema for updating a vehicle"""
    make: Optional[str] = Field(None, min_length=2, max_length=50)
    model: Optional[str] = Field(None, min_length=1, max_length=50)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    license_plate: Optional[str] = Field(None, min_length=2, max_length=20)
    color: Optional[str] = Field(None, min_length=2, max_length=30)
    
    @validator('make', 'model', 'color')
    def validate_text_fields(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Field cannot be empty')
            return v.strip()
        return v
    
    @validator('license_plate')
    def validate_license_plate(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('License plate cannot be empty')
            return v.strip().upper()
        return v
    
    @validator('year')
    def validate_year(cls, v):
        if v is not None:
            current_year = datetime.now().year
            if v > current_year + 2:
                raise ValueError(f'Year cannot be more than 2 years in the future')
        return v


class VehicleResponse(BaseModel):
    """Response schema for vehicle"""
    id: UUID
    user_id: UUID
    make: str
    model: str
    year: int
    license_plate: str
    color: str
    status: VehicleStatus
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    display_name: str
    
    class Config:
        from_attributes = True


class VehicleSummaryResponse(BaseModel):
    """Summary response schema for vehicle (for lists)"""
    id: UUID
    make: str
    model: str
    year: int
    license_plate: str
    color: str
    status: VehicleStatus
    is_default: bool
    display_name: str
    
    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    """Response schema for vehicle list"""
    vehicles: List[VehicleSummaryResponse]
    total: int
    default_vehicle_id: Optional[UUID]


class VehicleAnalyticsResponse(BaseModel):
    """Response schema for vehicle analytics"""
    total_vehicles: int
    active_vehicles: int
    inactive_vehicles: int
    deleted_vehicles: int
    default_vehicle_id: Optional[UUID]
    newest_vehicle_year: Optional[int]
    oldest_vehicle_year: Optional[int]


class VehicleFilters(BaseModel):
    """Query parameters for filtering vehicles"""
    status: Optional[VehicleStatus] = None
    search: Optional[str] = Field(None, max_length=100)
    include_inactive: bool = False
    
    @validator('search')
    def validate_search(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v.strip() if v else None


class SetDefaultVehicleRequest(BaseModel):
    """Request schema for setting default vehicle"""
    vehicle_id: UUID


class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    details: Optional[str] = None
    success: bool = False