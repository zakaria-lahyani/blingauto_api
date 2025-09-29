"""
Booking database models
"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID
from typing import List
from sqlalchemy import Column, String, DateTime, Text, Integer, DECIMAL, ForeignKey, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from sqlalchemy.orm import relationship

from src.shared.database import Base
from src.shared.utils.timestamp import db_utc_timestamp
from src.features.bookings.domain.entities import Booking, BookingService
from src.features.bookings.domain.enums import BookingStatus, BookingType, QualityRating


class BookingModel(Base):
    """Booking database model"""
    __tablename__ = "bookings"
    
    # Primary identification
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relationships
    customer_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=False)
    vehicle_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    
    # Scheduling information
    scheduled_at = Column(DateTime, nullable=False, index=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Booking details
    status = Column(String(20), nullable=False, default="pending", index=True)
    booking_type = Column(String(20), nullable=False, default="in_home")  # BookingType enum
    notes = Column(Text, nullable=True)
    customer_location = Column(Text, nullable=True)  # JSON stored as text
    vehicle_size = Column(String(20), nullable=False, default="standard")
    
    # Pricing and duration
    total_price = Column(DECIMAL(10, 2), nullable=False)
    total_duration = Column(Integer, nullable=False)  # in minutes
    cancellation_fee = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    
    # Quality rating
    quality_rating = Column(Integer, nullable=True)  # 1-5 scale
    quality_feedback = Column(Text, nullable=True)
    
    # Timestamps - using standardized UTC timestamps
    created_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), onupdate=db_utc_timestamp(), nullable=False)
    
    # Relationships - temporarily disabled back_populates to AuthUserModel
    # TODO: Re-enable back_populates once auth relationships are restored
    services = relationship("BookingServiceModel", back_populates="booking", cascade="all, delete-orphan")
    customer = relationship("AuthUserModel", foreign_keys=[customer_id])  # back_populates="bookings" temporarily removed
    vehicle = relationship("VehicleModel", back_populates="bookings", foreign_keys=[vehicle_id])
    
    def to_entity(self) -> Booking:
        """Convert model to domain entity"""
        import json
        
        # Convert BookingService models to domain entities
        booking_services = [service.to_entity() for service in self.services]
        
        # Parse customer location if it exists
        customer_location = None
        if self.customer_location:
            try:
                customer_location = json.loads(self.customer_location)
            except (json.JSONDecodeError, TypeError):
                customer_location = None
        
        return Booking(
            id=self.id,
            customer_id=self.customer_id,
            vehicle_id=self.vehicle_id,
            scheduled_at=self.scheduled_at,
            services=booking_services,
            booking_type=BookingType(self.booking_type),
            notes=self.notes,
            customer_location=customer_location,
            vehicle_size=self.vehicle_size,
            status=BookingStatus(self.status),
            total_price=Decimal(str(self.total_price)),
            total_duration=self.total_duration,
            cancellation_fee=Decimal(str(self.cancellation_fee)),
            quality_rating=QualityRating(self.quality_rating) if self.quality_rating else None,
            quality_feedback=self.quality_feedback,
            actual_start_time=self.actual_start_time,
            actual_end_time=self.actual_end_time,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
    
    @classmethod
    def from_entity(cls, entity: Booking) -> "BookingModel":
        """Create model from domain entity"""
        import json
        
        # Serialize customer location
        customer_location_str = None
        if entity.customer_location:
            customer_location_str = json.dumps(entity.customer_location)
        
        return cls(
            id=entity.id,
            customer_id=entity.customer_id,
            vehicle_id=entity.vehicle_id,
            scheduled_at=entity.scheduled_at,
            booking_type=entity.booking_type.value,
            notes=entity.notes,
            customer_location=customer_location_str,
            vehicle_size=entity.vehicle_size,
            status=entity.status.value,
            total_price=entity.total_price,
            total_duration=entity.total_duration,
            cancellation_fee=entity.cancellation_fee,
            quality_rating=entity.quality_rating.value if entity.quality_rating else None,
            quality_feedback=entity.quality_feedback,
            actual_start_time=entity.actual_start_time,
            actual_end_time=entity.actual_end_time,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def update_from_entity(self, entity: Booking) -> None:
        """Update model from domain entity"""
        import json
        
        # Serialize customer location
        customer_location_str = None
        if entity.customer_location:
            customer_location_str = json.dumps(entity.customer_location)
        
        self.booking_type = entity.booking_type.value
        self.notes = entity.notes
        self.customer_location = customer_location_str
        self.vehicle_size = entity.vehicle_size
        self.status = entity.status.value
        self.total_price = entity.total_price
        self.total_duration = entity.total_duration
        self.cancellation_fee = entity.cancellation_fee
        self.quality_rating = entity.quality_rating.value if entity.quality_rating else None
        self.quality_feedback = entity.quality_feedback
        self.actual_start_time = entity.actual_start_time
        self.actual_end_time = entity.actual_end_time
        self.updated_at = entity.updated_at
    
    def __repr__(self):
        return f"<BookingModel(id={self.id}, customer_id={self.customer_id}, status={self.status}, scheduled_at={self.scheduled_at})>"


class BookingServiceModel(Base):
    """Booking service association model"""
    __tablename__ = "booking_services"
    
    # Primary identification
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relationships
    booking_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    service_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    
    # Service snapshot (captured at booking time)
    service_name = Column(String(100), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    duration = Column(Integer, nullable=False)  # in minutes
    
    # Timestamps - using standardized UTC timestamps
    created_at = Column(DateTime(timezone=True), server_default=db_utc_timestamp(), nullable=False)
    
    # Relationships
    booking = relationship("BookingModel", back_populates="services")
    service = relationship("ServiceModel", foreign_keys=[service_id])
    
    def to_entity(self) -> BookingService:
        """Convert model to domain entity"""
        return BookingService(
            id=self.id,
            service_id=self.service_id,
            service_name=self.service_name,
            price=Decimal(str(self.price)),
            duration=self.duration
        )
    
    @classmethod
    def from_entity(cls, entity: BookingService, booking_id: UUID) -> "BookingServiceModel":
        """Create model from domain entity"""
        return cls(
            id=entity.id,
            booking_id=booking_id,
            service_id=entity.service_id,
            service_name=entity.service_name,
            price=entity.price,
            duration=entity.duration,
            created_at=entity.created_at if hasattr(entity, 'created_at') else None
        )
    
    def update_from_entity(self, entity: BookingService) -> None:
        """Update model from domain entity"""
        self.service_name = entity.service_name
        self.price = entity.price
        self.duration = entity.duration
    
    def __repr__(self):
        return f"<BookingServiceModel(booking_id={self.booking_id}, service_id={self.service_id}, price={self.price})>"


class BookingEventModel(Base):
    """Booking domain events for audit trail and integration"""
    __tablename__ = "booking_events"
    
    # Primary identification
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Event information
    booking_id = Column(PostgreSQL_UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(Text, nullable=True)  # JSON data
    
    # Context
    customer_id = Column(PostgreSQL_UUID(as_uuid=True), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=db_utc_timestamp(), index=True)
    
    # Processing status
    processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    booking = relationship("BookingModel", foreign_keys=[booking_id])
    
    def __repr__(self):
        return f"<BookingEventModel(booking_id={self.booking_id}, event_type={self.event_type}, occurred_at={self.occurred_at})>"