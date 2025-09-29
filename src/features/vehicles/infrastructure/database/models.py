"""
Vehicle database models
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import relationship

from src.shared.database.base import Base
from src.shared.utils.timestamp import db_utc_timestamp
from src.features.vehicles.domain.entities import Vehicle
from src.features.vehicles.domain.enums import VehicleStatus


class VehicleModel(Base):
    """Vehicle database model"""
    __tablename__ = "vehicles"
    
    # Primary key
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to user
    user_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False, index=True)
    
    # Vehicle details
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(30), nullable=False)
    license_plate = Column(String(20), nullable=False, index=True)
    
    # Status and metadata
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)  # VehicleStatus enum
    
    # Timestamps - using standardized UTC timestamps
    created_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), onupdate=db_utc_timestamp(), nullable=False)
    
    # Relationships - temporarily disabled back_populates to AuthUserModel
    # TODO: Re-enable back_populates once auth relationships are restored
    user = relationship("AuthUserModel")  # back_populates="vehicles" temporarily removed
    bookings = relationship("BookingModel", back_populates="vehicle")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_vehicles_user_status', 'user_id', 'status'),
        Index('idx_vehicles_user_default', 'user_id', 'is_default'),
        Index('idx_vehicles_license_plate_user', 'license_plate', 'user_id'),
        Index('idx_vehicles_make_model_year', 'make', 'model', 'year'),
    )
    
    def to_entity(self) -> Vehicle:
        """Convert model to domain entity"""
        return Vehicle(
            id=self.id,
            user_id=self.user_id,
            make=self.make,
            model=self.model,
            year=self.year,
            color=self.color,
            license_plate=self.license_plate,
            is_default=self.is_default,
            status=VehicleStatus(self.status),
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, entity: Vehicle) -> "VehicleModel":
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            make=entity.make,
            model=entity.model,
            year=entity.year,
            color=entity.color,
            license_plate=entity.license_plate,
            is_default=entity.is_default,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def update_from_entity(self, entity: Vehicle) -> None:
        """Update model from domain entity"""
        self.make = entity.make
        self.model = entity.model
        self.year = entity.year
        self.color = entity.color
        self.license_plate = entity.license_plate
        self.is_default = entity.is_default
        self.status = entity.status.value
        self.updated_at = entity.updated_at
    
    def __repr__(self):
        return f"<VehicleModel(id={self.id}, user_id={self.user_id}, {self.year} {self.make} {self.model})>"