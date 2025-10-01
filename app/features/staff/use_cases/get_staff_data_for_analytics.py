"""Get staff data for analytics - Public use case."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from app.features.staff.ports.repositories import (
    IStaffRepository,
    IAttendanceRepository,
)


@dataclass
class StaffWorkData:
    """Work data for a staff member."""

    staff_id: str
    staff_name: str
    date: date
    hours_worked: Decimal
    services_completed: int
    revenue_generated: Decimal
    status: str


@dataclass
class AttendanceData:
    """Attendance data for a staff member."""

    staff_id: str
    date: date
    status: str
    hours_worked: Decimal


@dataclass
class GetStaffWorkDataRequest:
    """Request for staff work data."""

    staff_id: str
    start_date: date
    end_date: date


@dataclass
class GetAttendanceDataRequest:
    """Request for attendance data."""

    staff_id: str
    start_date: date
    end_date: date


class GetStaffWorkDataUseCase:
    """Public use case for analytics to get staff work data."""

    def __init__(
        self,
        staff_repository: IStaffRepository,
        attendance_repository: IAttendanceRepository,
    ):
        self._staff_repo = staff_repository
        self._attendance_repo = attendance_repository

    async def execute(self, request: GetStaffWorkDataRequest) -> StaffWorkData:
        """Get aggregated work data for a staff member."""
        # Get staff info
        staff = await self._staff_repo.get_by_id(request.staff_id)
        if not staff:
            raise LookupError(f"Staff member {request.staff_id} not found")

        # Get attendance records
        all_attendance = await self._attendance_repo.list_all()
        period_attendance = [
            a
            for a in all_attendance
            if a.staff_member_id == request.staff_id
            and request.start_date <= a.date <= request.end_date
        ]

        # Aggregate data
        total_hours = sum(
            a.hours_worked for a in period_attendance if a.hours_worked
        )

        # Note: services_completed and revenue_generated would need
        # booking assignments to calculate - simplified here
        return StaffWorkData(
            staff_id=staff.id,
            staff_name=f"{staff.first_name} {staff.last_name}",
            date=request.end_date,
            hours_worked=total_hours,
            services_completed=0,  # Would need booking data
            revenue_generated=Decimal("0"),  # Would need booking data
            status=staff.status,
        )


class GetAttendanceDataUseCase:
    """Public use case for analytics to get attendance data."""

    def __init__(self, attendance_repository: IAttendanceRepository):
        self._repository = attendance_repository

    async def execute(
        self, request: GetAttendanceDataRequest
    ) -> List[AttendanceData]:
        """Get attendance records for a staff member."""
        all_attendance = await self._repository.list_all()

        # Filter by staff and date range
        period_attendance = [
            a
            for a in all_attendance
            if a.staff_member_id == request.staff_id
            and request.start_date <= a.date <= request.end_date
        ]

        return [
            AttendanceData(
                staff_id=a.staff_member_id,
                date=a.date,
                status=a.status,
                hours_worked=a.hours_worked or Decimal("0"),
            )
            for a in period_attendance
        ]


class GetActiveStaffIdsUseCase:
    """Public use case for analytics to get all active staff IDs."""

    def __init__(self, staff_repository: IStaffRepository):
        self._repository = staff_repository

    async def execute(self) -> List[str]:
        """Get IDs of all active staff members."""
        all_staff = await self._repository.list_all()
        return [s.id for s in all_staff if s.status == "active"]
