"""
Scheduling domain entities implementing facility management and scheduling rules.
Based on requirements RG-FAC-001, RG-FAC-002, RG-SCH-001, RG-SCH-002
"""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4

from .exceptions import ValidationError, BusinessRuleViolationError


class VehicleSize(str, Enum):
    """Vehicle size categories for compatibility checks - RG-FAC-002"""
    COMPACT = "compact"
    STANDARD = "standard"
    LARGE = "large"
    OVERSIZED = "oversized"


class ResourceType(str, Enum):
    """Resource type enumeration"""
    WASH_BAY = "wash_bay"
    MOBILE_TEAM = "mobile_team"


class ResourceStatus(str, Enum):
    """Resource status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    MAINTENANCE = "maintenance"


class DayOfWeek(str, Enum):
    """Day of week enumeration"""
    MONDAY = "monday"
    TUESDAY = "tuesday" 
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@dataclass
class Location:
    """GPS location for mobile services"""
    latitude: Decimal
    longitude: Decimal
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate GPS coordinates"""
        if not (-90 <= self.latitude <= 90):
            raise ValidationError("Latitude must be between -90 and 90")
        
        if not (-180 <= self.longitude <= 180):
            raise ValidationError("Longitude must be between -180 and 180")
    
    def distance_to(self, other: "Location") -> Decimal:
        """Calculate approximate distance to another location in kilometers"""
        # Simplified distance calculation (Haversine formula would be more accurate)
        lat_diff = abs(self.latitude - other.latitude)
        lng_diff = abs(self.longitude - other.longitude)
        
        # Rough approximation: 1 degree ≈ 111 km
        distance = Decimal(str(((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111))
        return distance


@dataclass
class BusinessHours:
    """Business hours for a specific day"""
    day: DayOfWeek
    open_time: Optional[time]
    close_time: Optional[time]
    is_closed: bool = False
    break_periods: List[Tuple[time, time]] = field(default_factory=list)
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate business hours"""
        if not self.is_closed:
            if not self.open_time or not self.close_time:
                raise ValidationError("Open and close times required when not closed")
            
            if self.open_time >= self.close_time:
                raise ValidationError("Open time must be before close time")
        
        # Validate break periods
        for start, end in self.break_periods:
            if start >= end:
                raise ValidationError("Break start time must be before end time")
            
            if not self.is_closed:
                if start < self.open_time or end > self.close_time:
                    raise ValidationError("Break periods must be within business hours")
    
    def is_time_available(self, check_time: time) -> bool:
        """Check if a specific time is available (not in break period)"""
        if self.is_closed:
            return False
        
        if check_time < self.open_time or check_time > self.close_time:
            return False
        
        for start, end in self.break_periods:
            if start <= check_time <= end:
                return False
        
        return True


@dataclass
class WashBay:
    """Wash bay resource - RG-FAC-001, RG-FAC-002"""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    bay_number: str = ""
    max_vehicle_size: VehicleSize = VehicleSize.STANDARD
    equipment_types: List[str] = field(default_factory=list)
    status: ResourceStatus = ResourceStatus.ACTIVE
    location: Optional[Location] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Business rule constants
    VEHICLE_SIZE_HIERARCHY = {
        VehicleSize.COMPACT: 1,
        VehicleSize.STANDARD: 2,
        VehicleSize.LARGE: 3,
        VehicleSize.OVERSIZED: 4
    }
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate wash bay constraints"""
        if not self.bay_number.strip():
            raise ValidationError("Bay number cannot be empty")
    
    @classmethod
    def create(
        cls,
        bay_number: str,
        max_vehicle_size: VehicleSize,
        equipment_types: List[str] = None,
        location: Optional[Location] = None
    ) -> "WashBay":
        """Create a new wash bay with validation"""
        return cls(
            bay_number=bay_number,
            max_vehicle_size=max_vehicle_size,
            equipment_types=equipment_types or [],
            location=location
        )
    
    def can_accommodate_vehicle(self, vehicle_size: VehicleSize) -> bool:
        """Check if bay can accommodate vehicle size - RG-FAC-002"""
        max_level = self.VEHICLE_SIZE_HIERARCHY[self.max_vehicle_size]
        vehicle_level = self.VEHICLE_SIZE_HIERARCHY[vehicle_size]
        return vehicle_level <= max_level
    
    def is_available_for_booking(self) -> bool:
        """Check if bay is available for new bookings"""
        return self.status == ResourceStatus.ACTIVE
    
    def activate(self) -> None:
        """Activate the wash bay"""
        self.status = ResourceStatus.ACTIVE
        self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate the wash bay for maintenance"""
        self.status = ResourceStatus.MAINTENANCE
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class MobileTeam:
    """Mobile team resource - RG-FAC-003, RG-FAC-004"""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    team_name: str = ""
    base_location: Location = None
    service_radius_km: Decimal = Decimal('50')  # Default 50km radius
    daily_capacity: int = 8  # Default 8 vehicles per day
    equipment_types: List[str] = field(default_factory=list)
    status: ResourceStatus = ResourceStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate mobile team constraints"""
        if not self.team_name.strip():
            raise ValidationError("Team name cannot be empty")
        
        if self.service_radius_km <= 0:
            raise ValidationError("Service radius must be positive")
        
        if self.daily_capacity <= 0:
            raise ValidationError("Daily capacity must be positive")
        
        if self.base_location is None:
            raise ValidationError("Base location is required")
    
    @classmethod
    def create(
        cls,
        team_name: str,
        base_location: Location,
        service_radius_km: Decimal = Decimal('50'),
        daily_capacity: int = 8,
        equipment_types: List[str] = None
    ) -> "MobileTeam":
        """Create a new mobile team with validation"""
        return cls(
            team_name=team_name,
            base_location=base_location,
            service_radius_km=service_radius_km,
            daily_capacity=daily_capacity,
            equipment_types=equipment_types or []
        )
    
    def can_service_location(self, customer_location: Location) -> bool:
        """Check if team can service the customer location - RG-FAC-004"""
        if self.status != ResourceStatus.ACTIVE:
            return False
        
        distance = self.base_location.distance_to(customer_location)
        return distance <= self.service_radius_km
    
    def is_available_for_booking(self) -> bool:
        """Check if team is available for new bookings"""
        return self.status == ResourceStatus.ACTIVE


@dataclass
class TimeSlot:
    """Time slot for scheduling"""
    start_time: datetime
    end_time: datetime
    resource_id: str
    resource_type: ResourceType
    is_available: bool = True
    booking_id: Optional[str] = None
    buffer_minutes: int = 15  # RG-SCH-002
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate time slot constraints"""
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Minimum slot duration (30 minutes from requirements)
        min_duration = timedelta(minutes=30)
        if self.end_time - self.start_time < min_duration:
            raise ValidationError("Time slot must be at least 30 minutes")
    
    @property
    def duration_minutes(self) -> int:
        """Get slot duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def conflicts_with(self, other: "TimeSlot") -> bool:
        """Check if this slot conflicts with another slot"""
        if self.resource_id != other.resource_id:
            return False
        
        # Check for overlap considering buffer time
        buffer = timedelta(minutes=self.buffer_minutes)
        
        self_start_with_buffer = self.start_time - buffer
        self_end_with_buffer = self.end_time + buffer
        other_start_with_buffer = other.start_time - buffer
        other_end_with_buffer = other.end_time + buffer
        
        return not (
            self_end_with_buffer <= other_start_with_buffer or
            other_end_with_buffer <= self_start_with_buffer
        )
    
    def reserve_for_booking(self, booking_id: str) -> None:
        """Reserve this slot for a booking"""
        if not self.is_available:
            raise BusinessRuleViolationError("Time slot is not available")
        
        self.is_available = False
        self.booking_id = booking_id
    
    def release(self) -> None:
        """Release this slot (make it available again)"""
        self.is_available = True
        self.booking_id = None


@dataclass
class SchedulingConstraints:
    """Scheduling constraints and rules - RG-SCH-002"""
    
    min_advance_hours: int = 2  # Minimum 2 hours advance booking
    max_advance_days: int = 90  # Maximum 90 days advance booking
    slot_duration_minutes: int = 30  # Default slot duration
    buffer_minutes: int = 15  # Buffer between bookings
    business_hours: Dict[DayOfWeek, BusinessHours] = field(default_factory=dict)
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate scheduling constraints"""
        if self.min_advance_hours < 0:
            raise ValidationError("Minimum advance hours cannot be negative")
        
        if self.max_advance_days <= 0:
            raise ValidationError("Maximum advance days must be positive")
        
        if self.slot_duration_minutes <= 0:
            raise ValidationError("Slot duration must be positive")
        
        if self.buffer_minutes < 0:
            raise ValidationError("Buffer minutes cannot be negative")
    
    def is_valid_booking_time(self, booking_time: datetime) -> bool:
        """Check if booking time meets constraints"""
        now = datetime.now(timezone.utc)
        
        # Check minimum advance time
        min_time = now + timedelta(hours=self.min_advance_hours)
        if booking_time < min_time:
            return False
        
        # Check maximum advance time  
        max_time = now + timedelta(days=self.max_advance_days)
        if booking_time > max_time:
            return False
        
        # Check business hours
        day_name = booking_time.strftime("%A").lower()
        try:
            day_enum = DayOfWeek(day_name)
        except ValueError:
            return False
        
        if day_enum in self.business_hours:
            business_hours = self.business_hours[day_enum]
            booking_time_only = booking_time.time()
            return business_hours.is_time_available(booking_time_only)
        
        # If no business hours defined for the day, assume closed
        return False