"""
Services database models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, DECIMAL, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from typing import Optional, List

from src.shared.database import Base
from src.shared.utils.timestamp import db_utc_timestamp
from src.features.services.domain.entities import ServiceCategory, Service
from src.features.services.domain.enums import ServiceStatus, CategoryStatus



class ServiceCategoryModel(Base):
    """Service category database model"""
    
    __tablename__ = "service_categories"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), nullable=False, default=CategoryStatus.ACTIVE.value)
    
    # Timestamps - using standardized UTC timestamps
    created_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), onupdate=db_utc_timestamp(), nullable=False)
    
    # Relationships
    services = relationship("ServiceModel", back_populates="category", cascade="all, delete-orphan")
    
    def to_entity(self) -> ServiceCategory:
        """Convert to domain entity"""
        return ServiceCategory(
            id=self.id,
            name=self.name,
            description=self.description,
            status=CategoryStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, category: ServiceCategory) -> "ServiceCategoryModel":
        """Create from domain entity"""
        return cls(
            id=category.id,
            name=category.name,
            description=category.description,
            status=category.status.value,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
    def update_from_entity(self, category: ServiceCategory) -> None:
        """Update from domain entity"""
        self.name = category.name
        self.description = category.description
        self.status = category.status.value
        self.updated_at = category.updated_at


class ServiceModel(Base):
    """Service database model"""
    
    __tablename__ = "services"
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in minutes
    category_id = Column(UUID(as_uuid=True), ForeignKey("service_categories.id"), nullable=False)
    description = Column(Text)
    point_description = Column(ARRAY(String), default=[])
    status = Column(String(20), nullable=False, default=ServiceStatus.ACTIVE.value)
    popular = Column(Boolean, default=False, nullable=False)
    
    # Timestamps - using standardized UTC timestamps
    created_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), onupdate=db_utc_timestamp(), nullable=False)
    
    # Relationships
    category = relationship("ServiceCategoryModel", back_populates="services")
    
    def to_entity(self) -> Service:
        """Convert to domain entity"""
        return Service(
            id=self.id,
            name=self.name,
            price=Decimal(str(self.price)),
            duration=self.duration,
            category_id=self.category_id,
            description=self.description,
            point_description=self.point_description or [],
            status=ServiceStatus(self.status),
            popular=self.popular,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, service: Service) -> "ServiceModel":
        """Create from domain entity"""
        return cls(
            id=service.id,
            name=service.name,
            price=service.price,
            duration=service.duration,
            category_id=service.category_id,
            description=service.description,
            point_description=service.point_description,
            status=service.status.value,
            popular=service.popular,
            created_at=service.created_at,
            updated_at=service.updated_at
        )
    
    def update_from_entity(self, service: Service) -> None:
        """Update from domain entity"""
        self.name = service.name
        self.price = service.price
        self.duration = service.duration
        self.category_id = service.category_id
        self.description = service.description
        self.point_description = service.point_description
        self.status = service.status.value
        self.popular = service.popular
        self.updated_at = service.updated_at