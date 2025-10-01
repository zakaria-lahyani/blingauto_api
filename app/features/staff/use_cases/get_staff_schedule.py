"""Get staff schedule use case."""

from typing import List

from app.core.errors import NotFoundError
from app.features.staff.domain import WorkSchedule
from app.features.staff.ports import IStaffRepository, IWorkScheduleRepository


class GetStaffScheduleUseCase:
    """Get work schedule for a staff member."""

    def __init__(
        self,
        staff_repository: IStaffRepository,
        schedule_repository: IWorkScheduleRepository,
    ):
        self._staff_repository = staff_repository
        self._schedule_repository = schedule_repository

    async def execute(
        self,
        staff_id: str,
        active_only: bool = True,
    ) -> List[WorkSchedule]:
        """
        Get staff schedule.

        Args:
            staff_id: Staff member ID
            active_only: Return only active schedules

        Returns:
            List[WorkSchedule]: List of schedules

        Raises:
            NotFoundError: If staff member not found
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {staff_id}")

        # Get schedules
        schedules = await self._schedule_repository.list_by_staff(
            staff_id=staff_id,
            active_only=active_only,
        )

        return schedules
