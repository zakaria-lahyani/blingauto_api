from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from .exceptions import ValidationError, BusinessRuleViolationError


@dataclass
class Vehicle:
    """Vehicle entity representing a customer's vehicle."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    color: str = ""
    license_plate: str = ""
    is_default: bool = False
    is_deleted: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        customer_id: str,
        make: str,
        model: str,
        year: int,
        color: str,
        license_plate: str,
        is_default: bool = False,
    ) -> "Vehicle":
        """Create a new vehicle with validation."""
        vehicle = cls(
            customer_id=customer_id,
            make=make,
            model=model,
            year=year,
            color=color,
            license_plate=license_plate,
            is_default=is_default,
        )
        
        vehicle._validate()
        return vehicle
    
    def _validate(self) -> None:
        """Validate vehicle data according to business rules."""
        if not self.customer_id or not self.customer_id.strip():
            raise ValidationError("Customer ID cannot be empty")
        
        # RG-VEH-001: Validation de la marque
        if not self.make or len(self.make.strip()) < 2:
            raise ValidationError("Vehicle make must be at least 2 characters")
        if len(self.make) > 50:
            raise ValidationError("Vehicle make cannot exceed 50 characters")
        
        # RG-VEH-002: Validation du modèle
        if not self.model or len(self.model.strip()) < 1:
            raise ValidationError("Vehicle model cannot be empty")
        if len(self.model) > 50:
            raise ValidationError("Vehicle model cannot exceed 50 characters")
        
        # RG-VEH-003: Validation de l'année
        current_year = datetime.now().year
        if self.year < 1900:
            raise ValidationError("Vehicle year cannot be before 1900")
        if self.year > current_year + 2:
            raise ValidationError(f"Vehicle year cannot be more than 2 years in the future (max: {current_year + 2})")
        
        # RG-VEH-004: Validation de la couleur
        if not self.color or len(self.color.strip()) < 2:
            raise ValidationError("Vehicle color must be at least 2 characters")
        if len(self.color) > 30:
            raise ValidationError("Vehicle color cannot exceed 30 characters")
        
        # RG-VEH-005: Validation de la plaque d'immatriculation
        if not self.license_plate or len(self.license_plate.strip()) < 2:
            raise ValidationError("License plate must be at least 2 characters")
        if len(self.license_plate) > 20:
            raise ValidationError("License plate cannot exceed 20 characters")
        
        # Normalize data
        self.make = self.make.strip().title()
        self.model = self.model.strip().title()
        self.color = self.color.strip().title()
        self.license_plate = self.license_plate.strip().upper()
    
    def update_details(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        color: Optional[str] = None,
        license_plate: Optional[str] = None,
    ) -> None:
        """Update vehicle details with validation."""
        if self.is_deleted:
            raise BusinessRuleViolationError("Cannot update deleted vehicle")
        
        # Update fields if provided
        if make is not None:
            self.make = make
        if model is not None:
            self.model = model
        if year is not None:
            self.year = year
        if color is not None:
            self.color = color
        if license_plate is not None:
            self.license_plate = license_plate
        
        # Validate updated data
        self._validate()
        self.updated_at = datetime.utcnow()
    
    def set_as_default(self) -> None:
        """Set this vehicle as the default vehicle."""
        if self.is_deleted:
            raise BusinessRuleViolationError("Cannot set deleted vehicle as default")
        
        self.is_default = True
        self.updated_at = datetime.utcnow()
    
    def unset_as_default(self) -> None:
        """Remove default status from this vehicle."""
        self.is_default = False
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the vehicle (RG-VEH-007)."""
        if self.is_default:
            raise BusinessRuleViolationError(
                "Cannot delete default vehicle. Please set another vehicle as default first."
            )
        
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted vehicle."""
        if not self.is_deleted:
            raise BusinessRuleViolationError("Vehicle is not deleted")
        
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.utcnow()
    
    @property
    def display_name(self) -> str:
        """Get a human-readable display name for the vehicle."""
        return f"{self.year} {self.make} {self.model}"
    
    @property
    def is_active(self) -> bool:
        """Check if vehicle is active (not deleted)."""
        return not self.is_deleted
    
    def __eq__(self, other) -> bool:
        """Compare vehicles by ID."""
        if not isinstance(other, Vehicle):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash vehicle by ID."""
        return hash(self.id)
    
    def __str__(self) -> str:
        """String representation of vehicle."""
        status = "DEFAULT" if self.is_default else "ACTIVE"
        if self.is_deleted:
            status = "DELETED"
        return f"Vehicle({self.display_name}, {self.license_plate}, {status})"