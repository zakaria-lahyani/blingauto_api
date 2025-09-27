"""
Service domain enums
"""
from enum import Enum


class ServiceStatus(Enum):
    """Service status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class CategoryStatus(Enum):
    """Category status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ServiceSortBy(Enum):
    """Service sorting options"""
    NAME = "name"
    PRICE = "price"
    DURATION = "duration"
    CREATED_AT = "created_at"
    POPULARITY = "popularity"


class CategorySortBy(Enum):
    """Category sorting options"""
    NAME = "name"
    CREATED_AT = "created_at"