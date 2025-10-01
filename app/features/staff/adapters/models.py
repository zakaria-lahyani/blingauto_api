"""Staff SQLAlchemy database models."""

from sqlalchemy import (
    Column,
    String,
    Numeric,
    Integer,
    Boolean,
    DateTime,
    Date,
    Time,
    ForeignKey,
    JSON,
    Text,
    Index,
)
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class StaffMemberModel(Base):
    """Staff member database model."""

    __tablename__ = "staff_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Link to auth user
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Basic info
    employee_code = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)

    # Employment details
    hire_date = Column(Date, nullable=False)
    employment_type = Column(String(20), nullable=False, index=True)  # full_time, part_time, contractor
    status = Column(String(20), nullable=False, default="active", index=True)  # active, on_leave, suspended, terminated
    hourly_rate = Column(Numeric(10, 2), nullable=False)

    # Assignments
    assigned_bay_id = Column(String, ForeignKey("wash_bays.id"), nullable=True)
    assigned_team_id = Column(String, ForeignKey("mobile_teams.id"), nullable=True)

    # Skills (stored as JSON array)
    skills = Column(JSON, nullable=False, default=list)

    # Performance metrics
    total_services_completed = Column(Integer, nullable=False, default=0)
    total_revenue_generated = Column(Numeric(12, 2), nullable=False, default=0)
    average_rating = Column(Numeric(3, 2), nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("ix_staff_status_deleted", "status", "deleted_at"),
        Index("ix_staff_employee_code_deleted", "employee_code", "deleted_at"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<StaffMemberModel(id={self.id}, employee_code={self.employee_code}, name={self.first_name} {self.last_name})>"


class StaffDocumentModel(Base):
    """Staff document database model."""

    __tablename__ = "staff_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    staff_id = Column(String, ForeignKey("staff_members.id"), nullable=False, index=True)

    # Document details
    document_type = Column(String(50), nullable=False, index=True)
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)

    # Metadata
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Verification
    verified = Column(Boolean, nullable=False, default=False)
    verified_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    # Index for finding expiring documents
    __table_args__ = (
        Index("ix_documents_expires_verified", "expires_at", "verified"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<StaffDocumentModel(id={self.id}, type={self.document_type}, name={self.document_name})>"


class AttendanceModel(Base):
    """Attendance record database model."""

    __tablename__ = "attendance_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    staff_id = Column(String, ForeignKey("staff_members.id"), nullable=False, index=True)

    # Date and times
    date = Column(Date, nullable=False, index=True)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)

    # Status and hours
    status = Column(String(20), nullable=False, index=True)  # present, absent, late, half_day, on_leave
    hours_worked = Column(Numeric(5, 2), nullable=False, default=0)

    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Composite indexes for queries
    __table_args__ = (
        Index("ix_attendance_staff_date", "staff_id", "date", unique=True),
        Index("ix_attendance_date_status", "date", "status"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<AttendanceModel(id={self.id}, staff_id={self.staff_id}, date={self.date}, status={self.status})>"


class WorkScheduleModel(Base):
    """Work schedule database model."""

    __tablename__ = "work_schedules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    staff_id = Column(String, ForeignKey("staff_members.id"), nullable=False, index=True)

    # Schedule details
    day_of_week = Column(Integer, nullable=False, index=True)  # 0=Monday, 6=Sunday
    shift_start = Column(Time, nullable=False)
    shift_end = Column(Time, nullable=False)
    break_duration_minutes = Column(Integer, nullable=False, default=0)

    # Status and effective dates
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    effective_from = Column(Date, nullable=False, index=True)
    effective_until = Column(Date, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Composite indexes for queries
    __table_args__ = (
        Index("ix_schedule_staff_day_active", "staff_id", "day_of_week", "is_active"),
        Index("ix_schedule_day_active_dates", "day_of_week", "is_active", "effective_from", "effective_until"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<WorkScheduleModel(id={self.id}, staff_id={self.staff_id}, day={self.day_of_week}, active={self.is_active})>"
