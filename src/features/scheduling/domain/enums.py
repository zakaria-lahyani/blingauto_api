"""
Scheduling domain enums
"""
from enum import Enum


class DayOfWeek(Enum):
    """Days of the week"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ResourceType(Enum):
    """Types of resources that can be scheduled"""
    WASH_BAY = "wash_bay"
    STAFF_MEMBER = "staff_member"
    EQUIPMENT = "equipment"
    PARKING_SPOT = "parking_spot"


class ResourceStatus(Enum):
    """Status of a resource"""
    AVAILABLE = "available"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class SlotStatus(Enum):
    """Status of a time slot"""
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"


class ScheduleType(Enum):
    """Types of schedules"""
    BUSINESS_HOURS = "business_hours"
    STAFF_SCHEDULE = "staff_schedule"
    RESOURCE_SCHEDULE = "resource_schedule"
    MAINTENANCE_SCHEDULE = "maintenance_schedule"


class ConflictType(Enum):
    """Types of scheduling conflicts"""
    DOUBLE_BOOKING = "double_booking"
    OUTSIDE_BUSINESS_HOURS = "outside_business_hours"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    STAFF_UNAVAILABLE = "staff_unavailable"
    INSUFFICIENT_DURATION = "insufficient_duration"
    MAINTENANCE_WINDOW = "maintenance_window"


class SuggestionStrategy(Enum):
    """Strategies for suggesting appointment times"""
    EARLIEST_AVAILABLE = "earliest_available"
    CLOSEST_TO_REQUESTED = "closest_to_requested"
    MINIMIZE_GAPS = "minimize_gaps"
    LOAD_BALANCING = "load_balancing"
    CUSTOMER_PREFERENCE = "customer_preference"