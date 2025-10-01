"""Staff repository interfaces."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional

from app.features.staff.domain import (
    StaffMember,
    StaffDocument,
    Attendance,
    WorkSchedule,
    StaffStatus,
)


class IStaffRepository(ABC):
    """Interface for staff member repository."""

    @abstractmethod
    async def create(self, staff: StaffMember) -> StaffMember:
        """Create a new staff member."""
        pass

    @abstractmethod
    async def get_by_id(self, staff_id: str) -> Optional[StaffMember]:
        """Get staff member by ID."""
        pass

    @abstractmethod
    async def get_by_employee_code(self, employee_code: str) -> Optional[StaffMember]:
        """Get staff member by employee code."""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[StaffMember]:
        """Get staff member by user ID."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StaffStatus] = None,
        assigned_bay_id: Optional[str] = None,
        assigned_team_id: Optional[str] = None,
    ) -> List[StaffMember]:
        """List staff members with filters."""
        pass

    @abstractmethod
    async def count(self, status: Optional[StaffStatus] = None) -> int:
        """Count staff members."""
        pass

    @abstractmethod
    async def update(self, staff: StaffMember) -> StaffMember:
        """Update staff member."""
        pass

    @abstractmethod
    async def delete(self, staff_id: str) -> bool:
        """Soft delete staff member."""
        pass

    @abstractmethod
    async def exists(self, staff_id: str) -> bool:
        """Check if staff member exists."""
        pass

    @abstractmethod
    async def employee_code_exists(self, employee_code: str) -> bool:
        """Check if employee code exists."""
        pass


class IStaffDocumentRepository(ABC):
    """Interface for staff document repository."""

    @abstractmethod
    async def create(self, document: StaffDocument) -> StaffDocument:
        """Create a new document."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[StaffDocument]:
        """Get document by ID."""
        pass

    @abstractmethod
    async def list_by_staff(
        self,
        staff_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StaffDocument]:
        """List documents for a staff member."""
        pass

    @abstractmethod
    async def update(self, document: StaffDocument) -> StaffDocument:
        """Update document."""
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete document."""
        pass

    @abstractmethod
    async def get_expiring_documents(
        self,
        days_threshold: int = 30,
    ) -> List[StaffDocument]:
        """Get documents expiring within threshold days."""
        pass


class IAttendanceRepository(ABC):
    """Interface for attendance repository."""

    @abstractmethod
    async def create(self, attendance: Attendance) -> Attendance:
        """Create attendance record."""
        pass

    @abstractmethod
    async def get_by_id(self, attendance_id: str) -> Optional[Attendance]:
        """Get attendance by ID."""
        pass

    @abstractmethod
    async def get_by_staff_and_date(
        self,
        staff_id: str,
        attendance_date: date,
    ) -> Optional[Attendance]:
        """Get attendance for staff on specific date."""
        pass

    @abstractmethod
    async def list_by_staff(
        self,
        staff_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Attendance]:
        """List attendance records for staff."""
        pass

    @abstractmethod
    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Attendance]:
        """List all attendance records in date range."""
        pass

    @abstractmethod
    async def update(self, attendance: Attendance) -> Attendance:
        """Update attendance record."""
        pass

    @abstractmethod
    async def delete(self, attendance_id: str) -> bool:
        """Delete attendance record."""
        pass

    @abstractmethod
    async def get_checked_in_staff(self) -> List[Attendance]:
        """Get all currently checked-in staff."""
        pass


class IWorkScheduleRepository(ABC):
    """Interface for work schedule repository."""

    @abstractmethod
    async def create(self, schedule: WorkSchedule) -> WorkSchedule:
        """Create work schedule."""
        pass

    @abstractmethod
    async def get_by_id(self, schedule_id: str) -> Optional[WorkSchedule]:
        """Get schedule by ID."""
        pass

    @abstractmethod
    async def list_by_staff(
        self,
        staff_id: str,
        active_only: bool = True,
    ) -> List[WorkSchedule]:
        """List schedules for staff member."""
        pass

    @abstractmethod
    async def list_by_day(
        self,
        day_of_week: int,
        active_only: bool = True,
    ) -> List[WorkSchedule]:
        """List all schedules for a day of week."""
        pass

    @abstractmethod
    async def update(self, schedule: WorkSchedule) -> WorkSchedule:
        """Update work schedule."""
        pass

    @abstractmethod
    async def delete(self, schedule_id: str) -> bool:
        """Delete work schedule."""
        pass

    @abstractmethod
    async def get_active_schedules_for_date(
        self,
        check_date: date,
    ) -> List[WorkSchedule]:
        """Get all active schedules for a specific date."""
        pass
