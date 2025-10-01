"""Staff repository implementations."""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.staff.domain import (
    StaffMember,
    StaffDocument,
    Attendance,
    WorkSchedule,
    EmploymentType,
    StaffStatus,
    DocumentType,
    AttendanceStatus,
    ServiceType,
)
from app.features.staff.ports import (
    IStaffRepository,
    IStaffDocumentRepository,
    IAttendanceRepository,
    IWorkScheduleRepository,
)
from .models import (
    StaffMemberModel,
    StaffDocumentModel,
    AttendanceModel,
    WorkScheduleModel,
)


class StaffRepository(IStaffRepository):
    """Staff member repository implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, staff: StaffMember) -> StaffMember:
        """Create a new staff member."""
        model = self._to_model(staff)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, staff_id: str) -> Optional[StaffMember]:
        """Get staff member by ID."""
        result = await self._session.execute(
            select(StaffMemberModel).where(
                and_(
                    StaffMemberModel.id == staff_id,
                    StaffMemberModel.deleted_at.is_(None),
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_employee_code(self, employee_code: str) -> Optional[StaffMember]:
        """Get staff member by employee code."""
        result = await self._session.execute(
            select(StaffMemberModel).where(
                and_(
                    StaffMemberModel.employee_code == employee_code,
                    StaffMemberModel.deleted_at.is_(None),
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_user_id(self, user_id: str) -> Optional[StaffMember]:
        """Get staff member by user ID."""
        result = await self._session.execute(
            select(StaffMemberModel).where(
                and_(
                    StaffMemberModel.user_id == user_id,
                    StaffMemberModel.deleted_at.is_(None),
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StaffStatus] = None,
        assigned_bay_id: Optional[str] = None,
        assigned_team_id: Optional[str] = None,
    ) -> List[StaffMember]:
        """List staff members with filters."""
        query = select(StaffMemberModel).where(
            StaffMemberModel.deleted_at.is_(None)
        )

        if status:
            query = query.where(StaffMemberModel.status == status.value)

        if assigned_bay_id:
            query = query.where(StaffMemberModel.assigned_bay_id == assigned_bay_id)

        if assigned_team_id:
            query = query.where(StaffMemberModel.assigned_team_id == assigned_team_id)

        query = query.offset(skip).limit(limit).order_by(StaffMemberModel.created_at.desc())

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def count(self, status: Optional[StaffStatus] = None) -> int:
        """Count staff members."""
        from sqlalchemy import func

        query = select(func.count(StaffMemberModel.id)).where(
            StaffMemberModel.deleted_at.is_(None)
        )

        if status:
            query = query.where(StaffMemberModel.status == status.value)

        result = await self._session.execute(query)
        return result.scalar_one()

    async def update(self, staff: StaffMember) -> StaffMember:
        """Update staff member."""
        result = await self._session.execute(
            select(StaffMemberModel).where(StaffMemberModel.id == staff.id)
        )
        model = result.scalar_one()

        # Update fields
        model.first_name = staff.first_name
        model.last_name = staff.last_name
        model.phone = staff.phone
        model.email = staff.email
        model.employment_type = staff.employment_type.value
        model.status = staff.status.value
        model.hourly_rate = staff.hourly_rate
        model.assigned_bay_id = staff.assigned_bay_id
        model.assigned_team_id = staff.assigned_team_id
        model.skills = [skill.value for skill in staff.skills]
        model.total_services_completed = staff.total_services_completed
        model.total_revenue_generated = staff.total_revenue_generated
        model.average_rating = staff.average_rating

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, staff_id: str) -> bool:
        """Soft delete staff member."""
        result = await self._session.execute(
            select(StaffMemberModel).where(StaffMemberModel.id == staff_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.deleted_at = datetime.now()
        await self._session.flush()
        return True

    async def exists(self, staff_id: str) -> bool:
        """Check if staff member exists."""
        from sqlalchemy import func

        result = await self._session.execute(
            select(func.count(StaffMemberModel.id)).where(
                and_(
                    StaffMemberModel.id == staff_id,
                    StaffMemberModel.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one() > 0

    async def employee_code_exists(self, employee_code: str) -> bool:
        """Check if employee code exists."""
        from sqlalchemy import func

        result = await self._session.execute(
            select(func.count(StaffMemberModel.id)).where(
                and_(
                    StaffMemberModel.employee_code == employee_code,
                    StaffMemberModel.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one() > 0

    def _to_domain(self, model: StaffMemberModel) -> StaffMember:
        """Convert model to domain entity."""
        return StaffMember(
            id=model.id,
            user_id=model.user_id,
            employee_code=model.employee_code,
            first_name=model.first_name,
            last_name=model.last_name,
            phone=model.phone,
            email=model.email,
            hire_date=model.hire_date,
            employment_type=EmploymentType(model.employment_type),
            status=StaffStatus(model.status),
            hourly_rate=model.hourly_rate,
            assigned_bay_id=model.assigned_bay_id,
            assigned_team_id=model.assigned_team_id,
            skills=[ServiceType(skill) for skill in model.skills],
            total_services_completed=model.total_services_completed,
            total_revenue_generated=model.total_revenue_generated,
            average_rating=model.average_rating,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def _to_model(self, entity: StaffMember) -> StaffMemberModel:
        """Convert domain entity to model."""
        return StaffMemberModel(
            id=entity.id,
            user_id=entity.user_id,
            employee_code=entity.employee_code,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone=entity.phone,
            email=entity.email,
            hire_date=entity.hire_date,
            employment_type=entity.employment_type.value,
            status=entity.status.value,
            hourly_rate=entity.hourly_rate,
            assigned_bay_id=entity.assigned_bay_id,
            assigned_team_id=entity.assigned_team_id,
            skills=[skill.value for skill in entity.skills],
            total_services_completed=entity.total_services_completed,
            total_revenue_generated=entity.total_revenue_generated,
            average_rating=entity.average_rating,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )


class StaffDocumentRepository(IStaffDocumentRepository):
    """Staff document repository implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, document: StaffDocument) -> StaffDocument:
        """Create a new document."""
        model = self._to_model(document)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, document_id: str) -> Optional[StaffDocument]:
        """Get document by ID."""
        result = await self._session.execute(
            select(StaffDocumentModel).where(StaffDocumentModel.id == document_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_staff(
        self,
        staff_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StaffDocument]:
        """List documents for a staff member."""
        result = await self._session.execute(
            select(StaffDocumentModel)
            .where(StaffDocumentModel.staff_id == staff_id)
            .offset(skip)
            .limit(limit)
            .order_by(StaffDocumentModel.uploaded_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, document: StaffDocument) -> StaffDocument:
        """Update document."""
        result = await self._session.execute(
            select(StaffDocumentModel).where(StaffDocumentModel.id == document.id)
        )
        model = result.scalar_one()

        model.document_name = document.document_name
        model.verified = document.verified
        model.verified_by_user_id = document.verified_by_user_id
        model.verified_at = document.verified_at
        model.notes = document.notes
        model.expires_at = document.expires_at

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, document_id: str) -> bool:
        """Delete document."""
        result = await self._session.execute(
            select(StaffDocumentModel).where(StaffDocumentModel.id == document_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def get_expiring_documents(
        self,
        days_threshold: int = 30,
    ) -> List[StaffDocument]:
        """Get documents expiring within threshold days."""
        from datetime import timedelta

        expiry_date = datetime.now() + timedelta(days=days_threshold)

        result = await self._session.execute(
            select(StaffDocumentModel).where(
                and_(
                    StaffDocumentModel.expires_at.isnot(None),
                    StaffDocumentModel.expires_at <= expiry_date,
                    StaffDocumentModel.verified == True,
                )
            ).order_by(StaffDocumentModel.expires_at.asc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: StaffDocumentModel) -> StaffDocument:
        """Convert model to domain entity."""
        return StaffDocument(
            id=model.id,
            staff_id=model.staff_id,
            document_type=DocumentType(model.document_type),
            document_name=model.document_name,
            file_path=model.file_path,
            uploaded_at=model.uploaded_at,
            expires_at=model.expires_at,
            verified=model.verified,
            verified_by_user_id=model.verified_by_user_id,
            verified_at=model.verified_at,
            notes=model.notes,
        )

    def _to_model(self, entity: StaffDocument) -> StaffDocumentModel:
        """Convert domain entity to model."""
        return StaffDocumentModel(
            id=entity.id,
            staff_id=entity.staff_id,
            document_type=entity.document_type.value,
            document_name=entity.document_name,
            file_path=entity.file_path,
            uploaded_at=entity.uploaded_at,
            expires_at=entity.expires_at,
            verified=entity.verified,
            verified_by_user_id=entity.verified_by_user_id,
            verified_at=entity.verified_at,
            notes=entity.notes,
        )


class AttendanceRepository(IAttendanceRepository):
    """Attendance repository implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, attendance: Attendance) -> Attendance:
        """Create attendance record."""
        model = self._to_model(attendance)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, attendance_id: str) -> Optional[Attendance]:
        """Get attendance by ID."""
        result = await self._session.execute(
            select(AttendanceModel).where(AttendanceModel.id == attendance_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_staff_and_date(
        self,
        staff_id: str,
        attendance_date: date,
    ) -> Optional[Attendance]:
        """Get attendance for staff on specific date."""
        result = await self._session.execute(
            select(AttendanceModel).where(
                and_(
                    AttendanceModel.staff_id == staff_id,
                    AttendanceModel.date == attendance_date,
                )
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_staff(
        self,
        staff_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Attendance]:
        """List attendance records for staff."""
        query = select(AttendanceModel).where(AttendanceModel.staff_id == staff_id)

        if start_date:
            query = query.where(AttendanceModel.date >= start_date)

        if end_date:
            query = query.where(AttendanceModel.date <= end_date)

        query = query.offset(skip).limit(limit).order_by(AttendanceModel.date.desc())

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Attendance]:
        """List all attendance records in date range."""
        result = await self._session.execute(
            select(AttendanceModel)
            .where(
                and_(
                    AttendanceModel.date >= start_date,
                    AttendanceModel.date <= end_date,
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(AttendanceModel.date.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, attendance: Attendance) -> Attendance:
        """Update attendance record."""
        result = await self._session.execute(
            select(AttendanceModel).where(AttendanceModel.id == attendance.id)
        )
        model = result.scalar_one()

        model.status = attendance.status.value
        model.check_in = attendance.check_in
        model.check_out = attendance.check_out
        model.hours_worked = attendance.hours_worked
        model.notes = attendance.notes

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, attendance_id: str) -> bool:
        """Delete attendance record."""
        result = await self._session.execute(
            select(AttendanceModel).where(AttendanceModel.id == attendance_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def get_checked_in_staff(self) -> List[Attendance]:
        """Get all currently checked-in staff."""
        result = await self._session.execute(
            select(AttendanceModel).where(
                and_(
                    AttendanceModel.date == date.today(),
                    AttendanceModel.check_in.isnot(None),
                    AttendanceModel.check_out.is_(None),
                )
            )
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: AttendanceModel) -> Attendance:
        """Convert model to domain entity."""
        return Attendance(
            id=model.id,
            staff_id=model.staff_id,
            date=model.date,
            status=AttendanceStatus(model.status),
            check_in=model.check_in,
            check_out=model.check_out,
            hours_worked=model.hours_worked,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Attendance) -> AttendanceModel:
        """Convert domain entity to model."""
        return AttendanceModel(
            id=entity.id,
            staff_id=entity.staff_id,
            date=entity.date,
            status=entity.status.value,
            check_in=entity.check_in,
            check_out=entity.check_out,
            hours_worked=entity.hours_worked,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class WorkScheduleRepository(IWorkScheduleRepository):
    """Work schedule repository implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, schedule: WorkSchedule) -> WorkSchedule:
        """Create work schedule."""
        model = self._to_model(schedule)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, schedule_id: str) -> Optional[WorkSchedule]:
        """Get schedule by ID."""
        result = await self._session.execute(
            select(WorkScheduleModel).where(WorkScheduleModel.id == schedule_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_by_staff(
        self,
        staff_id: str,
        active_only: bool = True,
    ) -> List[WorkSchedule]:
        """List schedules for staff member."""
        query = select(WorkScheduleModel).where(WorkScheduleModel.staff_id == staff_id)

        if active_only:
            query = query.where(WorkScheduleModel.is_active == True)

        query = query.order_by(WorkScheduleModel.day_of_week.asc())

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def list_by_day(
        self,
        day_of_week: int,
        active_only: bool = True,
    ) -> List[WorkSchedule]:
        """List all schedules for a day of week."""
        query = select(WorkScheduleModel).where(WorkScheduleModel.day_of_week == day_of_week)

        if active_only:
            query = query.where(WorkScheduleModel.is_active == True)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, schedule: WorkSchedule) -> WorkSchedule:
        """Update work schedule."""
        result = await self._session.execute(
            select(WorkScheduleModel).where(WorkScheduleModel.id == schedule.id)
        )
        model = result.scalar_one()

        model.day_of_week = schedule.day_of_week
        model.shift_start = schedule.shift_start
        model.shift_end = schedule.shift_end
        model.break_duration_minutes = schedule.break_duration_minutes
        model.is_active = schedule.is_active
        model.effective_from = schedule.effective_from
        model.effective_until = schedule.effective_until

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def delete(self, schedule_id: str) -> bool:
        """Delete work schedule."""
        result = await self._session.execute(
            select(WorkScheduleModel).where(WorkScheduleModel.id == schedule_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        await self._session.delete(model)
        await self._session.flush()
        return True

    async def get_active_schedules_for_date(
        self,
        check_date: date,
    ) -> List[WorkSchedule]:
        """Get all active schedules for a specific date."""
        day_of_week = check_date.weekday()

        result = await self._session.execute(
            select(WorkScheduleModel).where(
                and_(
                    WorkScheduleModel.day_of_week == day_of_week,
                    WorkScheduleModel.is_active == True,
                    WorkScheduleModel.effective_from <= check_date,
                    or_(
                        WorkScheduleModel.effective_until.is_(None),
                        WorkScheduleModel.effective_until >= check_date,
                    ),
                )
            )
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: WorkScheduleModel) -> WorkSchedule:
        """Convert model to domain entity."""
        return WorkSchedule(
            id=model.id,
            staff_id=model.staff_id,
            day_of_week=model.day_of_week,
            shift_start=model.shift_start,
            shift_end=model.shift_end,
            break_duration_minutes=model.break_duration_minutes,
            is_active=model.is_active,
            effective_from=model.effective_from,
            effective_until=model.effective_until,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: WorkSchedule) -> WorkScheduleModel:
        """Convert domain entity to model."""
        return WorkScheduleModel(
            id=entity.id,
            staff_id=entity.staff_id,
            day_of_week=entity.day_of_week,
            shift_start=entity.shift_start,
            shift_end=entity.shift_end,
            break_duration_minutes=entity.break_duration_minutes,
            is_active=entity.is_active,
            effective_from=entity.effective_from,
            effective_until=entity.effective_until,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
