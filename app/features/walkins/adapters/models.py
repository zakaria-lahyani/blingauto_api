"""Walk-in database models."""

from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    Integer,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class WalkInServiceModel(Base):
    """Walk-in service database model."""

    __tablename__ = "walkin_services"

    # Primary identification
    id = Column(String, primary_key=True)
    service_number = Column(String(50), unique=True, nullable=False, index=True)

    # Vehicle information
    vehicle_make = Column(String(100), nullable=False)
    vehicle_model = Column(String(100), nullable=False)
    vehicle_color = Column(String(50), nullable=False)
    vehicle_size = Column(String(20), nullable=False)  # SMALL, MEDIUM, LARGE, XL
    license_plate = Column(String(20), nullable=True, index=True)

    # Customer information (optional)
    customer_name = Column(String(200), nullable=True)
    customer_phone = Column(String(20), nullable=True, index=True)

    # Status
    status = Column(
        String(20), nullable=False, index=True
    )  # IN_PROGRESS, COMPLETED, CANCELLED
    payment_status = Column(
        String(20), nullable=False, index=True
    )  # PENDING, PARTIAL, PAID

    # Pricing
    total_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    discount_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    discount_reason = Column(String(200), nullable=True)
    final_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    paid_amount = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    # Timing
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Tracking (string-based FKs, no cross-feature imports)
    created_by_id = Column(String, nullable=False, index=True)  # Staff ID
    completed_by_id = Column(String, nullable=True)  # Staff ID
    cancelled_by_id = Column(String, nullable=True)  # Staff ID

    # Additional info
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Payment details (stored as JSONB)
    payment_details = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    service_items = relationship(
        "WalkInServiceItemModel",
        back_populates="walkin",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_walkin_services_status_created", "status", "created_at"),
        Index("ix_walkin_services_payment_status", "payment_status", "created_at"),
        Index("ix_walkin_services_created_by_date", "created_by_id", "created_at"),
        Index("ix_walkin_services_started_date", "started_at"),
        Index("ix_walkin_services_service_number", "service_number"),
    )


class WalkInServiceItemModel(Base):
    """Walk-in service item (individual service) database model."""

    __tablename__ = "walkin_service_items"

    # Primary identification
    id = Column(String, primary_key=True)
    walkin_id = Column(
        String, ForeignKey("walkin_services.id", ondelete="CASCADE"), nullable=False
    )

    # Service reference (string-based FK)
    service_id = Column(String, nullable=False, index=True)  # Reference to services
    service_name = Column(String(200), nullable=False)

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    product_costs = Column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )  # For profit calculation
    quantity = Column(Integer, nullable=False, default=1)

    # Additional info
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    walkin = relationship("WalkInServiceModel", back_populates="service_items")

    # Indexes for performance
    __table_args__ = (
        Index("ix_walkin_service_items_walkin", "walkin_id"),
        Index("ix_walkin_service_items_service", "service_id"),
    )
