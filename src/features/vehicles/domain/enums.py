"""
Vehicle domain enums
"""
from enum import Enum


class VehicleStatus(Enum):
    """Vehicle status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"