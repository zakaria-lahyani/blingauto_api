"""Get attendance report use case."""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.core.errors import NotFoundError
from app.features.staff.domain import Attendance
from app.features.staff.ports import IStaffRepository, IAttendanceRepository


@dataclass
class GetAttendanceReportRequest:
    """Request to get attendance report."""

    staff_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skip: int = 0
    limit: int = 100


class GetAttendanceReportUseCase:
    """Get attendance report for a staff member."""

    def __init__(
        self,
        staff_repository: IStaffRepository,
        attendance_repository: IAttendanceRepository,
    ):
        self._staff_repository = staff_repository
        self._attendance_repository = attendance_repository

    async def execute(self, request: GetAttendanceReportRequest) -> List[Attendance]:
        """
        Get attendance report.

        Args:
            request: Get attendance report request

        Returns:
            List[Attendance]: List of attendance records

        Raises:
            NotFoundError: If staff member not found
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(request.staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {request.staff_id}")

        # Get attendance records
        attendance_list = await self._attendance_repository.list_by_staff(
            staff_id=request.staff_id,
            start_date=request.start_date,
            end_date=request.end_date,
            skip=request.skip,
            limit=request.limit,
        )

        return attendance_list
