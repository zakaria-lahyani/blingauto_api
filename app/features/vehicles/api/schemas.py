from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class CreateVehicleSchema(BaseModel):
    """Schema for creating a new vehicle."""
    make: str = Field(..., min_length=2, max_length=50, description="Vehicle make")
    model: str = Field(..., min_length=1, max_length=50, description="Vehicle model")
    year: int = Field(..., ge=1900, description="Vehicle year")
    color: str = Field(..., min_length=2, max_length=30, description="Vehicle color")
    license_plate: str = Field(..., min_length=2, max_length=20, description="License plate")
    is_default: bool = Field(False, description="Set as default vehicle")
    
    @validator('year')
    def validate_year_not_too_future(cls, v):
        """Validate year is not too far in the future."""
        current_year = datetime.now().year
        if v > current_year + 2:
            raise ValueError(f'Year cannot be more than 2 years in the future (max: {current_year + 2})')
        return v
    
    @validator('make', 'model', 'color')
    def validate_text_fields(cls, v):
        """Validate text fields are not empty after stripping."""
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip().title()
    
    @validator('license_plate')
    def validate_license_plate(cls, v):
        """Validate and normalize license plate."""
        if not v.strip():
            raise ValueError('License plate cannot be empty')
        return v.strip().upper()


class UpdateVehicleSchema(BaseModel):
    """Schema for updating an existing vehicle."""
    make: Optional[str] = Field(None, min_length=2, max_length=50, description="Vehicle make")
    model: Optional[str] = Field(None, min_length=1, max_length=50, description="Vehicle model")
    year: Optional[int] = Field(None, ge=1900, description="Vehicle year")
    color: Optional[str] = Field(None, min_length=2, max_length=30, description="Vehicle color")
    license_plate: Optional[str] = Field(None, min_length=2, max_length=20, description="License plate")
    
    @validator('year')
    def validate_year_not_too_future(cls, v):
        """Validate year is not too far in the future."""
        if v is not None:
            current_year = datetime.now().year
            if v > current_year + 2:
                raise ValueError(f'Year cannot be more than 2 years in the future (max: {current_year + 2})')
        return v
    
    @validator('make', 'model', 'color')
    def validate_text_fields(cls, v):
        """Validate text fields are not empty after stripping."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip().title() if v else v
    
    @validator('license_plate')
    def validate_license_plate(cls, v):
        """Validate and normalize license plate."""
        if v is not None:
            if not v.strip():
                raise ValueError('License plate cannot be empty')
            return v.strip().upper()
        return v


class SetDefaultVehicleSchema(BaseModel):
    """Schema for setting default vehicle."""
    # No additional fields needed - vehicle ID comes from path parameter
    pass


class VehicleResponseSchema(BaseModel):
    """Schema for vehicle response."""
    id: str = Field(..., description="Vehicle ID")
    customer_id: str = Field(..., description="Customer ID")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Vehicle year")
    color: str = Field(..., description="Vehicle color")
    license_plate: str = Field(..., description="License plate")
    is_default: bool = Field(..., description="Is default vehicle")
    is_deleted: bool = Field(..., description="Is deleted")
    display_name: str = Field(..., description="Display name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    
    @classmethod
    def from_entity(cls, vehicle):
        """Create schema from vehicle entity."""
        return cls(
            id=vehicle.id,
            customer_id=vehicle.customer_id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            license_plate=vehicle.license_plate,
            is_default=vehicle.is_default,
            is_deleted=vehicle.is_deleted,
            display_name=vehicle.display_name,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
            deleted_at=vehicle.deleted_at,
        )
    
    class Config:
        from_attributes = True


class VehicleSummarySchema(BaseModel):
    """Schema for vehicle summary in lists."""
    id: str = Field(..., description="Vehicle ID")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Vehicle year")
    color: str = Field(..., description="Vehicle color")
    license_plate: str = Field(..., description="License plate")
    is_default: bool = Field(..., description="Is default vehicle")
    is_deleted: bool = Field(..., description="Is deleted")
    display_name: str = Field(..., description="Display name")
    created_at: str = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class VehicleListResponseSchema(BaseModel):
    """Schema for paginated vehicle list response."""
    vehicles: List[VehicleSummarySchema] = Field(..., description="List of vehicles")
    total_count: int = Field(..., ge=0, description="Total number of vehicles")
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    default_vehicle_id: Optional[str] = Field(None, description="Default vehicle ID")
    
    class Config:
        from_attributes = True


class CreateVehicleResponseSchema(BaseModel):
    """Schema for create vehicle response."""
    vehicle_id: str = Field(..., description="Created vehicle ID")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Vehicle year")
    color: str = Field(..., description="Vehicle color")
    license_plate: str = Field(..., description="License plate")
    is_default: bool = Field(..., description="Is default vehicle")
    display_name: str = Field(..., description="Display name")
    
    class Config:
        from_attributes = True


class UpdateVehicleResponseSchema(BaseModel):
    """Schema for update vehicle response."""
    vehicle_id: str = Field(..., description="Updated vehicle ID")
    make: str = Field(..., description="Vehicle make")
    model: str = Field(..., description="Vehicle model")
    year: int = Field(..., description="Vehicle year")
    color: str = Field(..., description="Vehicle color")
    license_plate: str = Field(..., description="License plate")
    is_default: bool = Field(..., description="Is default vehicle")
    display_name: str = Field(..., description="Display name")
    changes_made: List[str] = Field(..., description="List of changes made")
    
    class Config:
        from_attributes = True


class DeleteVehicleResponseSchema(BaseModel):
    """Schema for delete vehicle response."""
    vehicle_id: str = Field(..., description="Deleted vehicle ID")
    deleted: bool = Field(..., description="Deletion status")
    message: str = Field(..., description="Deletion message")
    
    class Config:
        from_attributes = True


class SetDefaultVehicleResponseSchema(BaseModel):
    """Schema for set default vehicle response."""
    vehicle_id: str = Field(..., description="Vehicle ID")
    display_name: str = Field(..., description="Display name")
    is_default: bool = Field(..., description="Is default vehicle")
    previous_default_vehicle: Optional[str] = Field(None, description="Previous default vehicle")
    
    class Config:
        from_attributes = True


class VehicleSuggestionsSchema(BaseModel):
    """Schema for vehicle suggestions response."""
    makes: List[str] = Field(..., description="Vehicle make suggestions")
    models: List[str] = Field(..., description="Vehicle model suggestions")
    colors: List[str] = Field(..., description="Vehicle color suggestions")
    popular_makes: List[dict] = Field(..., description="Popular makes with counts")
    
    class Config:
        from_attributes = True