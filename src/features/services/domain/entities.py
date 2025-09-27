"""
Service domain entities
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from .enums import ServiceStatus, CategoryStatus


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
        self.id = id or uuid4()
        self.name = name
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def update_name(self, name: str) -> None:
        """Update category name"""
        self.name = name
        self.updated_at = datetime.utcnow()
    
    def update_description(self, description: Optional[str]) -> None:
        """Update category description"""
        self.description = description
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the category"""
        self.status = CategoryStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the category"""
        self.status = CategoryStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
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
        self.id = id or uuid4()
        self.name = name
        self.price = price
        self.duration = duration
        self.category_id = category_id
        self.description = description
        self.point_description = point_description or []
        self.status = status
        self.popular = popular
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        
        # Validate business rules
        self._validate()
    
    def _validate(self) -> None:
        """Validate service business rules"""
        if self.price <= 0:
            raise ValueError("Service price must be positive")
        
        if self.duration <= 0:
            raise ValueError("Service duration must be positive")
        
        if len(self.name) > 100:
            raise ValueError("Service name cannot exceed 100 characters")
    
    def update_name(self, name: str) -> None:
        """Update service name"""
        if len(name) > 100:
            raise ValueError("Service name cannot exceed 100 characters")
        self.name = name
        self.updated_at = datetime.utcnow()
    
    def update_price(self, price: Decimal) -> None:
        """Update service price"""
        if price <= 0:
            raise ValueError("Service price must be positive")
        self.price = price
        self.updated_at = datetime.utcnow()
    
    def update_duration(self, duration: int) -> None:
        """Update service duration"""
        if duration <= 0:
            raise ValueError("Service duration must be positive")
        self.duration = duration
        self.updated_at = datetime.utcnow()
    
    def update_description(self, description: Optional[str]) -> None:
        """Update service description"""
        self.description = description
        self.updated_at = datetime.utcnow()
    
    def update_point_description(self, point_description: List[str]) -> None:
        """Update service point description"""
        self.point_description = point_description
        self.updated_at = datetime.utcnow()
    
    def update_category(self, category_id: UUID) -> None:
        """Update service category"""
        self.category_id = category_id
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate the service"""
        self.status = ServiceStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate the service"""
        self.status = ServiceStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def mark_as_popular(self) -> None:
        """Mark service as popular"""
        self.popular = True
        self.updated_at = datetime.utcnow()
    
    def unmark_as_popular(self) -> None:
        """Unmark service as popular"""
        self.popular = False
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if service is active"""
        return self.status == ServiceStatus.ACTIVE
    
    @property
    def is_popular(self) -> bool:
        """Check if service is popular"""
        return self.popular
    
    def __str__(self) -> str:
        return f"Service(id={self.id}, name='{self.name}', price={self.price}, duration={self.duration})"