"""
Booking domain events
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from .enums import BookingStatus, QualityRating


@dataclass(frozen=True)
class BookingEvent:
    """Base booking domain event"""
    booking_id: UUID
    customer_id: UUID
    occurred_at: datetime
    
    @property
    def event_type(self) -> str:
        """Event type - to be overridden by subclasses"""
        return "booking_event"


@dataclass(frozen=True)
class BookingCreated(BookingEvent):
    """Event fired when a new booking is created"""
    vehicle_id: UUID
    scheduled_at: datetime
    service_ids: List[UUID]
    total_price: Decimal
    total_duration: int
    notes: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "booking_created"


@dataclass(frozen=True)
class BookingConfirmed(BookingEvent):
    """Event fired when a booking is confirmed"""
    scheduled_at: datetime
    total_price: Decimal
    
    @property
    def event_type(self) -> str:
        return "booking_confirmed"


@dataclass(frozen=True)
class BookingStarted(BookingEvent):
    """Event fired when service starts"""
    scheduled_at: datetime
    actual_start_time: datetime
    service_ids: List[UUID]
    
    @property
    def event_type(self) -> str:
        return "booking_started"


@dataclass(frozen=True)
class BookingCompleted(BookingEvent):
    """Event fired when service is completed"""
    scheduled_at: datetime
    actual_start_time: datetime
    actual_end_time: datetime
    total_price: Decimal
    overtime_charge: Decimal
    service_ids: List[UUID]
    
    @property
    def event_type(self) -> str:
        return "booking_completed"


@dataclass(frozen=True)
class BookingCancelled(BookingEvent):
    """Event fired when a booking is cancelled"""
    scheduled_at: datetime
    cancellation_fee: Decimal
    notice_hours: float
    reason: Optional[str] = None
    
    @property
    def event_type(self) -> str:
        return "booking_cancelled"


@dataclass(frozen=True)
class BookingRescheduled(BookingEvent):
    """Event fired when a booking is rescheduled"""
    old_scheduled_at: datetime
    new_scheduled_at: datetime
    notice_hours: float
    
    @property
    def event_type(self) -> str:
        return "booking_rescheduled"


@dataclass(frozen=True)
class NoShowDetected(BookingEvent):
    """Event fired when a no-show is detected"""
    scheduled_at: datetime
    grace_period_end: datetime
    penalty_fee: Decimal
    
    @property
    def event_type(self) -> str:
        return "no_show_detected"


@dataclass(frozen=True)
class QualityRated(BookingEvent):
    """Event fired when service quality is rated"""
    rating: QualityRating
    feedback: Optional[str]
    service_ids: List[UUID]
    
    @property
    def event_type(self) -> str:
        return "quality_rated"


@dataclass(frozen=True)
class ServiceAdded(BookingEvent):
    """Event fired when a service is added to booking"""
    service_id: UUID
    service_name: str
    price: Decimal
    duration: int
    new_total_price: Decimal
    new_total_duration: int
    
    def __post_init__(self):
        object.__setattr__(self, 'event_type', 'service_added')


@dataclass(frozen=True)
class ServiceRemoved(BookingEvent):
    """Event fired when a service is removed from booking"""
    service_id: UUID
    service_name: str
    price: Decimal
    duration: int
    new_total_price: Decimal
    new_total_duration: int
    
    def __post_init__(self):
        object.__setattr__(self, 'event_type', 'service_removed')