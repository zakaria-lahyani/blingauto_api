"""Update work schedule use case."""

from dataclasses import dataclass
from datetime import date, time
from typing import Optional

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from app.features.staff.domain import SchedulePolicy
from app.features.staff.ports import IWorkScheduleRepository, IStaffRepository


@dataclass
class UpdateScheduleRequest:
    """Request to update work schedule."""

    schedule_id: str
    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    break_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    effective_until: Optional[date] = None


class UpdateScheduleUseCase:
    """Update work schedule."""

    def __init__(
        self,
        schedule_repository: IWorkScheduleRepository,
        staff_repository: IStaffRepository,
    ):
        self._schedule_repository = schedule_repository
        self._staff_repository = staff_repository

    async def execute(self, request: UpdateScheduleRequest):
        """
        Update work schedule.

        Args:
            request: Update schedule request

        Returns:
            WorkSchedule: Updated schedule

        Raises:
            NotFoundError: If schedule not found
            ValidationError: If validation fails
        """
        # Get existing schedule
        schedule = await self._schedule_repository.get_by_id(request.schedule_id)
        if not schedule:
            raise NotFoundError(f"Schedule not found: {request.schedule_id}")

        # Check if can modify
        if not SchedulePolicy.can_modify_schedule(schedule):
            raise BusinessRuleViolationError("Cannot modify inactive or expired schedule")

        # Update fields
        if request.shift_start is not None:
            schedule.shift_start = request.shift_start

        if request.shift_end is not None:
            schedule.shift_end = request.shift_end

        if request.break_duration_minutes is not None:
            schedule.break_duration_minutes = request.break_duration_minutes

        if request.is_active is not None:
            schedule.is_active = request.is_active

        if request.effective_until is not None:
            schedule.effective_until = request.effective_until

        # Validate updated shift duration
        SchedulePolicy.validate_shift_duration(
            schedule.shift_start,
            schedule.shift_end,
            schedule.break_duration_minutes,
        )

        # Validate break duration
        SchedulePolicy.validate_break_duration(
            schedule.shift_duration_hours,
            schedule.break_duration_minutes,
        )

        # Check for conflicts if times changed
        if request.shift_start or request.shift_end:
            staff = await self._staff_repository.get_by_id(schedule.staff_id)
            existing_schedules = await self._schedule_repository.list_by_staff(
                schedule.staff_id,
                active_only=True,
            )

            conflicts = SchedulePolicy.check_schedule_conflicts(existing_schedules, schedule)
            if conflicts:
                raise BusinessRuleViolationError("Schedule conflicts with existing schedules")

            # Validate weekly hours
            SchedulePolicy.validate_weekly_hours(existing_schedules, staff.employment_type)

        return await self._schedule_repository.update(schedule)
