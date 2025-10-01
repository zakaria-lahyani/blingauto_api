"""List staff members use case."""

from dataclasses import dataclass
from typing import List, Optional

from app.features.staff.domain import StaffMember, StaffStatus
from app.features.staff.ports import IStaffRepository


@dataclass
class ListStaffRequest:
    """Request to list staff members."""

    skip: int = 0
    limit: int = 100
    status: Optional[StaffStatus] = None
    assigned_bay_id: Optional[str] = None
    assigned_team_id: Optional[str] = None


class ListStaffUseCase:
    """List staff members with filters."""

    def __init__(self, staff_repository: IStaffRepository):
        self._staff_repository = staff_repository

    async def execute(self, request: ListStaffRequest) -> List[StaffMember]:
        """
        List staff members.

        Args:
            request: List staff request

        Returns:
            List[StaffMember]: List of staff members
        """
        staff_list = await self._staff_repository.list(
            skip=request.skip,
            limit=request.limit,
            status=request.status,
            assigned_bay_id=request.assigned_bay_id,
            assigned_team_id=request.assigned_team_id,
        )

        return staff_list
