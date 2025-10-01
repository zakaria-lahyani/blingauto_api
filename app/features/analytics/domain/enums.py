"""Analytics domain enums."""

from enum import Enum


class MetricType(str, Enum):
    """Types of metrics."""

    REVENUE = "revenue"
    BOOKINGS = "bookings"
    CUSTOMERS = "customers"
    STAFF_PERFORMANCE = "staff_performance"
    EXPENSES = "expenses"
    PROFIT = "profit"


class TimeGranularity(str, Enum):
    """Time granularity for analytics."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class RevenueSource(str, Enum):
    """Sources of revenue."""

    BOOKINGS = "bookings"
    WALK_INS = "walk_ins"
    SUBSCRIPTIONS = "subscriptions"
    OTHER = "other"


class CustomerSegment(str, Enum):
    """Customer segments for analysis."""

    NEW = "new"
    RETURNING = "returning"
    VIP = "vip"
    INACTIVE = "inactive"
