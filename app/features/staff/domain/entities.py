"""Staff domain entities."""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from .enums import (
    EmploymentType,
    StaffStatus,
    DocumentType,
    AttendanceStatus,
    ServiceType,
)


@dataclass
class StaffMember:
    """
    Staff member (washer) entity.

    Represents a car wash employee with their profile, skills, and performance metrics.
    """

    id: str
    user_id: str  # Link to auth.User
    employee_code: str
    first_name: str
    last_name: str
    phone: str
    email: str
    hire_date: date
    employment_type: EmploymentType
    status: StaffStatus
    hourly_rate: Decimal

    # Assignments
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None

    # Skills and capabilities
    skills: List[ServiceType] = field(default_factory=list)

    # Performance metrics
    total_services_completed: int = 0
    total_revenue_generated: Decimal = Decimal("0.00")
    average_rating: Decimal = Decimal("0.00")

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        """Check if staff member is active."""
        return self.status == StaffStatus.ACTIVE and self.deleted_at is None

    def can_perform_service(self, service_type: ServiceType) -> bool:
        """
        Check if staff member can perform a specific service type.

        Args:
            service_type: The service type to check

        Returns:
            bool: True if staff member has the required skill
        """
        if not self.is_active:
            return False
        return service_type in self.skills

    def add_skill(self, skill: ServiceType) -> None:
        """
        Add a skill to staff member's capabilities.

        Args:
            skill: The skill to add
        """
        if skill not in self.skills:
            self.skills.append(skill)

    def remove_skill(self, skill: ServiceType) -> None:
        """
        Remove a skill from staff member's capabilities.

        Args:
            skill: The skill to remove
        """
        if skill in self.skills:
            self.skills.remove(skill)

    def calculate_earnings(self, hours_worked: Decimal) -> Decimal:
        """
        Calculate earnings for given hours.

        Args:
            hours_worked: Number of hours worked

        Returns:
            Decimal: Total earnings
        """
        return self.hourly_rate * hours_worked

    def update_performance(
        self,
        services_increment: int = 0,
        revenue_increment: Decimal = Decimal("0.00"),
        new_rating: Optional[Decimal] = None,
    ) -> None:
        """
        Update performance metrics.

        Args:
            services_increment: Number of services to add
            revenue_increment: Revenue to add
            new_rating: New rating to average in
        """
        self.total_services_completed += services_increment
        self.total_revenue_generated += revenue_increment

        if new_rating is not None:
            # Calculate moving average
            current_total = self.average_rating * (self.total_services_completed - 1)
            self.average_rating = (current_total + new_rating) / self.total_services_completed


@dataclass
class StaffDocument:
    """
    Staff document entity.

    Represents documents associated with staff members (ID cards, certificates, contracts, etc.)
    """

    id: str
    staff_id: str
    document_type: DocumentType
    document_name: str
    file_path: str
    uploaded_at: datetime
    expires_at: Optional[datetime] = None
    verified: bool = False
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if document has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get number of days until document expires."""
        if self.expires_at is None:
            return None
        delta = self.expires_at - datetime.now()
        return delta.days

    def verify(self, verified_by_user_id: str) -> None:
        """
        Mark document as verified.

        Args:
            verified_by_user_id: ID of user verifying the document
        """
        self.verified = True
        self.verified_by_user_id = verified_by_user_id
        self.verified_at = datetime.now()


@dataclass
class Attendance:
    """
    Attendance record entity.

    Tracks daily attendance, check-in/out times, and hours worked.
    """

    id: str
    staff_id: str
    date: date
    status: AttendanceStatus
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_checked_in(self) -> bool:
        """Check if staff is currently checked in."""
        return self.check_in is not None and self.check_out is None

    def calculate_hours_worked(self) -> Decimal:
        """
        Calculate hours worked from check-in/out times.

        Returns:
            Decimal: Hours worked (rounded to 2 decimal places)
        """
        if self.check_in is None or self.check_out is None:
            return Decimal("0.00")

        delta = self.check_out - self.check_in
        hours = Decimal(delta.total_seconds()) / Decimal(3600)
        return round(hours, 2)

    def is_late(self, shift_start: time) -> bool:
        """
        Check if check-in was late compared to shift start time.

        Args:
            shift_start: Expected shift start time

        Returns:
            bool: True if checked in late
        """
        if self.check_in is None:
            return False

        check_in_time = self.check_in.time()
        return check_in_time > shift_start

    def check_in_staff(self) -> None:
        """Record check-in time."""
        self.check_in = datetime.now()
        if self.status == AttendanceStatus.ABSENT:
            self.status = AttendanceStatus.PRESENT

    def check_out_staff(self) -> None:
        """Record check-out time and calculate hours."""
        self.check_out = datetime.now()
        self.hours_worked = self.calculate_hours_worked()


@dataclass
class WorkSchedule:
    """
    Work schedule entity.

    Defines regular working hours for staff members.
    """

    id: str
    staff_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    shift_start: time
    shift_end: time
    break_duration_minutes: int = 0
    is_active: bool = True
    effective_from: date = field(default_factory=date.today)
    effective_until: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def day_name(self) -> str:
        """Get day name from day_of_week."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[self.day_of_week]

    @property
    def shift_duration_hours(self) -> Decimal:
        """Calculate shift duration in hours (excluding breaks)."""
        # Calculate total minutes
        start_minutes = self.shift_start.hour * 60 + self.shift_start.minute
        end_minutes = self.shift_end.hour * 60 + self.shift_end.minute

        # Handle overnight shifts
        if end_minutes < start_minutes:
            end_minutes += 24 * 60

        total_minutes = end_minutes - start_minutes - self.break_duration_minutes
        return Decimal(total_minutes) / Decimal(60)

    def is_effective_on(self, check_date: date) -> bool:
        """
        Check if schedule is effective on a given date.

        Args:
            check_date: Date to check

        Returns:
            bool: True if schedule is effective on the date
        """
        if not self.is_active:
            return False

        if check_date < self.effective_from:
            return False

        if self.effective_until and check_date > self.effective_until:
            return False

        return True

    def overlaps_with(self, other: "WorkSchedule") -> bool:
        """
        Check if this schedule overlaps with another.

        Args:
            other: Another work schedule

        Returns:
            bool: True if schedules overlap
        """
        if self.day_of_week != other.day_of_week:
            return False

        # Check time overlap
        return (
            self.shift_start < other.shift_end and self.shift_end > other.shift_start
        )
