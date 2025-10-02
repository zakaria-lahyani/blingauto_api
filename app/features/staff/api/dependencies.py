"""Staff API dependencies - dependency injection setup."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.features.staff.adapters import (
    StaffRepository,
    StaffDocumentRepository,
    AttendanceRepository,
    WorkScheduleRepository,
    LocalFileStorageService,
)
from app.features.staff.ports import (
    IStaffRepository,
    IStaffDocumentRepository,
    IAttendanceRepository,
    IWorkScheduleRepository,
    IFileStorageService,
)
from app.features.staff.use_cases import (
    CreateStaffUseCase,
    UpdateStaffUseCase,
    GetStaffUseCase,
    ListStaffUseCase,
    DeactivateStaffUseCase,
    CheckInStaffUseCase,
    CheckOutStaffUseCase,
    RecordAttendanceUseCase,
    GetAttendanceReportUseCase,
    UploadDocumentUseCase,
    DeleteDocumentUseCase,
    VerifyDocumentUseCase,
    ListDocumentsUseCase,
    CreateScheduleUseCase,
    UpdateScheduleUseCase,
    GetStaffScheduleUseCase,
)


# ============================================================================
# Repository Dependencies
# ============================================================================

async def get_staff_repository(
    session: AsyncSession = Depends(get_db),
) -> IStaffRepository:
    """Get staff repository instance."""
    return StaffRepository(session)


async def get_staff_document_repository(
    session: AsyncSession = Depends(get_db),
) -> IStaffDocumentRepository:
    """Get staff document repository instance."""
    return StaffDocumentRepository(session)


async def get_attendance_repository(
    session: AsyncSession = Depends(get_db),
) -> IAttendanceRepository:
    """Get attendance repository instance."""
    return AttendanceRepository(session)


async def get_work_schedule_repository(
    session: AsyncSession = Depends(get_db),
) -> IWorkScheduleRepository:
    """Get work schedule repository instance."""
    return WorkScheduleRepository(session)


# ============================================================================
# Service Dependencies
# ============================================================================

async def get_file_storage_service() -> IFileStorageService:
    """Get file storage service instance."""
    return LocalFileStorageService(base_path="uploads")


# ============================================================================
# Staff Management Use Case Dependencies
# ============================================================================

async def get_create_staff_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
) -> CreateStaffUseCase:
    """Get create staff use case."""
    return CreateStaffUseCase(staff_repo)


async def get_update_staff_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
) -> UpdateStaffUseCase:
    """Get update staff use case."""
    return UpdateStaffUseCase(staff_repo)


async def get_get_staff_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
) -> GetStaffUseCase:
    """Get staff use case."""
    return GetStaffUseCase(staff_repo)


async def get_list_staff_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
) -> ListStaffUseCase:
    """Get list staff use case."""
    return ListStaffUseCase(staff_repo)


async def get_deactivate_staff_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
) -> DeactivateStaffUseCase:
    """Get deactivate staff use case."""
    return DeactivateStaffUseCase(staff_repo)


# ============================================================================
# Attendance Use Case Dependencies
# ============================================================================

async def get_check_in_staff_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    attendance_repo: IAttendanceRepository = Depends(get_attendance_repository),
) -> CheckInStaffUseCase:
    """Get check-in staff use case."""
    return CheckInStaffUseCase(staff_repo, attendance_repo)


async def get_check_out_staff_use_case(
    attendance_repo: IAttendanceRepository = Depends(get_attendance_repository),
) -> CheckOutStaffUseCase:
    """Get check-out staff use case."""
    return CheckOutStaffUseCase(attendance_repo)


async def get_record_attendance_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    attendance_repo: IAttendanceRepository = Depends(get_attendance_repository),
) -> RecordAttendanceUseCase:
    """Get record attendance use case."""
    return RecordAttendanceUseCase(staff_repo, attendance_repo)


async def get_attendance_report_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    attendance_repo: IAttendanceRepository = Depends(get_attendance_repository),
) -> GetAttendanceReportUseCase:
    """Get attendance report use case."""
    return GetAttendanceReportUseCase(staff_repo, attendance_repo)


# ============================================================================
# Document Use Case Dependencies
# ============================================================================

async def get_upload_document_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    document_repo: IStaffDocumentRepository = Depends(get_staff_document_repository),
    file_storage: IFileStorageService = Depends(get_file_storage_service),
) -> UploadDocumentUseCase:
    """Get upload document use case."""
    return UploadDocumentUseCase(staff_repo, document_repo, file_storage)


async def get_delete_document_use_case(
    document_repo: IStaffDocumentRepository = Depends(get_staff_document_repository),
    file_storage: IFileStorageService = Depends(get_file_storage_service),
) -> DeleteDocumentUseCase:
    """Get delete document use case."""
    return DeleteDocumentUseCase(document_repo, file_storage)


async def get_verify_document_use_case(
    document_repo: IStaffDocumentRepository = Depends(get_staff_document_repository),
) -> VerifyDocumentUseCase:
    """Get verify document use case."""
    return VerifyDocumentUseCase(document_repo)


async def get_list_documents_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    document_repo: IStaffDocumentRepository = Depends(get_staff_document_repository),
) -> ListDocumentsUseCase:
    """Get list documents use case."""
    return ListDocumentsUseCase(staff_repo, document_repo)


# ============================================================================
# Schedule Use Case Dependencies
# ============================================================================

async def get_create_schedule_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    schedule_repo: IWorkScheduleRepository = Depends(get_work_schedule_repository),
) -> CreateScheduleUseCase:
    """Get create schedule use case."""
    return CreateScheduleUseCase(staff_repo, schedule_repo)


async def get_update_schedule_use_case(
    schedule_repo: IWorkScheduleRepository = Depends(get_work_schedule_repository),
    staff_repo: IStaffRepository = Depends(get_staff_repository),
) -> UpdateScheduleUseCase:
    """Get update schedule use case."""
    return UpdateScheduleUseCase(schedule_repo, staff_repo)


async def get_staff_schedule_use_case(
    staff_repo: IStaffRepository = Depends(get_staff_repository),
    schedule_repo: IWorkScheduleRepository = Depends(get_work_schedule_repository),
) -> GetStaffScheduleUseCase:
    """Get staff schedule use case."""
    return GetStaffScheduleUseCase(staff_repo, schedule_repo)
