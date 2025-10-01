"""Scheduling database models.

Clean Architecture Compliance:
- Uses string-based foreign keys (no cross-feature model imports)
- No relationship declarations (data fetched via repositories)
- Maintains database integrity through FK constraints
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text, JSON
import uuid

from app.core.db.base import Base, TimestampMixin


class TimeSlot(Base):
    """Time slot database model.

    Uses string-based foreign keys to avoid cross-feature imports.
    Related data is fetched via repositories, not relationships.
    """

    __tablename__ = "time_slots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    resource_id = Column(String, nullable=False)
    resource_type = Column(String(20), nullable=False)  # wash_bay or mobile_team
    is_available = Column(Boolean, nullable=False, default=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=True)
    buffer_minutes = Column(Integer, nullable=False, default=15)

    # String-based foreign keys (maintains DB integrity without model coupling)
    wash_bay_id = Column(String, ForeignKey("wash_bays.id"), nullable=True)
    mobile_team_id = Column(String, ForeignKey("mobile_teams.id"), nullable=True)

    # Note: No relationships declared here (clean architecture principle)
    # Related data is fetched explicitly via repositories when needed

    @property
    def duration_minutes(self):
        """Get duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def __repr__(self):
        return f"<TimeSlot({self.start_time}, {self.resource_type}, available={self.is_available})>"


class SchedulingConstraints(Base, TimestampMixin):
    """Scheduling constraints database model."""

    __tablename__ = "scheduling_constraints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    is_active = Column(Boolean, nullable=False, default=True)
    min_advance_hours = Column(Integer, nullable=False, default=2)
    max_advance_days = Column(Integer, nullable=False, default=90)
    slot_duration_minutes = Column(Integer, nullable=False, default=30)
    buffer_minutes = Column(Integer, nullable=False, default=15)
    business_hours = Column(JSON, nullable=True)  # Business hours by day

    def __repr__(self):
        return f"<SchedulingConstraints(active={self.is_active})>"


class BusinessHours(Base):
    """Business hours database model."""

    __tablename__ = "business_hours"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    day_of_week = Column(String(10), nullable=False)  # monday, tuesday, etc.
    open_time = Column(String(8), nullable=True)  # HH:MM:SS format
    close_time = Column(String(8), nullable=True)  # HH:MM:SS format
    is_closed = Column(Boolean, nullable=False, default=False)
    break_periods = Column(JSON, nullable=True)  # List of break periods
    facility_id = Column(String, nullable=True)  # For multi-location support

    def __repr__(self):
        return f"<BusinessHours({self.day_of_week}, {self.open_time}-{self.close_time})>"
