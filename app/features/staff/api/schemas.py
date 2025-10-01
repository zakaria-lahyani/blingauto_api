"""Staff API schemas (Pydantic DTOs)."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, validator

from app.features.staff.domain import (
    EmploymentType,
    StaffStatus,
    DocumentType,
    AttendanceStatus,
    ServiceType,
)


# ============================================================================
# Staff Schemas
# ============================================================================

class CreateStaffSchema(BaseModel):
    """Request schema for creating staff member."""

    user_id: str = Field(..., description="User ID from auth system")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    email: EmailStr
    hire_date: date
    employment_type: EmploymentType
    hourly_rate: Decimal = Field(..., gt=0, le=1000)
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None
    skills: List[ServiceType] = Field(default_factory=list)


class UpdateStaffSchema(BaseModel):
    """Request schema for updating staff member."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=1, max_length=20)
    email: Optional[EmailStr] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[StaffStatus] = None
    hourly_rate: Optional[Decimal] = Field(None, gt=0, le=1000)
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None
    skills: Optional[List[ServiceType]] = None


class StaffSchema(BaseModel):
    """Response schema for staff member."""

    id: str
    user_id: str
    employee_code: str
    first_name: str
    last_name: str
    full_name: str
    phone: str
    email: str
    hire_date: date
    employment_type: EmploymentType
    status: StaffStatus
    hourly_rate: Decimal
    assigned_bay_id: Optional[str]
    assigned_team_id: Optional[str]
    skills: List[ServiceType]
    total_services_completed: int
    total_revenue_generated: Decimal
    average_rating: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListStaffSchema(BaseModel):
    """Response schema for list of staff members."""

    items: List[StaffSchema]
    total: int
    skip: int
    limit: int


# ============================================================================
# Document Schemas
# ============================================================================

class UploadDocumentSchema(BaseModel):
    """Request schema for uploading document."""

    document_type: DocumentType
    document_name: str = Field(..., min_length=1, max_length=255)
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None


class StaffDocumentSchema(BaseModel):
    """Response schema for staff document."""

    id: str
    staff_id: str
    document_type: DocumentType
    document_name: str
    file_path: str
    file_url: str
    uploaded_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool
    days_until_expiry: Optional[int]
    verified: bool
    verified_by_user_id: Optional[str]
    verified_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ListDocumentsSchema(BaseModel):
    """Response schema for list of documents."""

    items: List[StaffDocumentSchema]
    total: int


# ============================================================================
# Attendance Schemas
# ============================================================================

class CheckInResponseSchema(BaseModel):
    """Response schema for check-in."""

    attendance_id: str
    staff_id: str
    date: date
    check_in: datetime
    status: AttendanceStatus
    message: str = "Successfully checked in"


class CheckOutResponseSchema(BaseModel):
    """Response schema for check-out."""

    attendance_id: str
    staff_id: str
    date: date
    check_in: datetime
    check_out: datetime
    hours_worked: Decimal
    status: AttendanceStatus
    message: str = "Successfully checked out"


class RecordAttendanceSchema(BaseModel):
    """Request schema for recording attendance (manual)."""

    staff_id: str
    date: date
    status: AttendanceStatus
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Optional[Decimal] = Field(None, ge=0, le=24)
    notes: Optional[str] = None


class AttendanceSchema(BaseModel):
    """Response schema for attendance record."""

    id: str
    staff_id: str
    date: date
    status: AttendanceStatus
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    hours_worked: Decimal
    is_checked_in: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttendanceReportSchema(BaseModel):
    """Response schema for attendance report."""

    items: List[AttendanceSchema]
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    total_hours: Decimal
    average_hours_per_day: Decimal
    attendance_rate: Decimal


# ============================================================================
# Schedule Schemas
# ============================================================================

class CreateScheduleSchema(BaseModel):
    """Request schema for creating schedule."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    shift_start: time
    shift_end: time
    break_duration_minutes: int = Field(default=0, ge=0, le=120)
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None

    @validator("effective_from", pre=True, always=True)
    def set_effective_from(cls, v):
        return v or date.today()


class UpdateScheduleSchema(BaseModel):
    """Request schema for updating schedule."""

    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    break_duration_minutes: Optional[int] = Field(None, ge=0, le=120)
    is_active: Optional[bool] = None
    effective_until: Optional[date] = None


class WorkScheduleSchema(BaseModel):
    """Response schema for work schedule."""

    id: str
    staff_id: str
    day_of_week: int
    day_name: str
    shift_start: time
    shift_end: time
    break_duration_minutes: int
    shift_duration_hours: Decimal
    is_active: bool
    effective_from: date
    effective_until: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ListSchedulesSchema(BaseModel):
    """Response schema for list of schedules."""

    items: List[WorkScheduleSchema]
    total: int


# ============================================================================
# Query Parameters
# ============================================================================

class StaffQueryParams(BaseModel):
    """Query parameters for listing staff."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
    status: Optional[StaffStatus] = None
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None


class AttendanceQueryParams(BaseModel):
    """Query parameters for attendance report."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
