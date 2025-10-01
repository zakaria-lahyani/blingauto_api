"""Record attendance use case (manager/admin function)."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from app.core.errors import NotFoundError, ValidationError
from app.features.staff.domain import Attendance, AttendanceStatus, AttendancePolicy
from app.features.staff.ports import IStaffRepository, IAttendanceRepository


@dataclass
class RecordAttendanceRequest:
    """Request to record attendance."""

    staff_id: str
    date: date
    status: AttendanceStatus
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    hours_worked: Optional[Decimal] = None
    notes: Optional[str] = None


class RecordAttendanceUseCase:
    """
    Record attendance manually (for managers/admins).

    Allows recording past attendance or correcting existing records.
    """

    def __init__(
        self,
        staff_repository: IStaffRepository,
        attendance_repository: IAttendanceRepository,
    ):
        self._staff_repository = staff_repository
        self._attendance_repository = attendance_repository

    async def execute(self, request: RecordAttendanceRequest) -> Attendance:
        """
        Record attendance.

        Args:
            request: Record attendance request

        Returns:
            Attendance: Created/updated attendance record

        Raises:
            NotFoundError: If staff member not found
            ValidationError: If validation fails
        """
        # Verify staff exists
        staff = await self._staff_repository.get_by_id(request.staff_id)
        if not staff:
            raise NotFoundError(f"Staff member not found: {request.staff_id}")

        # Validate date
        AttendancePolicy.validate_attendance_date(request.date)

        # Check if attendance already exists
        existing = await self._attendance_repository.get_by_staff_and_date(
            request.staff_id, request.date
        )

        if existing:
            # Update existing
            existing.status = request.status
            existing.check_in = request.check_in
            existing.check_out = request.check_out
            existing.notes = request.notes

            if request.hours_worked:
                existing.hours_worked = request.hours_worked
            elif request.check_in and request.check_out:
                existing.hours_worked = existing.calculate_hours_worked()

            return await self._attendance_repository.update(existing)

        # Create new attendance
        attendance = Attendance(
            id=str(uuid.uuid4()),
            staff_id=request.staff_id,
            date=request.date,
            status=request.status,
            check_in=request.check_in,
            check_out=request.check_out,
            hours_worked=request.hours_worked or Decimal("0.00"),
            notes=request.notes,
        )

        # Calculate hours if both times provided
        if request.check_in and request.check_out and not request.hours_worked:
            attendance.hours_worked = attendance.calculate_hours_worked()

        return await self._attendance_repository.create(attendance)
