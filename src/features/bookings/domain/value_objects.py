"""
Booking domain value objects
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from .enums import BookingStatus, CancellationPolicy, QualityRating


@dataclass(frozen=True)
class BookingPeriod:
    """Time period for a booking"""
    start: datetime
    end: datetime
    
    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes"""
        return int((self.end - self.start).total_seconds() / 60)
    
    def overlaps_with(self, other: 'BookingPeriod') -> bool:
        """Check if this period overlaps with another"""
        return self.start < other.end and self.end > other.start


@dataclass(frozen=True)
class CancellationInfo:
    """Cancellation information with policy and fee"""
    policy: CancellationPolicy
    fee: Decimal
    notice_hours: float
    
    @classmethod
    def calculate(cls, total_price: Decimal, notice_hours: float) -> 'CancellationInfo':
        """Calculate cancellation info based on notice period"""
        if notice_hours > 24:
            return cls(CancellationPolicy.FREE, Decimal("0.00"), notice_hours)
        elif notice_hours > 6:
            return cls(CancellationPolicy.QUARTER_FEE, total_price * Decimal("0.25"), notice_hours)
        elif notice_hours > 2:
            return cls(CancellationPolicy.HALF_FEE, total_price * Decimal("0.50"), notice_hours)
        else:
            return cls(CancellationPolicy.FULL_FEE, total_price, notice_hours)


@dataclass(frozen=True)
class ServiceSummary:
    """Summary of services in a booking"""
    service_count: int
    total_price: Decimal
    total_duration: int
    service_names: tuple[str, ...]
    
    def __post_init__(self):
        if self.service_count <= 0:
            raise ValueError("Service count must be positive")
        if self.total_price < 0:
            raise ValueError("Total price cannot be negative")
        if self.total_duration <= 0:
            raise ValueError("Total duration must be positive")


@dataclass(frozen=True)
class QualityScore:
    """Service quality rating with feedback"""
    rating: QualityRating
    feedback: Optional[str] = None
    rated_at: Optional[datetime] = None
    
    @property
    def rating_value(self) -> int:
        """Get numeric rating value"""
        return self.rating.value
    
    @property
    def is_positive(self) -> bool:
        """Check if rating is positive (4 or 5)"""
        return self.rating.value >= 4
    
    @property
    def is_negative(self) -> bool:
        """Check if rating is negative (1 or 2)"""
        return self.rating.value <= 2


@dataclass(frozen=True)
class BookingMetrics:
    """Booking performance metrics"""
    scheduled_duration: int  # minutes
    actual_duration: Optional[int] = None  # minutes
    overtime_minutes: int = 0
    overtime_charge: Decimal = Decimal("0.00")
    on_time_start: bool = True
    
    @property
    def efficiency_ratio(self) -> Optional[float]:
        """Calculate efficiency ratio (scheduled/actual)"""
        if self.actual_duration is None or self.actual_duration == 0:
            return None
        return self.scheduled_duration / self.actual_duration
    
    @property
    def was_on_time(self) -> bool:
        """Check if service was completed on time"""
        return self.overtime_minutes == 0 and self.on_time_start