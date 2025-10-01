"""Get staff member use case."""

from app.core.errors import NotFoundError
from app.features.staff.domain import StaffMember
from app.features.staff.ports import IStaffRepository


class GetStaffUseCase:
    """Get staff member by ID."""

    def __init__(self, staff_repository: IStaffRepository):
        self._staff_repository = staff_repository

    async def execute(self, staff_id: str) -> StaffMember:
        """
        Get staff member by ID.

        Args:
            staff_id: Staff member ID

        Returns:
            StaffMember: Staff member entity

        Raises:
            NotFoundError: If staff member not found
        """
        staff = await self._staff_repository.get_by_id(staff_id)

        if not staff:
            raise NotFoundError(f"Staff member not found: {staff_id}")

        return staff
