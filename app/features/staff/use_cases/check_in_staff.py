"""Check in staff member use case."""

from datetime import date, datetime
import uuid

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.staff.domain import Attendance, AttendanceStatus
from app.features.staff.ports import IStaffRepository, IAttendanceRepository


class CheckInStaffUseCase:
    """Check in staff member for the day."""

    def __init__(
        self,
        staff_repository: IStaffRepository,
        attendance_repository: IAttendanceRepository,
    ):
        self._staff_repository = staff_repository
        self._attendance_repository = attendance_repository

    async def execute(self, staff_id: str) -> Attendance:
        """
        Check in staff member.

        Args:
            staff_id: Staff member ID

        Returns:
            Attendance: Created/updated attendance record

        Raises:
            NotFoundError: If staff member not found
            BusinessRuleViolationError: If already checked in
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {staff_id}")

        # Check if already has attendance for today
        today = date.today()
        existing_attendance = await self._attendance_repository.get_by_staff_and_date(
            staff_id, today
        )

        if existing_attendance:
            if existing_attendance.is_checked_in:
                raise BusinessRuleViolationError(
                    "Staff member is already checked in",
                    details={"attendance_id": existing_attendance.id},
                )

            # Update existing attendance
            existing_attendance.check_in_staff()
            return await self._attendance_repository.update(existing_attendance)

        # Create new attendance record
        attendance = Attendance(
            id=str(uuid.uuid4()),
            staff_id=staff_id,
            date=today,
            status=AttendanceStatus.PRESENT,
            check_in=datetime.now(),
        )

        return await self._attendance_repository.create(attendance)
