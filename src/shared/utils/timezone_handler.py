"""
Robust timezone handling utilities for the booking system.
Automatically handles timezone-aware and naive datetime conversions.
"""
from datetime import datetime, timezone
from typing import Optional


class RobustTimezoneHandler:
    """Handles all timezone conversions robustly and automatically"""
    
    @staticmethod
    def to_utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Convert any datetime to timezone-aware UTC datetime.
        
        Args:
            dt: Input datetime (can be naive or aware)
            
        Returns:
            UTC timezone-aware datetime or None if input is None
        """
        if dt is None:
            return None
            
        if dt.tzinfo is None:
            # Assume UTC if naive
            return dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if already timezone-aware
            return dt.astimezone(timezone.utc)
    
    @staticmethod
    def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
        """
        Convert any datetime to naive UTC datetime (for database storage).
        
        Args:
            dt: Input datetime (can be naive or aware)
            
        Returns:
            Naive UTC datetime or None if input is None
        """
        if dt is None:
            return None
            
        if dt.tzinfo is None:
            # Already naive, assume it's UTC
            return dt
        else:
            # Convert to UTC and make naive
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
    
    @staticmethod
    def safe_compare(dt1: Optional[datetime], dt2: Optional[datetime]) -> bool:
        """
        Safely compare two datetimes by converting both to UTC-aware.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            True if dt1 <= dt2, False otherwise
        """
        if dt1 is None or dt2 is None:
            return False
            
        dt1_aware = RobustTimezoneHandler.to_utc_aware(dt1)
        dt2_aware = RobustTimezoneHandler.to_utc_aware(dt2)
        
        return dt1_aware <= dt2_aware
    
    @staticmethod
    def safe_subtract(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[float]:
        """
        Safely subtract two datetimes and return seconds difference.
        
        Args:
            dt1: First datetime
            dt2: Second datetime
            
        Returns:
            Seconds difference (dt1 - dt2) or None if either is None
        """
        if dt1 is None or dt2 is None:
            return None
            
        dt1_aware = RobustTimezoneHandler.to_utc_aware(dt1)
        dt2_aware = RobustTimezoneHandler.to_utc_aware(dt2)
        
        return (dt1_aware - dt2_aware).total_seconds()
    
    @staticmethod
    def now_utc_aware() -> datetime:
        """Get current UTC time as timezone-aware datetime"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def now_utc_naive() -> datetime:
        """Get current UTC time as naive datetime"""
        return datetime.now(timezone.utc).replace(tzinfo=None)


# Convenience functions
def normalize_datetime_for_db(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to format suitable for database storage (naive UTC)"""
    return RobustTimezoneHandler.to_naive_utc(dt)


def normalize_datetime_for_comparison(dt: Optional[datetime]) -> Optional[datetime]:
    """Convert datetime to format suitable for comparison (aware UTC)"""
    return RobustTimezoneHandler.to_utc_aware(dt)


def safe_datetime_compare(dt1: Optional[datetime], dt2: Optional[datetime]) -> bool:
    """Safely compare two datetimes (dt1 <= dt2)"""
    return RobustTimezoneHandler.safe_compare(dt1, dt2)


def safe_datetime_subtract_hours(dt1: Optional[datetime], dt2: Optional[datetime]) -> Optional[float]:
    """Safely subtract datetimes and return hours difference"""
    seconds = RobustTimezoneHandler.safe_subtract(dt1, dt2)
    return seconds / 3600 if seconds is not None else None