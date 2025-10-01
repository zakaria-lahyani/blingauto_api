"""Staff use cases - application logic."""

# Staff Management
from .create_staff import CreateStaffUseCase, CreateStaffRequest
from .update_staff import UpdateStaffUseCase, UpdateStaffRequest
from .get_staff import GetStaffUseCase
from .list_staff import ListStaffUseCase, ListStaffRequest
from .deactivate_staff import DeactivateStaffUseCase

# Document Management
from .upload_document import UploadDocumentUseCase, UploadDocumentRequest
from .delete_document import DeleteDocumentUseCase
from .verify_document import VerifyDocumentUseCase
from .list_documents import ListDocumentsUseCase

# Attendance Management
from .check_in_staff import CheckInStaffUseCase
from .check_out_staff import CheckOutStaffUseCase
from .record_attendance import RecordAttendanceUseCase, RecordAttendanceRequest
from .get_attendance_report import GetAttendanceReportUseCase, GetAttendanceReportRequest

# Schedule Management
from .create_schedule import CreateScheduleUseCase, CreateScheduleRequest
from .update_schedule import UpdateScheduleUseCase, UpdateScheduleRequest
from .get_staff_schedule import GetStaffScheduleUseCase

__all__ = [
    # Staff Management
    "CreateStaffUseCase",
    "CreateStaffRequest",
    "UpdateStaffUseCase",
    "UpdateStaffRequest",
    "GetStaffUseCase",
    "ListStaffUseCase",
    "ListStaffRequest",
    "DeactivateStaffUseCase",
    # Document Management
    "UploadDocumentUseCase",
    "UploadDocumentRequest",
    "DeleteDocumentUseCase",
    "VerifyDocumentUseCase",
    "ListDocumentsUseCase",
    # Attendance Management
    "CheckInStaffUseCase",
    "CheckOutStaffUseCase",
    "RecordAttendanceUseCase",
    "RecordAttendanceRequest",
    "GetAttendanceReportUseCase",
    "GetAttendanceReportRequest",
    # Schedule Management
    "CreateScheduleUseCase",
    "CreateScheduleRequest",
    "UpdateScheduleUseCase",
    "UpdateScheduleRequest",
    "GetStaffScheduleUseCase",
]
