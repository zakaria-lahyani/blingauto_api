from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum
import uuid

from .exceptions import ValidationError, BusinessRuleViolationError


class CategoryStatus(Enum):
    """Category status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ServiceStatus(Enum):
    """Service status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass
class Category:
    """Service category entity."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: CategoryStatus = CategoryStatus.ACTIVE
    display_order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        display_order: int = 0,
    ) -> "Category":
        """Create a new category with validation."""
        category = cls(
            name=name,
            description=description,
            display_order=display_order,
        )
        
        category._validate()
        return category
    
    def _validate(self) -> None:
        """Validate category data according to business rules."""
        
        # RG-SVC-001: Validation du nom de catégorie
        if not self.name or not self.name.strip():
            raise ValidationError("Category name cannot be empty")
        
        if len(self.name) > 100:
            raise ValidationError("Category name cannot exceed 100 characters")
        
        # Normalize name
        self.name = self.name.strip()
        
        # Validate description
        if self.description and len(self.description) > 500:
            raise ValidationError("Category description cannot exceed 500 characters")
        
        # Validate display order
        if self.display_order < 0:
            raise ValidationError("Display order must be non-negative")
    
    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> None:
        """Update category details with validation."""
        if self.status == CategoryStatus.INACTIVE:
            raise BusinessRuleViolationError("Cannot update inactive category")
        
        # Update fields if provided
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if display_order is not None:
            self.display_order = display_order
        
        # Validate updated data
        self._validate()
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the category."""
        if self.status == CategoryStatus.ACTIVE:
            raise BusinessRuleViolationError("Category is already active")
        
        self.status = CategoryStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the category (RG-SVC-002)."""
        if self.status == CategoryStatus.INACTIVE:
            raise BusinessRuleViolationError("Category is already inactive")
        
        self.status = CategoryStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if category is active."""
        return self.status == CategoryStatus.ACTIVE
    
    def __eq__(self, other) -> bool:
        """Compare categories by ID."""
        if not isinstance(other, Category):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash category by ID."""
        return hash(self.id)
    
    def __str__(self) -> str:
        """String representation of category."""
        return f"Category({self.name}, {self.status.value})"


@dataclass
class Service:
    """Service entity."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category_id: str = ""
    name: str = ""
    description: str = ""
    price: Decimal = field(default_factory=lambda: Decimal('0.00'))
    duration_minutes: int = 0
    status: ServiceStatus = ServiceStatus.ACTIVE
    is_popular: bool = False
    display_order: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(
        cls,
        category_id: str,
        name: str,
        description: str,
        price: Decimal,
        duration_minutes: int,
        is_popular: bool = False,
        display_order: int = 0,
    ) -> "Service":
        """Create a new service with validation."""
        service = cls(
            category_id=category_id,
            name=name,
            description=description,
            price=price,
            duration_minutes=duration_minutes,
            is_popular=is_popular,
            display_order=display_order,
        )
        
        service._validate()
        return service
    
    def _validate(self) -> None:
        """Validate service data according to business rules."""
        if not self.category_id or not self.category_id.strip():
            raise ValidationError("Service must belong to a category")
        
        # RG-SVC-003: Validation du nom de service
        if not self.name or not self.name.strip():
            raise ValidationError("Service name cannot be empty")
        
        if len(self.name) > 100:
            raise ValidationError("Service name cannot exceed 100 characters")
        
        # RG-SVC-004: Validation du prix
        if self.price <= 0:
            raise ValidationError("Service price must be positive")
        
        if self.price > Decimal('10000.00'):
            raise ValidationError("Service price cannot exceed 10,000.00")
        
        # RG-SVC-005: Validation de la durée
        if self.duration_minutes <= 0:
            raise ValidationError("Service duration must be positive")
        
        if self.duration_minutes > 480:  # 8 hours max
            raise ValidationError("Service duration cannot exceed 480 minutes (8 hours)")
        
        # Normalize name
        self.name = self.name.strip()
        
        # Validate description
        if self.description and len(self.description) > 1000:
            raise ValidationError("Service description cannot exceed 1000 characters")
        
        # Validate display order
        if self.display_order < 0:
            raise ValidationError("Display order must be non-negative")
    
    def update_details(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[Decimal] = None,
        duration_minutes: Optional[int] = None,
        display_order: Optional[int] = None,
    ) -> None:
        """Update service details with validation."""
        if self.status == ServiceStatus.ARCHIVED:
            raise BusinessRuleViolationError("Cannot update archived service")
        
        # Update fields if provided
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if price is not None:
            self.price = price
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
        if display_order is not None:
            self.display_order = display_order
        
        # Validate updated data
        self._validate()
        self.updated_at = datetime.utcnow()
    
    def update_pricing(self, new_price: Decimal) -> None:
        """Update service pricing with validation."""
        if self.status == ServiceStatus.ARCHIVED:
            raise BusinessRuleViolationError("Cannot update pricing for archived service")
        
        old_price = self.price
        self.price = new_price
        
        # Validate new price
        self._validate()
        self.updated_at = datetime.utcnow()
        
        # Could emit price change event here
    
    def set_popular(self, is_popular: bool) -> None:
        """Set service as popular or not (RG-SVC-006)."""
        if self.status != ServiceStatus.ACTIVE:
            raise BusinessRuleViolationError("Only active services can be marked as popular")
        
        self.is_popular = is_popular
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the service."""
        if self.status == ServiceStatus.ACTIVE:
            raise BusinessRuleViolationError("Service is already active")
        
        self.status = ServiceStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the service."""
        if self.status == ServiceStatus.INACTIVE:
            raise BusinessRuleViolationError("Service is already inactive")
        
        self.status = ServiceStatus.INACTIVE
        self.is_popular = False  # Remove popular status when deactivating
        self.updated_at = datetime.utcnow()
    
    def archive(self) -> None:
        """Archive the service (soft delete)."""
        if self.status == ServiceStatus.ARCHIVED:
            raise BusinessRuleViolationError("Service is already archived")
        
        self.status = ServiceStatus.ARCHIVED
        self.is_popular = False  # Remove popular status when archiving
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore archived service to inactive status."""
        if self.status != ServiceStatus.ARCHIVED:
            raise BusinessRuleViolationError("Can only restore archived services")
        
        self.status = ServiceStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if service is active."""
        return self.status == ServiceStatus.ACTIVE
    
    @property
    def is_available(self) -> bool:
        """Check if service is available for booking."""
        return self.status == ServiceStatus.ACTIVE
    
    @property
    def price_display(self) -> str:
        """Get formatted price for display."""
        return f"${self.price:.2f}"
    
    @property
    def duration_display(self) -> str:
        """Get formatted duration for display."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def calculate_price_for_quantity(self, quantity: int) -> Decimal:
        """Calculate total price for a given quantity."""
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        return self.price * quantity
    
    def __eq__(self, other) -> bool:
        """Compare services by ID."""
        if not isinstance(other, Service):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash service by ID."""
        return hash(self.id)
    
    def __str__(self) -> str:
        """String representation of service."""
        popular_indicator = " (Popular)" if self.is_popular else ""
        return f"Service({self.name}, {self.price_display}, {self.duration_display}{popular_indicator})"