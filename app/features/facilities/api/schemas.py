"""
Pydantic schemas for facilities API.

Request and response models for HTTP layer.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, validator

from ..domain.entities import VehicleSize, ResourceStatus


# Common schemas
class LocationSchema(BaseModel):
    """Location coordinates schema."""
    latitude: Decimal = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Longitude coordinate")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": "40.7128",
                "longitude": "-74.0060"
            }
        }


# Wash Bay schemas
class CreateWashBaySchema(BaseModel):
    """Request schema for creating a wash bay."""
    bay_number: str = Field(..., min_length=1, max_length=50, description="Unique bay number")
    max_vehicle_size: VehicleSize = Field(..., description="Maximum vehicle size capacity")
    equipment_types: List[str] = Field(default_factory=list, description="Available equipment types")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Bay latitude")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Bay longitude")

    @validator('equipment_types')
    def validate_equipment_types(cls, v):
        """Validate equipment types list."""
        if v is None:
            return []
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "bay_number": "Bay 1",
                "max_vehicle_size": "large",
                "equipment_types": ["pressure_washer", "foam_cannon", "dryer", "wax_applicator"],
                "latitude": "40.7128",
                "longitude": "-74.0060"
            }
        }


class UpdateWashBaySchema(BaseModel):
    """Request schema for updating a wash bay."""
    bay_number: Optional[str] = Field(None, min_length=1, max_length=50)
    max_vehicle_size: Optional[VehicleSize] = None
    equipment_types: Optional[List[str]] = None
    status: Optional[ResourceStatus] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "maintenance",
                "equipment_types": ["pressure_washer", "foam_cannon", "dryer"]
            }
        }


class WashBaySchema(BaseModel):
    """Response schema for wash bay."""
    id: str
    bay_number: str
    max_vehicle_size: str
    equipment_types: List[str]
    status: str
    location: Optional[LocationSchema]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid-123",
                "bay_number": "Bay 1",
                "max_vehicle_size": "large",
                "equipment_types": ["pressure_washer", "foam_cannon", "dryer"],
                "status": "active",
                "location": {
                    "latitude": "40.7128",
                    "longitude": "-74.0060"
                },
                "created_at": "2025-10-01T10:00:00Z",
                "updated_at": "2025-10-01T10:00:00Z"
            }
        }


class ListWashBaysSchema(BaseModel):
    """Response schema for listing wash bays."""
    wash_bays: List[WashBaySchema]
    total_count: int
    active_count: int
    inactive_count: int
    maintenance_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "wash_bays": [],
                "total_count": 5,
                "active_count": 3,
                "inactive_count": 1,
                "maintenance_count": 1
            }
        }


class DeleteWashBaySchema(BaseModel):
    """Response schema for wash bay deletion."""
    id: str
    bay_number: str
    deleted: bool
    message: str


# Mobile Team schemas
class CreateMobileTeamSchema(BaseModel):
    """Request schema for creating a mobile team."""
    team_name: str = Field(..., min_length=1, max_length=100, description="Unique team name")
    base_latitude: Decimal = Field(..., ge=-90, le=90, description="Base location latitude")
    base_longitude: Decimal = Field(..., ge=-180, le=180, description="Base location longitude")
    service_radius_km: Decimal = Field(Decimal('50'), gt=0, description="Service radius in kilometers")
    daily_capacity: int = Field(8, gt=0, description="Maximum vehicles per day")
    equipment_types: List[str] = Field(default_factory=list, description="Portable equipment types")

    @validator('equipment_types')
    def validate_equipment_types(cls, v):
        """Validate equipment types list."""
        if v is None:
            return []
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "team_name": "Mobile Team Alpha",
                "base_latitude": "40.7128",
                "base_longitude": "-74.0060",
                "service_radius_km": "50",
                "daily_capacity": 8,
                "equipment_types": ["portable_washer", "vacuum", "detailing_kit", "water_tank"]
            }
        }


class UpdateMobileTeamSchema(BaseModel):
    """Request schema for updating a mobile team."""
    team_name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    base_longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    service_radius_km: Optional[Decimal] = Field(None, gt=0)
    daily_capacity: Optional[int] = Field(None, gt=0)
    equipment_types: Optional[List[str]] = None
    status: Optional[ResourceStatus] = None

    class Config:
        json_schema_extra = {
            "example": {
                "service_radius_km": "60",
                "daily_capacity": 10,
                "status": "active"
            }
        }


class MobileTeamSchema(BaseModel):
    """Response schema for mobile team."""
    id: str
    team_name: str
    base_location: LocationSchema
    service_radius_km: str
    daily_capacity: int
    equipment_types: List[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "uuid-456",
                "team_name": "Mobile Team Alpha",
                "base_location": {
                    "latitude": "40.7128",
                    "longitude": "-74.0060"
                },
                "service_radius_km": "50",
                "daily_capacity": 8,
                "equipment_types": ["portable_washer", "vacuum", "detailing_kit"],
                "status": "active",
                "created_at": "2025-10-01T10:00:00Z",
                "updated_at": "2025-10-01T10:00:00Z"
            }
        }


class ListMobileTeamsSchema(BaseModel):
    """Response schema for listing mobile teams."""
    mobile_teams: List[MobileTeamSchema]
    total_count: int
    active_count: int
    inactive_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "mobile_teams": [],
                "total_count": 3,
                "active_count": 2,
                "inactive_count": 1
            }
        }


class DeleteMobileTeamSchema(BaseModel):
    """Response schema for mobile team deletion."""
    id: str
    team_name: str
    deleted: bool
    message: str
