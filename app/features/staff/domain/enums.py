"""Staff domain enumerations."""

from enum import Enum


class EmploymentType(str, Enum):
    """Employment type classification."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACTOR = "contractor"
    TEMPORARY = "temporary"


class StaffStatus(str, Enum):
    """Staff member status."""

    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class DocumentType(str, Enum):
    """Staff document types."""

    ID_CARD = "id_card"
    DRIVERS_LICENSE = "drivers_license"
    CERTIFICATE = "certificate"
    CONTRACT = "contract"
    TRAINING_RECORD = "training_record"
    BACKGROUND_CHECK = "background_check"
    OTHER = "other"


class AttendanceStatus(str, Enum):
    """Attendance record status."""

    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"
    SICK_LEAVE = "sick_leave"
    HOLIDAY = "holiday"


class ServiceType(str, Enum):
    """Types of services staff can perform."""

    BASIC_WASH = "basic_wash"
    PREMIUM_WASH = "premium_wash"
    DETAILING = "detailing"
    WAX_POLISH = "wax_polish"
    INTERIOR_CLEANING = "interior_cleaning"
    ENGINE_CLEANING = "engine_cleaning"
    MOBILE_SERVICE = "mobile_service"
