"""Bookings database models."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship
import uuid

from app.core.db.base import Base, TimestampMixin


class Booking(Base, TimestampMixin):
    """Booking database model."""
    
    __tablename__ = "bookings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    booking_type = Column(String(20), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)  # in minutes
    
    # Optional fields
    notes = Column(Text, nullable=True, default="")
    phone_number = Column(String(20), nullable=True, default="")
    customer_location = Column(JSON, nullable=True)  # {'lat': float, 'lng': float}
    cancellation_fee = Column(Numeric(10, 2), default=0.00)
    quality_rating = Column(Integer, nullable=True)  # 1-5 stars
    quality_feedback = Column(Text, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    overtime_charges = Column(Numeric(10, 2), default=0.00)
    
    # Cancellation tracking
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by = Column(String, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Payment tracking
    payment_intent_id = Column(String, nullable=True)
    
    # Relationships
    customer = relationship("UserModel", back_populates="bookings")
    vehicle = relationship("Vehicle", back_populates="bookings")
    booking_services = relationship("BookingService", back_populates="booking", cascade="all, delete-orphan")
    
    @property
    def total_price_display(self) -> str:
        """Get formatted total price display."""
        return f"${float(self.total_price):.2f}"
    
    @property
    def total_duration_display(self) -> str:
        """Get formatted duration display."""
        hours = self.estimated_duration_minutes // 60
        minutes = self.estimated_duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def __repr__(self):
        return f"<Booking({self.id}, {self.status}, {self.scheduled_at})>"


class BookingService(Base):
    """BookingService database model - junction table with additional data."""
    
    __tablename__ = "booking_services"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    service_id = Column(String, ForeignKey("services.id"), nullable=False)
    name = Column(String(100), nullable=False)  # Snapshot of service name at booking time
    price = Column(Numeric(10, 2), nullable=False)  # Snapshot of price at booking time
    duration_minutes = Column(Integer, nullable=False)  # Snapshot of duration at booking time
    
    # Relationships
    booking = relationship("Booking", back_populates="booking_services")
    service = relationship("Service")  # Reference to current service data
    
    @property
    def price_display(self) -> str:
        """Get formatted price display."""
        return f"${float(self.price):.2f}"
    
    @property
    def duration_display(self) -> str:
        """Get formatted duration display."""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    def __repr__(self):
        return f"<BookingService({self.name}, {self.price_display})>"