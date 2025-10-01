"""Services database models."""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
import uuid

from app.core.db.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """Category database model."""
    
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    display_order = Column(Integer, nullable=False, default=0)
    
    # Relationships
    services = relationship("Service", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category({self.name}, {self.status})>"


class Service(Base, TimestampMixin):
    """Service database model."""
    
    __tablename__ = "services"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    is_popular = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    
    # Relationships
    category = relationship("Category", back_populates="services")
    # bookings = relationship("Booking", back_populates="service")  # Will be added when booking feature is implemented
    
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
        return f"<Service({self.name}, {self.price_display}, {self.status})>"