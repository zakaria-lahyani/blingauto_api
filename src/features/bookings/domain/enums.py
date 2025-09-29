"""
Booking domain enums
"""
from enum import Enum


class BookingStatus(Enum):
    """Booking status enumeration with lifecycle management"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class CancellationPolicy(Enum):
    """Cancellation fee policy based on notice period"""
    FREE = "free"           # >24 hours notice
    QUARTER_FEE = "quarter" # 6-24 hours notice  
    HALF_FEE = "half"       # 2-6 hours notice
    FULL_FEE = "full"       # <2 hours notice or no-show


class BookingSortBy(Enum):
    """Booking sorting options"""
    CREATED_AT = "created_at"
    SCHEDULED_AT = "scheduled_at"
    TOTAL_PRICE = "total_price"
    STATUS = "status"
    CUSTOMER_NAME = "customer_name"


class BookingType(Enum):
    """Booking type enumeration - defines where the service takes place and resource allocation"""
    IN_HOME = "in_home"      # Customer comes to the facility (uses wash bays)
    MOBILE = "mobile"        # Service team goes to customer location (uses mobile teams)


class QualityRating(Enum):
    """Service quality rating scale"""
    POOR = 1
    FAIR = 2
    GOOD = 3
    VERY_GOOD = 4
    EXCELLENT = 5


class BookingEvent(Enum):
    """Domain events for booking lifecycle"""
    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_STARTED = "booking_started"
    BOOKING_COMPLETED = "booking_completed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled"
    NO_SHOW_DETECTED = "no_show_detected"
    QUALITY_RATED = "quality_rated"