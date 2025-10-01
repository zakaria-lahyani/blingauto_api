"""Deactivate staff member use case."""

from app.core.errors import NotFoundError
from app.features.staff.domain import StaffStatus
from app.features.staff.ports import IStaffRepository


class DeactivateStaffUseCase:
    """Deactivate (soft delete) staff member."""

    def __init__(self, staff_repository: IStaffRepository):
        self._staff_repository = staff_repository

    async def execute(self, staff_id: str) -> bool:
        """
        Deactivate staff member.

        Args:
            staff_id: Staff member ID

        Returns:
            bool: True if deactivated successfully

        Raises:
            NotFoundError: If staff member not found
        """
        staff = await self._staff_repository.get_by_id(staff_id)

        if not staff:
            raise NotFoundError(f"Staff member not found: {staff_id}")

        # Change status to terminated
        staff.status = StaffStatus.TERMINATED
        await self._staff_repository.update(staff)

        # Soft delete
        return await self._staff_repository.delete(staff_id)
