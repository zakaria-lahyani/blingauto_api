"""
Service domain entities
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from .enums import ServiceStatus, CategoryStatus
from src.shared.utils.timestamp import utc_now


class ServiceCategory:
    """Service Category entity"""
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        status: CategoryStatus = CategoryStatus.ACTIVE,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Validate business rules
        self._validate_name(name)
        
        self.id = id or uuid4()
        self.name = name.strip() if name else name
        self.description = description
        self.status = status
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
    
    def _validate_name(self, name: str) -> None:
        """Validate category name"""
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")
        if len(name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")
    
    def update_name(self, name: str) -> None:
        """Update category name"""
        self._validate_name(name)
        self.name = name.strip()
        self.updated_at = utc_now()
    
    def update_description(self, description: Optional[str]) -> None:
        """Update category description"""
        self.description = description
        self.updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate the category"""
        self.status = CategoryStatus.ACTIVE
        self.updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate the category"""
        self.status = CategoryStatus.INACTIVE
        self.updated_at = utc_now()
    
    def update_details(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Update category details"""
        if name is not None:
            self._validate_name(name)
            self.name = name.strip()
        if description is not None:
            self.description = description
        self.updated_at = utc_now()
    
    @property
    def is_active(self) -> bool:
        """Check if category is active"""
        return self.status == CategoryStatus.ACTIVE
    
    def __str__(self) -> str:
        return f"ServiceCategory(id={self.id}, name='{self.name}', status={self.status.value})"


class Service:
    """Service entity"""
    
    def __init__(
        self,
        name: str,
        price: Decimal,
        duration: int,
        category_id: UUID,
        description: Optional[str] = None,
        point_description: Optional[List[str]] = None,
        status: ServiceStatus = ServiceStatus.ACTIVE,
        popular: bool = False,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # Validate business rules before setting
        self._validate_name(name)
        self._validate_price(price)
        self._validate_duration(duration)
        
        self.id = id or uuid4()
        self.name = name.strip() if name else name
        self.price = price
        self.duration = duration
        self.category_id = category_id
        self.description = description
        self.point_description = point_description or []
        self.status = status
        self.popular = popular
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
    
    def _validate_name(self, name: str) -> None:
        """Validate service name"""
        if not name or not name.strip():
            raise ValueError("Service name cannot be empty")
        if len(name) > 100:
            raise ValueError("Service name cannot exceed 100 characters")
    
    def _validate_price(self, price: Decimal) -> None:
        """Validate service price"""
        if price <= 0:
            raise ValueError("Service price must be positive")
    
    def _validate_duration(self, duration: int) -> None:
        """Validate service duration"""
        if duration <= 0:
            raise ValueError("Service duration must be positive")
    
    def update_name(self, name: str) -> None:
        """Update service name"""
        self._validate_name(name)
        self.name = name.strip()
        self.updated_at = utc_now()
    
    def update_price(self, price: Decimal) -> None:
        """Update service price"""
        self._validate_price(price)
        self.price = price
        self.updated_at = utc_now()
    
    def update_duration(self, duration: int) -> None:
        """Update service duration"""
        self._validate_duration(duration)
        self.duration = duration
        self.updated_at = utc_now()
    
    def update_description(self, description: Optional[str]) -> None:
        """Update service description"""
        self.description = description
        self.updated_at = utc_now()
    
    def update_point_description(self, point_description: List[str]) -> None:
        """Update service point description"""
        self.point_description = point_description
        self.updated_at = utc_now()
    
    def update_category(self, category_id: UUID) -> None:
        """Update service category"""
        self.category_id = category_id
        self.updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate the service"""
        self.status = ServiceStatus.ACTIVE
        self.updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate the service"""
        self.status = ServiceStatus.INACTIVE
        self.updated_at = utc_now()
    
    def mark_popular(self) -> None:
        """Mark service as popular"""
        self.popular = True
        self.updated_at = utc_now()
    
    def unmark_popular(self) -> None:
        """Unmark service as popular"""
        self.popular = False
        self.updated_at = utc_now()
    
    def soft_delete(self) -> None:
        """Soft delete the service"""
        self.status = ServiceStatus.DELETED
        self.updated_at = utc_now()
    
    def update_details(
        self,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        duration: Optional[int] = None,
        category_id: Optional[UUID] = None,
        description: Optional[str] = None,
        point_description: Optional[List[str]] = None
    ) -> None:
        """Update service details"""
        if name is not None:
            self._validate_name(name)
            self.name = name.strip()
        if price is not None:
            self._validate_price(price)
            self.price = price
        if duration is not None:
            self._validate_duration(duration)
            self.duration = duration
        if category_id is not None:
            self.category_id = category_id
        if description is not None:
            self.description = description
        if point_description is not None:
            self.point_description = point_description
        
        self.updated_at = utc_now()
    
    @property
    def is_active(self) -> bool:
        """Check if service is active"""
        return self.status == ServiceStatus.ACTIVE
    
    @property
    def is_deleted(self) -> bool:
        """Check if service is deleted"""
        return self.status == ServiceStatus.DELETED
    
    @property
    def is_popular(self) -> bool:
        """Check if service is popular"""
        return self.popular
    
    def __str__(self) -> str:
        return f"Service(id={self.id}, name='{self.name}', price={self.price}, duration={self.duration})"