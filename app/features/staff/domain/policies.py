"""Staff domain policies - business rules."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional

from .entities import StaffMember, Attendance, WorkSchedule
from .enums import StaffStatus, AttendanceStatus, EmploymentType


class StaffManagementPolicy:
    """Business rules for staff management."""

    MIN_HOURLY_RATE = Decimal("10.00")
    MAX_HOURLY_RATE = Decimal("100.00")
    EMPLOYEE_CODE_PREFIX = "EMP"

    @staticmethod
    def validate_hourly_rate(rate: Decimal) -> None:
        """
        Validate hourly rate is within acceptable range.

        Args:
            rate: Hourly rate to validate

        Raises:
            ValueError: If rate is outside acceptable range
        """
        if rate < StaffManagementPolicy.MIN_HOURLY_RATE:
            raise ValueError(
                f"Hourly rate cannot be less than {StaffManagementPolicy.MIN_HOURLY_RATE}"
            )

        if rate > StaffManagementPolicy.MAX_HOURLY_RATE:
            raise ValueError(
                f"Hourly rate cannot exceed {StaffManagementPolicy.MAX_HOURLY_RATE}"
            )

    @staticmethod
    def validate_hire_date(hire_date: date) -> None:
        """
        Validate hire date is not in the future.

        Args:
            hire_date: Hire date to validate

        Raises:
            ValueError: If hire date is in the future
        """
        if hire_date > date.today():
            raise ValueError("Hire date cannot be in the future")

    @staticmethod
    def can_terminate(staff: StaffMember) -> bool:
        """
        Check if staff member can be terminated.

        Args:
            staff: Staff member to check

        Returns:
            bool: True if staff can be terminated
        """
        # Cannot terminate already terminated staff
        if staff.status == StaffStatus.TERMINATED:
            return False

        return True

    @staticmethod
    def can_suspend(staff: StaffMember) -> bool:
        """
        Check if staff member can be suspended.

        Args:
            staff: Staff member to check

        Returns:
            bool: True if staff can be suspended
        """
        # Can only suspend active staff
        return staff.status == StaffStatus.ACTIVE

    @staticmethod
    def can_reactivate(staff: StaffMember) -> bool:
        """
        Check if staff member can be reactivated.

        Args:
            staff: Staff member to check

        Returns:
            bool: True if staff can be reactivated
        """
        # Can reactivate suspended or on-leave staff
        return staff.status in [StaffStatus.SUSPENDED, StaffStatus.ON_LEAVE]

    @staticmethod
    def generate_employee_code(staff_count: int) -> str:
        """
        Generate unique employee code.

        Args:
            staff_count: Current count of staff members

        Returns:
            str: Generated employee code
        """
        return f"{StaffManagementPolicy.EMPLOYEE_CODE_PREFIX}{staff_count + 1:05d}"

    @staticmethod
    def calculate_probation_end_date(
        hire_date: date,
        employment_type: EmploymentType,
    ) -> date:
        """
        Calculate probation period end date.

        Args:
            hire_date: Date of hire
            employment_type: Type of employment

        Returns:
            date: Probation end date
        """
        # Full-time: 3 months, Part-time: 1 month, Contractor: No probation
        if employment_type == EmploymentType.FULL_TIME:
            return hire_date + timedelta(days=90)
        elif employment_type == EmploymentType.PART_TIME:
            return hire_date + timedelta(days=30)
        else:
            return hire_date  # No probation for contractors


class AttendancePolicy:
    """Business rules for attendance management."""

    LATE_THRESHOLD_MINUTES = 15
    HALF_DAY_HOURS = Decimal("4.00")
    FULL_DAY_HOURS = Decimal("8.00")
    AUTO_CHECKOUT_HOUR = 23  # 11 PM

    @staticmethod
    def determine_attendance_status(
        check_in: Optional[datetime],
        check_out: Optional[datetime],
        shift_start: time,
        shift_end: time,
    ) -> AttendanceStatus:
        """
        Determine attendance status based on check-in/out times.

        Args:
            check_in: Check-in time
            check_out: Check-out time
            shift_start: Expected shift start time
            shift_end: Expected shift end time

        Returns:
            AttendanceStatus: Determined status
        """
        if check_in is None:
            return AttendanceStatus.ABSENT

        check_in_time = check_in.time()

        # Calculate lateness
        shift_start_dt = datetime.combine(check_in.date(), shift_start)
        late_minutes = (check_in - shift_start_dt).total_seconds() / 60

        if late_minutes > AttendancePolicy.LATE_THRESHOLD_MINUTES:
            return AttendanceStatus.LATE

        # Check if half day (if checked out early)
        if check_out is not None:
            hours_worked = Decimal((check_out - check_in).total_seconds() / 3600)
            if hours_worked < AttendancePolicy.HALF_DAY_HOURS:
                return AttendanceStatus.HALF_DAY

        return AttendanceStatus.PRESENT

    @staticmethod
    def should_auto_checkout(attendance: Attendance) -> bool:
        """
        Check if attendance should be auto-checked out.

        Args:
            attendance: Attendance record

        Returns:
            bool: True if should auto checkout
        """
        if not attendance.is_checked_in:
            return False

        # Auto checkout if still checked in after auto checkout hour
        now = datetime.now()
        if now.hour >= AttendancePolicy.AUTO_CHECKOUT_HOUR:
            return True

        return False

    @staticmethod
    def validate_attendance_date(attendance_date: date) -> None:
        """
        Validate attendance date.

        Args:
            attendance_date: Date to validate

        Raises:
            ValueError: If date is invalid
        """
        # Cannot record attendance more than 30 days in the past
        if attendance_date < date.today() - timedelta(days=30):
            raise ValueError("Cannot record attendance more than 30 days in the past")

        # Cannot record attendance more than 7 days in the future
        if attendance_date > date.today() + timedelta(days=7):
            raise ValueError("Cannot record attendance more than 7 days in the future")

    @staticmethod
    def calculate_attendance_rate(
        present_days: int,
        total_days: int,
    ) -> Decimal:
        """
        Calculate attendance rate percentage.

        Args:
            present_days: Number of days present
            total_days: Total working days

        Returns:
            Decimal: Attendance rate percentage
        """
        if total_days == 0:
            return Decimal("0.00")

        rate = (Decimal(present_days) / Decimal(total_days)) * Decimal("100")
        return round(rate, 2)


class SchedulePolicy:
    """Business rules for work schedule management."""

    MIN_SHIFT_HOURS = Decimal("2.00")
    MAX_SHIFT_HOURS = Decimal("12.00")
    MAX_WEEKLY_HOURS_FULL_TIME = Decimal("40.00")
    MAX_WEEKLY_HOURS_PART_TIME = Decimal("30.00")
    MIN_BREAK_MINUTES = 30

    @staticmethod
    def validate_shift_duration(
        shift_start: time,
        shift_end: time,
        break_minutes: int,
    ) -> None:
        """
        Validate shift duration is within acceptable range.

        Args:
            shift_start: Shift start time
            shift_end: Shift end time
            break_minutes: Break duration in minutes

        Raises:
            ValueError: If shift duration is invalid
        """
        # Calculate duration
        start_minutes = shift_start.hour * 60 + shift_start.minute
        end_minutes = shift_end.hour * 60 + shift_end.minute

        if end_minutes < start_minutes:
            end_minutes += 24 * 60

        duration_hours = Decimal(end_minutes - start_minutes - break_minutes) / Decimal(60)

        if duration_hours < SchedulePolicy.MIN_SHIFT_HOURS:
            raise ValueError(f"Shift duration cannot be less than {SchedulePolicy.MIN_SHIFT_HOURS} hours")

        if duration_hours > SchedulePolicy.MAX_SHIFT_HOURS:
            raise ValueError(f"Shift duration cannot exceed {SchedulePolicy.MAX_SHIFT_HOURS} hours")

    @staticmethod
    def validate_break_duration(shift_duration_hours: Decimal, break_minutes: int) -> None:
        """
        Validate break duration based on shift length.

        Args:
            shift_duration_hours: Duration of shift in hours
            break_minutes: Break duration in minutes

        Raises:
            ValueError: If break duration is invalid
        """
        # Shifts over 6 hours require at least 30 minutes break
        if shift_duration_hours > Decimal("6.00") and break_minutes < SchedulePolicy.MIN_BREAK_MINUTES:
            raise ValueError(
                f"Shifts over 6 hours require at least {SchedulePolicy.MIN_BREAK_MINUTES} minutes break"
            )

    @staticmethod
    def validate_weekly_hours(
        schedules: List[WorkSchedule],
        employment_type: EmploymentType,
    ) -> None:
        """
        Validate total weekly hours don't exceed limits.

        Args:
            schedules: List of work schedules for the week
            employment_type: Type of employment

        Raises:
            ValueError: If weekly hours exceed limits
        """
        total_hours = sum(schedule.shift_duration_hours for schedule in schedules)

        max_hours = (
            SchedulePolicy.MAX_WEEKLY_HOURS_FULL_TIME
            if employment_type == EmploymentType.FULL_TIME
            else SchedulePolicy.MAX_WEEKLY_HOURS_PART_TIME
        )

        if total_hours > max_hours:
            raise ValueError(
                f"{employment_type.value} employees cannot exceed {max_hours} hours per week"
            )

    @staticmethod
    def check_schedule_conflicts(
        existing_schedules: List[WorkSchedule],
        new_schedule: WorkSchedule,
    ) -> List[WorkSchedule]:
        """
        Check for schedule conflicts.

        Args:
            existing_schedules: List of existing schedules
            new_schedule: New schedule to check

        Returns:
            List[WorkSchedule]: List of conflicting schedules
        """
        conflicts = []
        for schedule in existing_schedules:
            if schedule.id != new_schedule.id and new_schedule.overlaps_with(schedule):
                # Check if both are effective on the same dates
                if (
                    schedule.is_effective_on(new_schedule.effective_from)
                    or new_schedule.is_effective_on(schedule.effective_from)
                ):
                    conflicts.append(schedule)

        return conflicts

    @staticmethod
    def can_modify_schedule(schedule: WorkSchedule) -> bool:
        """
        Check if schedule can be modified.

        Args:
            schedule: Schedule to check

        Returns:
            bool: True if schedule can be modified
        """
        # Cannot modify inactive schedules
        if not schedule.is_active:
            return False

        # Cannot modify expired schedules
        if schedule.effective_until and schedule.effective_until < date.today():
            return False

        return True
