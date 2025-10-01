"""Vehicle database models."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.core.db.base import Base, TimestampMixin


class Vehicle(Base, TimestampMixin):
    """Vehicle database model."""
    
    __tablename__ = "vehicles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("users.id"), nullable=False)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    color = Column(String(30), nullable=False)
    license_plate = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("UserModel", back_populates="vehicles")
    bookings = relationship("Booking", back_populates="vehicle", cascade="all, delete-orphan")
    
    @property
    def display_name(self) -> str:
        """Get display name for the vehicle."""
        return f"{self.year} {self.make} {self.model}"
    
    def __repr__(self):
        return f"<Vehicle({self.display_name}, {self.license_plate})>"