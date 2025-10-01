"""Check out staff member use case."""

from datetime import date

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.staff.domain import Attendance
from app.features.staff.ports import IAttendanceRepository


class CheckOutStaffUseCase:
    """Check out staff member for the day."""

    def __init__(self, attendance_repository: IAttendanceRepository):
        self._attendance_repository = attendance_repository

    async def execute(self, staff_id: str) -> Attendance:
        """
        Check out staff member.

        Args:
            staff_id: Staff member ID

        Returns:
            Attendance: Updated attendance record

        Raises:
            NotFoundError: If attendance record not found
            BusinessRuleViolationError: If not checked in
        """
        # Get today's attendance
        today = date.today()
        attendance = await self._attendance_repository.get_by_staff_and_date(
            staff_id, today
        )

        if not attendance:
            raise NotFoundError(
                f"No attendance record found for staff {staff_id} on {today}"
            )

        if not attendance.is_checked_in:
            raise BusinessRuleViolationError(
                "Staff member is not checked in",
                details={"attendance_id": attendance.id},
            )

        # Check out
        attendance.check_out_staff()

        return await self._attendance_repository.update(attendance)
