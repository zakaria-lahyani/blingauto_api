"""
SQLAlchemy database models for facilities feature.

Maps domain entities to database tables following clean architecture.
"""

from datetime import datetime
from sqlalchemy import Column, String, Numeric, Integer, DateTime, JSON, Index
from sqlalchemy.sql import func

from app.core.db import Base


class WashBayModel(Base):
    """
    Database model for wash bays.

    Implements RG-FAC-001: Wash bay configuration persistence.
    """

    __tablename__ = "wash_bays"

    id = Column(String, primary_key=True)
    bay_number = Column(String(50), unique=True, nullable=False, index=True)
    max_vehicle_size = Column(String(20), nullable=False)  # compact, standard, large, oversized
    equipment_types = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default='active', index=True)  # active, inactive, maintenance
    location_latitude = Column(Numeric(10, 8), nullable=True)
    location_longitude = Column(Numeric(11, 8), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('ix_wash_bays_status_deleted', 'status', 'deleted_at'),
        Index('ix_wash_bays_bay_number_deleted', 'bay_number', 'deleted_at'),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<WashBayModel(id={self.id}, bay_number={self.bay_number}, status={self.status})>"


class MobileTeamModel(Base):
    """
    Database model for mobile teams.

    Implements RG-FAC-003: Mobile team configuration persistence.
    """

    __tablename__ = "mobile_teams"

    id = Column(String, primary_key=True)
    team_name = Column(String(100), unique=True, nullable=False, index=True)
    base_latitude = Column(Numeric(10, 8), nullable=False)
    base_longitude = Column(Numeric(11, 8), nullable=False)
    service_radius_km = Column(Numeric(6, 2), nullable=False, default=50.0)
    daily_capacity = Column(Integer, nullable=False, default=8)
    equipment_types = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default='active', index=True)  # active, inactive
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('ix_mobile_teams_status_deleted', 'status', 'deleted_at'),
        Index('ix_mobile_teams_team_name_deleted', 'team_name', 'deleted_at'),
        Index('ix_mobile_teams_location', 'base_latitude', 'base_longitude'),  # For radius queries
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<MobileTeamModel(id={self.id}, team_name={self.team_name}, status={self.status})>"
