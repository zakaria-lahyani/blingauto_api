"""Create work schedule use case."""

from dataclasses import dataclass
from datetime import date, time
from typing import Optional
import uuid

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from app.features.staff.domain import WorkSchedule, SchedulePolicy
from app.features.staff.ports import IStaffRepository, IWorkScheduleRepository


@dataclass
class CreateScheduleRequest:
    """Request to create work schedule."""

    staff_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    shift_start: time
    shift_end: time
    break_duration_minutes: int = 0
    effective_from: date = None
    effective_until: Optional[date] = None

    def __post_init__(self):
        if self.effective_from is None:
            self.effective_from = date.today()


class CreateScheduleUseCase:
    """
    Create work schedule for staff member.

    Business Rules:
    - Shift duration must be within acceptable range
    - No overlapping schedules for same day
    - Weekly hours must not exceed limits
    """

    def __init__(
        self,
        staff_repository: IStaffRepository,
        schedule_repository: IWorkScheduleRepository,
    ):
        self._staff_repository = staff_repository
        self._schedule_repository = schedule_repository

    async def execute(self, request: CreateScheduleRequest) -> WorkSchedule:
        """
        Create work schedule.

        Args:
            request: Create schedule request

        Returns:
            WorkSchedule: Created schedule

        Raises:
            NotFoundError: If staff member not found
            ValidationError: If validation fails
            BusinessRuleViolationError: If business rules violated
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(request.staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {request.staff_id}")

        # Validate day of week
        if request.day_of_week < 0 or request.day_of_week > 6:
            raise ValidationError("Day of week must be between 0 (Monday) and 6 (Sunday)")

        # Validate shift duration
        SchedulePolicy.validate_shift_duration(
            request.shift_start,
            request.shift_end,
            request.break_duration_minutes,
        )

        # Create schedule entity
        schedule = WorkSchedule(
            id=str(uuid.uuid4()),
            staff_id=request.staff_id,
            day_of_week=request.day_of_week,
            shift_start=request.shift_start,
            shift_end=request.shift_end,
            break_duration_minutes=request.break_duration_minutes,
            effective_from=request.effective_from,
            effective_until=request.effective_until,
        )

        # Validate break duration based on shift length
        SchedulePolicy.validate_break_duration(
            schedule.shift_duration_hours,
            request.break_duration_minutes,
        )

        # Check for conflicts
        existing_schedules = await self._schedule_repository.list_by_staff(
            request.staff_id,
            active_only=True,
        )

        conflicts = SchedulePolicy.check_schedule_conflicts(existing_schedules, schedule)
        if conflicts:
            conflict_details = [
                {
                    "day": c.day_name,
                    "time": f"{c.shift_start} - {c.shift_end}",
                }
                for c in conflicts
            ]
            raise BusinessRuleViolationError(
                "Schedule conflicts with existing schedules",
                details={"conflicts": conflict_details},
            )

        # Validate weekly hours don't exceed limits
        # Get all schedules including the new one
        all_schedules = existing_schedules + [schedule]
        SchedulePolicy.validate_weekly_hours(all_schedules, staff.employment_type)

        return await self._schedule_repository.create(schedule)
