"""
Vehicle domain entities
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from .enums import VehicleStatus
from src.shared.utils.timestamp import utc_now


class Vehicle:
    """Vehicle entity with essential vehicle information"""
    
    def __init__(
        self,
        user_id: UUID,
        make: str,
        model: str,
        year: int,
        color: str,
        license_plate: str,
        is_default: bool = False,
        id: Optional[UUID] = None,
        status: VehicleStatus = VehicleStatus.ACTIVE,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Validate business rules
        self._validate_vehicle_data(make, model, year, color, license_plate)
        
        self.id = id or uuid4()
        self.user_id = user_id
        self.make = make.strip().title()
        self.model = model.strip().title()
        self.year = year
        self.color = color.strip().title()
        self.license_plate = license_plate.strip().upper()
        self.is_default = is_default
        self.status = status
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
    
    def _validate_vehicle_data(self, make: str, model: str, year: int, color: str, license_plate: str) -> None:
        """Validate vehicle data business rules"""
        self._validate_make(make)
        self._validate_model(model)
        self._validate_year(year)
        self._validate_color(color)
        self._validate_license_plate(license_plate)
    
    def _validate_make(self, make: str) -> None:
        """Validate vehicle make"""
        if not make or len(make.strip()) < 2:
            raise ValueError("Vehicle make must be at least 2 characters")
        if len(make.strip()) > 50:
            raise ValueError("Vehicle make cannot exceed 50 characters")
    
    def _validate_model(self, model: str) -> None:
        """Validate vehicle model"""
        if not model or len(model.strip()) < 1:
            raise ValueError("Vehicle model is required")
        if len(model.strip()) > 50:
            raise ValueError("Vehicle model cannot exceed 50 characters")
    
    def _validate_year(self, year: int) -> None:
        """Validate vehicle year"""
        current_year = utc_now().year
        if year < 1900:
            raise ValueError("Vehicle year cannot be before 1900")
        if year > current_year + 2:
            raise ValueError(f"Vehicle year cannot be more than 2 years in the future")
    
    def _validate_color(self, color: str) -> None:
        """Validate vehicle color"""
        if not color or len(color.strip()) < 2:
            raise ValueError("Vehicle color must be at least 2 characters")
        if len(color.strip()) > 30:
            raise ValueError("Vehicle color cannot exceed 30 characters")
    
    def _validate_license_plate(self, license_plate: str) -> None:
        """Validate license plate"""
        if not license_plate or len(license_plate.strip()) < 2:
            raise ValueError("License plate must be at least 2 characters")
        if len(license_plate.strip()) > 20:
            raise ValueError("License plate cannot exceed 20 characters")
    
    def update_make(self, make: str) -> None:
        """Update vehicle make"""
        self._validate_make(make)
        self.make = make.strip().title()
        self.updated_at = utc_now()
    
    def update_model(self, model: str) -> None:
        """Update vehicle model"""
        self._validate_model(model)
        self.model = model.strip().title()
        self.updated_at = utc_now()
    
    def update_year(self, year: int) -> None:
        """Update vehicle year"""
        self._validate_year(year)
        self.year = year
        self.updated_at = utc_now()
    
    def update_color(self, color: str) -> None:
        """Update vehicle color"""
        self._validate_color(color)
        self.color = color.strip().title()
        self.updated_at = utc_now()
    
    def update_license_plate(self, license_plate: str) -> None:
        """Update vehicle license plate"""
        self._validate_license_plate(license_plate)
        self.license_plate = license_plate.strip().upper()
        self.updated_at = utc_now()
    
    def update_details(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        color: Optional[str] = None,
        license_plate: Optional[str] = None
    ) -> None:
        """Update vehicle details"""
        # Validate each field individually
        if make is not None:
            self._validate_make(make)
            self.make = make.strip().title()
        if model is not None:
            self._validate_model(model)
            self.model = model.strip().title()
        if year is not None:
            self._validate_year(year)
            self.year = year
        if color is not None:
            self._validate_color(color)
            self.color = color.strip().title()
        if license_plate is not None:
            self._validate_license_plate(license_plate)
            self.license_plate = license_plate.strip().upper()
        
        self.updated_at = utc_now()
    
    def set_as_default(self) -> None:
        """Set this vehicle as the default for the owner"""
        self.is_default = True
        self.updated_at = utc_now()
    
    def unset_as_default(self) -> None:
        """Unset this vehicle as default"""
        self.is_default = False
        self.updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate the vehicle (soft delete)"""
        if self.status == VehicleStatus.DELETED:
            raise ValueError("Vehicle is already deleted")
        
        self.status = VehicleStatus.INACTIVE
        self.is_default = False  # Cannot be default if inactive
        self.updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate the vehicle"""
        if self.status == VehicleStatus.DELETED:
            raise ValueError("Cannot activate deleted vehicle")
        
        self.status = VehicleStatus.ACTIVE
        self.updated_at = utc_now()
    
    def delete(self) -> None:
        """Delete the vehicle (soft delete)"""
        self.status = VehicleStatus.DELETED
        self.is_default = False  # Cannot be default if deleted
        self.updated_at = utc_now()
    
    @property
    def is_active(self) -> bool:
        """Check if vehicle is active"""
        return self.status == VehicleStatus.ACTIVE
    
    @property
    def is_deleted(self) -> bool:
        """Check if vehicle is deleted"""
        return self.status == VehicleStatus.DELETED
    
    @property
    def display_name(self) -> str:
        """Get display name for the vehicle"""
        return f"{self.year} {self.make} {self.model}"
    
    @property
    def full_name(self) -> str:
        """Get full name of the vehicle"""
        return f"{self.year} {self.make} {self.model}"
    
    @property
    def age_years(self) -> int:
        """Get vehicle age in years"""
        return utc_now().year - self.year
    
    def __str__(self) -> str:
        return f"Vehicle(id={self.id}, user={self.user_id}, {self.display_name}, plate={self.license_plate})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Vehicle):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)