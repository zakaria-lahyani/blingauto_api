"""Staff ports layer - interfaces and abstract base classes."""

from .repositories import (
    IStaffRepository,
    IAttendanceRepository,
    IWorkScheduleRepository,
    IStaffDocumentRepository,
)
from .services import IFileStorageService

__all__ = [
    # Repositories
    "IStaffRepository",
    "IAttendanceRepository",
    "IWorkScheduleRepository",
    "IStaffDocumentRepository",
    # Services
    "IFileStorageService",
]
