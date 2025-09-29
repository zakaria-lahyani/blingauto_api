"""
Scheduling domain entities
"""
from datetime import datetime, time, timedelta
from typing import List, Optional, Set, Dict, Any
from uuid import UUID, uuid4

from .enums import (
    DayOfWeek, ResourceType, ResourceStatus, SlotStatus, 
    ScheduleType, ConflictType, SuggestionStrategy
)


class BusinessHours:
    """Business hours configuration for a specific day"""
    
    def __init__(
        self,
        day_of_week: DayOfWeek,
        open_time: time,
        close_time: time,
        is_closed: bool = False,
        break_periods: Optional[List[tuple[time, time]]] = None,
        id: Optional[UUID] = None
    ):
        if not is_closed and open_time >= close_time:
            raise ValueError("Open time must be before close time")
        
        self.id = id or uuid4()
        self.day_of_week = day_of_week
        self.open_time = open_time
        self.close_time = close_time
        self.is_closed = is_closed
        self.break_periods = break_periods or []
    
    def is_time_within_hours(self, check_time: time) -> bool:
        """Check if a time falls within business hours"""
        if self.is_closed:
            return False
        
        if not (self.open_time <= check_time <= self.close_time):
            return False
        
        # Check if time falls within break periods
        for break_start, break_end in self.break_periods:
            if break_start <= check_time <= break_end:
                return False
        
        return True
    
    def get_available_minutes(self) -> int:
        """Get total available minutes in the day"""
        if self.is_closed:
            return 0
        
        # Calculate total business hours in minutes
        total_minutes = (
            datetime.combine(datetime.today(), self.close_time) -
            datetime.combine(datetime.today(), self.open_time)
        ).total_seconds() / 60
        
        # Subtract break periods
        for break_start, break_end in self.break_periods:
            break_minutes = (
                datetime.combine(datetime.today(), break_end) -
                datetime.combine(datetime.today(), break_start)
            ).total_seconds() / 60
            total_minutes -= break_minutes
        
        return int(total_minutes)


class Resource:
    """Schedulable resource (wash bay, staff member, equipment)"""
    
    def __init__(
        self,
        name: str,
        resource_type: ResourceType,
        capacity: int = 1,
        status: ResourceStatus = ResourceStatus.AVAILABLE,
        skills: Optional[Set[str]] = None,
        hourly_rate: Optional[float] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.name = name
        self.resource_type = resource_type
        self.capacity = capacity
        self.status = status
        self.skills = skills or set()
        self.hourly_rate = hourly_rate
        self.created_at = created_at or datetime.utcnow()
    
    def is_available(self) -> bool:
        """Check if resource is available for booking"""
        return self.status == ResourceStatus.AVAILABLE
    
    def can_handle_service(self, required_skills: Set[str]) -> bool:
        """Check if resource has required skills for a service"""
        if not required_skills:
            return True
        return required_skills.issubset(self.skills)


class TimeSlot:
    """Represents a bookable time slot"""
    
    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        resource_id: Optional[UUID] = None,
        status: SlotStatus = SlotStatus.AVAILABLE,
        booking_id: Optional[UUID] = None,
        blocked_reason: Optional[str] = None,
        id: Optional[UUID] = None
    ):
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")
        
        self.id = id or uuid4()
        self.start_time = start_time
        self.end_time = end_time
        self.resource_id = resource_id
        self.status = status
        self.booking_id = booking_id
        self.blocked_reason = blocked_reason
    
    @property
    def duration_minutes(self) -> int:
        """Get slot duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this slot overlaps with another slot"""
        return (
            self.start_time < other.end_time and
            self.end_time > other.start_time
        )
    
    def can_accommodate_duration(self, required_minutes: int) -> bool:
        """Check if slot can accommodate required duration"""
        return self.duration_minutes >= required_minutes
    
    def is_available(self) -> bool:
        """Check if slot is available for booking"""
        return self.status == SlotStatus.AVAILABLE


class SchedulingConflict:
    """Represents a scheduling conflict"""
    
    def __init__(
        self,
        conflict_type: ConflictType,
        message: str,
        requested_time: datetime,
        conflicting_booking_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        suggested_alternatives: Optional[List[datetime]] = None
    ):
        self.conflict_type = conflict_type
        self.message = message
        self.requested_time = requested_time
        self.conflicting_booking_id = conflicting_booking_id
        self.resource_id = resource_id
        self.suggested_alternatives = suggested_alternatives or []


class AvailabilityRequest:
    """Request for checking availability"""
    
    def __init__(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        required_skills: Optional[Set[str]] = None,
        preferred_resources: Optional[List[UUID]] = None,
        exclude_times: Optional[List[tuple[datetime, datetime]]] = None
    ):
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        
        self.start_date = start_date
        self.end_date = end_date
        self.duration_minutes = duration_minutes
        self.required_skills = required_skills or set()
        self.preferred_resources = preferred_resources or []
        self.exclude_times = exclude_times or []


class AvailabilityResponse:
    """Response containing available time slots"""
    
    def __init__(
        self,
        available_slots: List[TimeSlot],
        conflicts: List[SchedulingConflict],
        suggested_times: List[datetime],
        total_available_slots: int,
        search_period: tuple[datetime, datetime]
    ):
        self.available_slots = available_slots
        self.conflicts = conflicts
        self.suggested_times = suggested_times
        self.total_available_slots = total_available_slots
        self.search_period = search_period
    
    def has_available_slots(self) -> bool:
        """Check if any slots are available"""
        return len(self.available_slots) > 0
    
    def get_earliest_slot(self) -> Optional[TimeSlot]:
        """Get the earliest available slot"""
        if not self.available_slots:
            return None
        return min(self.available_slots, key=lambda slot: slot.start_time)


class SchedulingPreferences:
    """User preferences for scheduling suggestions"""
    
    def __init__(
        self,
        preferred_days: Optional[Set[DayOfWeek]] = None,
        preferred_times: Optional[List[tuple[time, time]]] = None,
        avoid_times: Optional[List[tuple[time, time]]] = None,
        preferred_resources: Optional[List[UUID]] = None,
        max_travel_time: Optional[int] = None,  # minutes
        buffer_time: int = 15,  # minutes between appointments
        strategy: SuggestionStrategy = SuggestionStrategy.EARLIEST_AVAILABLE
    ):
        self.preferred_days = preferred_days or set()
        self.preferred_times = preferred_times or []
        self.avoid_times = avoid_times or []
        self.preferred_resources = preferred_resources or []
        self.max_travel_time = max_travel_time
        self.buffer_time = buffer_time
        self.strategy = strategy
    
    def matches_preferred_day(self, check_date: datetime) -> bool:
        """Check if date matches preferred days"""
        if not self.preferred_days:
            return True
        
        day_mapping = {
            0: DayOfWeek.MONDAY,
            1: DayOfWeek.TUESDAY,
            2: DayOfWeek.WEDNESDAY,
            3: DayOfWeek.THURSDAY,
            4: DayOfWeek.FRIDAY,
            5: DayOfWeek.SATURDAY,
            6: DayOfWeek.SUNDAY
        }
        
        day_of_week = day_mapping[check_date.weekday()]
        return day_of_week in self.preferred_days
    
    def matches_preferred_time(self, check_time: time) -> bool:
        """Check if time matches preferred time ranges"""
        if not self.preferred_times:
            return True
        
        return any(
            start_time <= check_time <= end_time
            for start_time, end_time in self.preferred_times
        )
    
    def should_avoid_time(self, check_time: time) -> bool:
        """Check if time should be avoided"""
        return any(
            start_time <= check_time <= end_time
            for start_time, end_time in self.avoid_times
        )


class BusinessConfiguration:
    """Overall business configuration for scheduling"""
    
    def __init__(
        self,
        business_hours: Dict[DayOfWeek, BusinessHours],
        slot_duration_minutes: int = 30,
        buffer_between_bookings: int = 15,
        max_advance_booking_days: int = 90,
        min_advance_booking_hours: int = 2,
        allow_same_day_booking: bool = True,
        timezone: str = "UTC"
    ):
        self.business_hours = business_hours
        self.slot_duration_minutes = slot_duration_minutes
        self.buffer_between_bookings = buffer_between_bookings
        self.max_advance_booking_days = max_advance_booking_days
        self.min_advance_booking_hours = min_advance_booking_hours
        self.allow_same_day_booking = allow_same_day_booking
        self.timezone = timezone
    
    def get_business_hours_for_date(self, date: datetime) -> Optional[BusinessHours]:
        """Get business hours for a specific date"""
        day_mapping = {
            0: DayOfWeek.MONDAY,
            1: DayOfWeek.TUESDAY,
            2: DayOfWeek.WEDNESDAY,
            3: DayOfWeek.THURSDAY,
            4: DayOfWeek.FRIDAY,
            5: DayOfWeek.SATURDAY,
            6: DayOfWeek.SUNDAY
        }
        
        day_of_week = day_mapping[date.weekday()]
        return self.business_hours.get(day_of_week)
    
    def is_business_open_at(self, check_datetime: datetime) -> bool:
        """Check if business is open at specific datetime"""
        business_hours = self.get_business_hours_for_date(check_datetime)
        if not business_hours:
            return False
        
        return business_hours.is_time_within_hours(check_datetime.time())
    
    def get_next_business_day(self, from_date: datetime) -> Optional[datetime]:
        """Get next business day from given date"""
        current_date = from_date.date()
        for _ in range(7):  # Check up to a week
            current_date += timedelta(days=1)
            check_datetime = datetime.combine(current_date, time.min)
            business_hours = self.get_business_hours_for_date(check_datetime)
            if business_hours and not business_hours.is_closed:
                return check_datetime
        return None