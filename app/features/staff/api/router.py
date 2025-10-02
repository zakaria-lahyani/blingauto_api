"""Staff API router."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from app.shared.auth import get_current_user, CurrentUser, require_any_role

# Cross-feature import exception (ADR-001: Shared Auth Enums)
# UserRole is an immutable enum used only for authorization checks in API layer
from app.features.auth.domain import UserRole

from .schemas import (
    # Staff
    CreateStaffSchema,
    UpdateStaffSchema,
    StaffSchema,
    ListStaffSchema,
    StaffQueryParams,
    # Documents
    StaffDocumentSchema,
    ListDocumentsSchema,
    # Attendance
    CheckInResponseSchema,
    CheckOutResponseSchema,
    RecordAttendanceSchema,
    AttendanceSchema,
    AttendanceReportSchema,
    AttendanceQueryParams,
    # Schedules
    CreateScheduleSchema,
    UpdateScheduleSchema,
    WorkScheduleSchema,
    ListSchedulesSchema,
)
from .dependencies import (
    get_create_staff_use_case,
    get_update_staff_use_case,
    get_get_staff_use_case,
    get_list_staff_use_case,
    get_deactivate_staff_use_case,
    get_check_in_staff_use_case,
    get_check_out_staff_use_case,
    get_record_attendance_use_case,
    get_attendance_report_use_case,
    get_upload_document_use_case,
    get_delete_document_use_case,
    get_verify_document_use_case,
    get_list_documents_use_case,
    get_create_schedule_use_case,
    get_update_schedule_use_case,
    get_staff_schedule_use_case,
    get_file_storage_service,
)
from app.features.staff.use_cases import (
    CreateStaffRequest,
    UpdateStaffRequest,
    ListStaffRequest,
    RecordAttendanceRequest,
    UploadDocumentRequest,
    CreateScheduleRequest,
    UpdateScheduleRequest,
    GetAttendanceReportRequest,
)

router = APIRouter()


# ============================================================================
# Staff Management Endpoints
# ============================================================================

@router.post(
    "/",
    response_model=StaffSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Staff Member",
    description="Create a new staff member. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def create_staff(
    data: CreateStaffSchema,
    use_case=Depends(get_create_staff_use_case),
) -> StaffSchema:
    """Create a new staff member."""
    try:
        request = CreateStaffRequest(
            user_id=data.user_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            hire_date=data.hire_date,
            employment_type=data.employment_type,
            hourly_rate=data.hourly_rate,
            assigned_bay_id=data.assigned_bay_id,
            assigned_team_id=data.assigned_team_id,
            skills=data.skills or [],
        )

        staff = await use_case.execute(request)

        return StaffSchema(
            id=staff.id,
            user_id=staff.user_id,
            employee_code=staff.employee_code,
            first_name=staff.first_name,
            last_name=staff.last_name,
            full_name=staff.full_name,
            phone=staff.phone,
            email=staff.email,
            hire_date=staff.hire_date,
            employment_type=staff.employment_type,
            status=staff.status,
            hourly_rate=staff.hourly_rate,
            assigned_bay_id=staff.assigned_bay_id,
            assigned_team_id=staff.assigned_team_id,
            skills=staff.skills,
            total_services_completed=staff.total_services_completed,
            total_revenue_generated=staff.total_revenue_generated,
            average_rating=staff.average_rating,
            is_active=staff.is_active,
            created_at=staff.created_at,
            updated_at=staff.updated_at,
        )

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/",
    response_model=ListStaffSchema,
    summary="List Staff Members",
    description="List all staff members with optional filters. Requires Admin, Manager, or Washer role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.WASHER.value))],
)
async def list_staff(
    params: StaffQueryParams = Depends(),
    use_case=Depends(get_list_staff_use_case),
    staff_repo=Depends(lambda: None),  # Will be injected in dependencies
) -> ListStaffSchema:
    """List staff members with filters."""
    try:
        request = ListStaffRequest(
            skip=params.skip,
            limit=params.limit,
            status=params.status,
            assigned_bay_id=params.assigned_bay_id,
            assigned_team_id=params.assigned_team_id,
        )

        staff_list = await use_case.execute(request)

        # Get total count (simplified - in production, add count to use case)
        total = len(staff_list)

        return ListStaffSchema(
            items=[
                StaffSchema(
                    id=s.id,
                    user_id=s.user_id,
                    employee_code=s.employee_code,
                    first_name=s.first_name,
                    last_name=s.last_name,
                    full_name=s.full_name,
                    phone=s.phone,
                    email=s.email,
                    hire_date=s.hire_date,
                    employment_type=s.employment_type,
                    status=s.status,
                    hourly_rate=s.hourly_rate,
                    assigned_bay_id=s.assigned_bay_id,
                    assigned_team_id=s.assigned_team_id,
                    skills=s.skills,
                    total_services_completed=s.total_services_completed,
                    total_revenue_generated=s.total_revenue_generated,
                    average_rating=s.average_rating,
                    is_active=s.is_active,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in staff_list
            ],
            total=total,
            skip=params.skip,
            limit=params.limit,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{staff_id}",
    response_model=StaffSchema,
    summary="Get Staff Member",
    description="Get staff member details by ID.",
)
async def get_staff(
    staff_id: str,
    current_user: CurrentUser,
    use_case=Depends(get_get_staff_use_case),
) -> StaffSchema:
    """Get staff member by ID."""
    try:
        staff = await use_case.execute(staff_id)

        return StaffSchema(
            id=staff.id,
            user_id=staff.user_id,
            employee_code=staff.employee_code,
            first_name=staff.first_name,
            last_name=staff.last_name,
            full_name=staff.full_name,
            phone=staff.phone,
            email=staff.email,
            hire_date=staff.hire_date,
            employment_type=staff.employment_type,
            status=staff.status,
            hourly_rate=staff.hourly_rate,
            assigned_bay_id=staff.assigned_bay_id,
            assigned_team_id=staff.assigned_team_id,
            skills=staff.skills,
            total_services_completed=staff.total_services_completed,
            total_revenue_generated=staff.total_revenue_generated,
            average_rating=staff.average_rating,
            is_active=staff.is_active,
            created_at=staff.created_at,
            updated_at=staff.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{staff_id}",
    response_model=StaffSchema,
    summary="Update Staff Member",
    description="Update staff member information. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def update_staff(
    staff_id: str,
    data: UpdateStaffSchema,
    use_case=Depends(get_update_staff_use_case),
) -> StaffSchema:
    """Update staff member."""
    try:
        request = UpdateStaffRequest(
            staff_id=staff_id,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            email=data.email,
            employment_type=data.employment_type,
            status=data.status,
            hourly_rate=data.hourly_rate,
            assigned_bay_id=data.assigned_bay_id,
            assigned_team_id=data.assigned_team_id,
            skills=data.skills,
        )

        staff = await use_case.execute(request)

        return StaffSchema(
            id=staff.id,
            user_id=staff.user_id,
            employee_code=staff.employee_code,
            first_name=staff.first_name,
            last_name=staff.last_name,
            full_name=staff.full_name,
            phone=staff.phone,
            email=staff.email,
            hire_date=staff.hire_date,
            employment_type=staff.employment_type,
            status=staff.status,
            hourly_rate=staff.hourly_rate,
            assigned_bay_id=staff.assigned_bay_id,
            assigned_team_id=staff.assigned_team_id,
            skills=staff.skills,
            total_services_completed=staff.total_services_completed,
            total_revenue_generated=staff.total_revenue_generated,
            average_rating=staff.average_rating,
            is_active=staff.is_active,
            created_at=staff.created_at,
            updated_at=staff.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate Staff Member",
    description="Deactivate (soft delete) a staff member. Requires Admin role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value))],
)
async def deactivate_staff(
    staff_id: str,
    use_case=Depends(get_deactivate_staff_use_case),
):
    """Deactivate staff member."""
    try:
        await use_case.execute(staff_id)
        return None

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Document Management Endpoints
# ============================================================================

@router.post(
    "/{staff_id}/documents",
    response_model=StaffDocumentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Staff Document",
    description="Upload a document for staff member (ID, certificate, contract, etc.).",
)
async def upload_document(
    staff_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_name: str = Form(...),
    expires_at: str = Form(None),
    notes: str = Form(None),
    use_case=Depends(get_upload_document_use_case),
    file_storage=Depends(get_file_storage_service),
) -> StaffDocumentSchema:
    """Upload staff document."""
    try:
        from datetime import datetime
        from app.features.staff.domain import DocumentType

        request = UploadDocumentRequest(
            staff_id=staff_id,
            document_type=DocumentType(document_type),
            document_name=document_name,
            file_content=file.file,
            file_name=file.filename,
            content_type=file.content_type,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            notes=notes,
        )

        document = await use_case.execute(request)
        file_url = await file_storage.get_file_url(document.file_path)

        return StaffDocumentSchema(
            id=document.id,
            staff_id=document.staff_id,
            document_type=document.document_type,
            document_name=document.document_name,
            file_path=document.file_path,
            file_url=file_url,
            uploaded_at=document.uploaded_at,
            expires_at=document.expires_at,
            is_expired=document.is_expired,
            days_until_expiry=document.days_until_expiry,
            verified=document.verified,
            verified_by_user_id=document.verified_by_user_id,
            verified_at=document.verified_at,
            notes=document.notes,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{staff_id}/documents",
    response_model=ListDocumentsSchema,
    summary="List Staff Documents",
    description="Get all documents for a staff member.",
)
async def list_documents(
    staff_id: str,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    use_case=Depends(get_list_documents_use_case),
    file_storage=Depends(get_file_storage_service),
) -> ListDocumentsSchema:
    """List staff documents."""
    try:
        documents = await use_case.execute(staff_id, skip, limit)

        items = []
        for doc in documents:
            file_url = await file_storage.get_file_url(doc.file_path)
            items.append(
                StaffDocumentSchema(
                    id=doc.id,
                    staff_id=doc.staff_id,
                    document_type=doc.document_type,
                    document_name=doc.document_name,
                    file_path=doc.file_path,
                    file_url=file_url,
                    uploaded_at=doc.uploaded_at,
                    expires_at=doc.expires_at,
                    is_expired=doc.is_expired,
                    days_until_expiry=doc.days_until_expiry,
                    verified=doc.verified,
                    verified_by_user_id=doc.verified_by_user_id,
                    verified_at=doc.verified_at,
                    notes=doc.notes,
                )
            )

        return ListDocumentsSchema(items=items, total=len(items))

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{staff_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Staff Document",
    description="Delete a staff document.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def delete_document(
    staff_id: str,
    document_id: str,
    use_case=Depends(get_delete_document_use_case),
):
    """Delete staff document."""
    try:
        await use_case.execute(document_id)
        return None

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{staff_id}/documents/{document_id}/verify",
    response_model=StaffDocumentSchema,
    summary="Verify Staff Document",
    description="Mark document as verified. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def verify_document(
    staff_id: str,
    document_id: str,
    current_user: CurrentUser,
    use_case=Depends(get_verify_document_use_case),
    file_storage=Depends(get_file_storage_service),
) -> StaffDocumentSchema:
    """Verify staff document."""
    try:
        document = await use_case.execute(document_id, current_user.id)
        file_url = await file_storage.get_file_url(document.file_path)

        return StaffDocumentSchema(
            id=document.id,
            staff_id=document.staff_id,
            document_type=document.document_type,
            document_name=document.document_name,
            file_path=document.file_path,
            file_url=file_url,
            uploaded_at=document.uploaded_at,
            expires_at=document.expires_at,
            is_expired=document.is_expired,
            days_until_expiry=document.days_until_expiry,
            verified=document.verified,
            verified_by_user_id=document.verified_by_user_id,
            verified_at=document.verified_at,
            notes=document.notes,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Attendance Management Endpoints
# ============================================================================

@router.post(
    "/{staff_id}/attendance/check-in",
    response_model=CheckInResponseSchema,
    summary="Check In Staff",
    description="Check in staff member for the day.",
)
async def check_in(
    staff_id: str,
    current_user: CurrentUser,
    use_case=Depends(get_check_in_staff_use_case),
) -> CheckInResponseSchema:
    """Check in staff member."""
    try:
        attendance = await use_case.execute(staff_id)

        return CheckInResponseSchema(
            attendance_id=attendance.id,
            staff_id=attendance.staff_id,
            date=attendance.date,
            check_in=attendance.check_in,
            status=attendance.status,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/{staff_id}/attendance/check-out",
    response_model=CheckOutResponseSchema,
    summary="Check Out Staff",
    description="Check out staff member for the day.",
)
async def check_out(
    staff_id: str,
    current_user: CurrentUser,
    use_case=Depends(get_check_out_staff_use_case),
) -> CheckOutResponseSchema:
    """Check out staff member."""
    try:
        attendance = await use_case.execute(staff_id)

        return CheckOutResponseSchema(
            attendance_id=attendance.id,
            staff_id=attendance.staff_id,
            date=attendance.date,
            check_in=attendance.check_in,
            check_out=attendance.check_out,
            hours_worked=attendance.hours_worked,
            status=attendance.status,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/attendance",
    response_model=AttendanceSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Record Attendance",
    description="Manually record attendance (for managers/admins).",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def record_attendance(
    data: RecordAttendanceSchema,
    use_case=Depends(get_record_attendance_use_case),
) -> AttendanceSchema:
    """Record attendance manually."""
    try:
        request = RecordAttendanceRequest(
            staff_id=data.staff_id,
            date=data.date,
            status=data.status,
            check_in=data.check_in,
            check_out=data.check_out,
            hours_worked=data.hours_worked,
            notes=data.notes,
        )

        attendance = await use_case.execute(request)

        return AttendanceSchema(
            id=attendance.id,
            staff_id=attendance.staff_id,
            date=attendance.date,
            status=attendance.status,
            check_in=attendance.check_in,
            check_out=attendance.check_out,
            hours_worked=attendance.hours_worked,
            is_checked_in=attendance.is_checked_in,
            notes=attendance.notes,
            created_at=attendance.created_at,
            updated_at=attendance.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/{staff_id}/attendance",
    response_model=AttendanceReportSchema,
    summary="Get Attendance Report",
    description="Get attendance history and statistics for a staff member.",
)
async def get_attendance_report(
    staff_id: str,
    current_user: CurrentUser,
    params: AttendanceQueryParams = Depends(),
    use_case=Depends(get_attendance_report_use_case),
) -> AttendanceReportSchema:
    """Get attendance report."""
    try:
        from decimal import Decimal
        from app.features.staff.domain import AttendanceStatus as AS

        request = GetAttendanceReportRequest(
            staff_id=staff_id,
            start_date=params.start_date,
            end_date=params.end_date,
            skip=params.skip,
            limit=params.limit,
        )

        attendance_list = await use_case.execute(request)

        # Calculate statistics
        total_days = len(attendance_list)
        present_days = len([a for a in attendance_list if a.status == AS.PRESENT])
        absent_days = len([a for a in attendance_list if a.status == AS.ABSENT])
        late_days = len([a for a in attendance_list if a.status == AS.LATE])
        total_hours = sum(a.hours_worked for a in attendance_list)
        avg_hours = total_hours / total_days if total_days > 0 else Decimal("0.00")
        attendance_rate = (Decimal(present_days) / Decimal(total_days) * Decimal("100")) if total_days > 0 else Decimal("0.00")

        return AttendanceReportSchema(
            items=[
                AttendanceSchema(
                    id=a.id,
                    staff_id=a.staff_id,
                    date=a.date,
                    status=a.status,
                    check_in=a.check_in,
                    check_out=a.check_out,
                    hours_worked=a.hours_worked,
                    is_checked_in=a.is_checked_in,
                    notes=a.notes,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                )
                for a in attendance_list
            ],
            total_days=total_days,
            present_days=present_days,
            absent_days=absent_days,
            late_days=late_days,
            total_hours=total_hours,
            average_hours_per_day=avg_hours,
            attendance_rate=attendance_rate,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Schedule Management Endpoints
# ============================================================================

@router.post(
    "/{staff_id}/schedule",
    response_model=WorkScheduleSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create Work Schedule",
    description="Create a work schedule for staff member. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def create_schedule(
    staff_id: str,
    data: CreateScheduleSchema,
    use_case=Depends(get_create_schedule_use_case),
) -> WorkScheduleSchema:
    """Create work schedule."""
    try:
        request = CreateScheduleRequest(
            staff_id=staff_id,
            day_of_week=data.day_of_week,
            shift_start=data.shift_start,
            shift_end=data.shift_end,
            break_duration_minutes=data.break_duration_minutes,
            effective_from=data.effective_from,
            effective_until=data.effective_until,
        )

        schedule = await use_case.execute(request)

        return WorkScheduleSchema(
            id=schedule.id,
            staff_id=schedule.staff_id,
            day_of_week=schedule.day_of_week,
            day_name=schedule.day_name,
            shift_start=schedule.shift_start,
            shift_end=schedule.shift_end,
            break_duration_minutes=schedule.break_duration_minutes,
            shift_duration_hours=schedule.shift_duration_hours,
            is_active=schedule.is_active,
            effective_from=schedule.effective_from,
            effective_until=schedule.effective_until,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{staff_id}/schedule",
    response_model=ListSchedulesSchema,
    summary="Get Staff Schedule",
    description="Get work schedule for a staff member.",
)
async def get_schedule(
    staff_id: str,
    current_user: CurrentUser,
    active_only: bool = True,
    use_case=Depends(get_staff_schedule_use_case),
) -> ListSchedulesSchema:
    """Get staff schedule."""
    try:
        schedules = await use_case.execute(staff_id, active_only)

        return ListSchedulesSchema(
            items=[
                WorkScheduleSchema(
                    id=s.id,
                    staff_id=s.staff_id,
                    day_of_week=s.day_of_week,
                    day_name=s.day_name,
                    shift_start=s.shift_start,
                    shift_end=s.shift_end,
                    break_duration_minutes=s.break_duration_minutes,
                    shift_duration_hours=s.shift_duration_hours,
                    is_active=s.is_active,
                    effective_from=s.effective_from,
                    effective_until=s.effective_until,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in schedules
            ],
            total=len(schedules),
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/{staff_id}/schedule/{schedule_id}",
    response_model=WorkScheduleSchema,
    summary="Update Work Schedule",
    description="Update a work schedule. Requires Admin or Manager role.",
    dependencies=[Depends(require_any_role(UserRole.ADMIN.value, UserRole.MANAGER.value))],
)
async def update_schedule(
    staff_id: str,
    schedule_id: str,
    data: UpdateScheduleSchema,
    use_case=Depends(get_update_schedule_use_case),
) -> WorkScheduleSchema:
    """Update work schedule."""
    try:
        request = UpdateScheduleRequest(
            schedule_id=schedule_id,
            shift_start=data.shift_start,
            shift_end=data.shift_end,
            break_duration_minutes=data.break_duration_minutes,
            is_active=data.is_active,
            effective_until=data.effective_until,
        )

        schedule = await use_case.execute(request)

        return WorkScheduleSchema(
            id=schedule.id,
            staff_id=schedule.staff_id,
            day_of_week=schedule.day_of_week,
            day_name=schedule.day_name,
            shift_start=schedule.shift_start,
            shift_end=schedule.shift_end,
            break_duration_minutes=schedule.break_duration_minutes,
            shift_duration_hours=schedule.shift_duration_hours,
            is_active=schedule.is_active,
            effective_from=schedule.effective_from,
            effective_until=schedule.effective_until,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
