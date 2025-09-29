"""
Bookings Feature Configuration
"""
from typing import List, Optional, Dict
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from datetime import timedelta


class BookingsConfig(BaseSettings):
    """Bookings feature specific configuration"""
    
    # Feature settings
    table_prefix: str = Field(default="booking_", description="Table prefix for booking tables")
    cache_key_prefix: str = Field(default="booking", description="Cache key prefix")
    
    # Business rules
    max_bookings_per_user: int = Field(default=50, description="Maximum active bookings per user")
    max_services_per_booking: int = Field(default=10, description="Maximum services per booking")
    allow_past_bookings: bool = Field(default=False, description="Allow bookings in the past")
    
    # Booking timing
    min_advance_booking_hours: int = Field(default=1, description="Minimum hours in advance for booking")
    max_advance_booking_days: int = Field(default=90, description="Maximum days in advance for booking")
    booking_time_slot_minutes: int = Field(default=30, description="Time slot granularity in minutes")
    
    # Operating hours
    operating_start_hour: int = Field(default=8, description="Start of operating hours (24h format)")
    operating_end_hour: int = Field(default=18, description="End of operating hours (24h format)")
    operating_days: List[int] = Field(
        default=[1, 2, 3, 4, 5, 6],  # Monday to Saturday
        description="Operating days (1=Monday, 7=Sunday)"
    )
    
    # Booking modifications
    allow_booking_modifications: bool = Field(default=True, description="Allow booking modifications")
    min_modification_hours: int = Field(default=4, description="Minimum hours before booking to allow modifications")
    allow_cancellation: bool = Field(default=True, description="Allow booking cancellation")
    min_cancellation_hours: int = Field(default=2, description="Minimum hours before booking to allow cancellation")
    
    # Booking states
    auto_confirm_bookings: bool = Field(default=False, description="Auto-confirm new bookings")
    default_booking_status: str = Field(default="pending", description="Default status for new bookings")
    valid_booking_statuses: List[str] = Field(
        default=["pending", "confirmed", "in_progress", "completed", "cancelled", "no_show"],
        description="Valid booking status values"
    )
    
    # Notifications
    enable_booking_notifications: bool = Field(default=True, description="Enable booking notifications")
    reminder_hours_before: List[int] = Field(
        default=[24, 2], 
        description="Hours before booking to send reminders"
    )
    notify_on_status_change: bool = Field(default=True, description="Notify on status changes")
    
    # Payment integration
    require_payment_for_booking: bool = Field(default=False, description="Require payment at booking")
    allow_partial_payments: bool = Field(default=True, description="Allow partial payments")
    payment_deadline_hours: int = Field(default=24, description="Hours to complete payment")
    
    # Capacity management
    enable_capacity_management: bool = Field(default=True, description="Enable booking capacity limits")
    max_concurrent_bookings: int = Field(default=5, description="Max concurrent bookings at same time")
    buffer_time_minutes: int = Field(default=15, description="Buffer time between bookings")
    
    # Event tracking
    track_booking_events: bool = Field(default=True, description="Track booking lifecycle events")
    auto_log_status_changes: bool = Field(default=True, description="Auto-log status changes")
    track_user_interactions: bool = Field(default=True, description="Track user interactions with bookings")
    
    # Soft delete behavior
    soft_delete_bookings: bool = Field(default=True, description="Use soft delete for bookings")
    soft_delete_events: bool = Field(default=False, description="Use soft delete for booking events")
    retain_cancelled_bookings: bool = Field(default=True, description="Retain cancelled booking records")
    
    # Performance
    cache_user_bookings_ttl: int = Field(default=300, description="Cache TTL for user bookings (5 min)")
    cache_booking_detail_ttl: int = Field(default=600, description="Cache TTL for booking details")
    cache_availability_ttl: int = Field(default=60, description="Cache TTL for availability data")
    
    # Audit settings
    track_booking_changes: bool = Field(default=True, description="Track booking modifications")
    log_cancellation_reasons: bool = Field(default=True, description="Log cancellation reasons")
    
    class Config:
        env_prefix = "BOOKINGS_"
        extra = "ignore"
    
    @validator("max_bookings_per_user")
    def validate_max_bookings(cls, v):
        """Ensure max bookings is positive"""
        if v < 1:
            raise ValueError("Max bookings per user must be at least 1")
        return v
    
    @validator("operating_start_hour", "operating_end_hour")
    def validate_operating_hours(cls, v):
        """Ensure operating hours are valid 24h format"""
        if not 0 <= v <= 23:
            raise ValueError("Operating hours must be between 0 and 23")
        return v
    
    @validator("operating_end_hour")
    def validate_end_after_start(cls, v, values):
        """Ensure end hour is after start hour"""
        start_hour = values.get("operating_start_hour", 8)
        if v <= start_hour:
            raise ValueError("Operating end hour must be after start hour")
        return v
    
    @validator("operating_days")
    def validate_operating_days(cls, v):
        """Ensure operating days are valid"""
        if not v or len(v) == 0:
            raise ValueError("At least one operating day must be specified")
        
        for day in v:
            if not 1 <= day <= 7:
                raise ValueError("Operating days must be between 1 (Monday) and 7 (Sunday)")
        
        return sorted(list(set(v)))  # Remove duplicates and sort
    
    @validator("valid_booking_statuses")
    def validate_booking_statuses(cls, v):
        """Ensure at least basic statuses are present"""
        required_statuses = ["pending", "confirmed", "cancelled"]
        for status in required_statuses:
            if status not in v:
                raise ValueError(f"Required booking status '{status}' missing from valid statuses")
        return v
    
    @validator("default_booking_status")
    def validate_default_status(cls, v, values):
        """Ensure default status is in valid statuses"""
        valid_statuses = values.get("valid_booking_statuses", [])
        if valid_statuses and v not in valid_statuses:
            raise ValueError(f"Default booking status '{v}' not in valid statuses")
        return v
    
    def is_valid_booking_time(self, hour: int, day_of_week: int) -> bool:
        """Check if booking time is within operating hours and days"""
        return (
            day_of_week in self.operating_days and
            self.operating_start_hour <= hour < self.operating_end_hour
        )
    
    def is_valid_booking_status(self, status: str) -> bool:
        """Check if booking status is valid"""
        return status in self.valid_booking_statuses
    
    def get_operating_hours_duration(self) -> int:
        """Get total operating hours per day"""
        return self.operating_end_hour - self.operating_start_hour
    
    def get_time_slots_per_day(self) -> int:
        """Get number of time slots per operating day"""
        operating_minutes = self.get_operating_hours_duration() * 60
        return operating_minutes // self.booking_time_slot_minutes
    
    def get_cache_key_for_user_bookings(self, user_id: str) -> str:
        """Get cache key for user's booking list"""
        return f"{self.cache_key_prefix}:user:{user_id}:bookings"
    
    def get_cache_key_for_booking(self, booking_id: str) -> str:
        """Get cache key for specific booking"""
        return f"{self.cache_key_prefix}:booking:{booking_id}"
    
    def get_cache_key_for_availability(self, date: str) -> str:
        """Get cache key for date availability"""
        return f"{self.cache_key_prefix}:availability:{date}"


# Singleton instance
_bookings_config: Optional[BookingsConfig] = None


def get_bookings_config() -> BookingsConfig:
    """Get bookings configuration singleton"""
    global _bookings_config
    if _bookings_config is None:
        _bookings_config = BookingsConfig()
    return _bookings_config