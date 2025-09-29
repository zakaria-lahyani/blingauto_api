"""
Standardized timestamp utilities for consistent time handling across the application
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, func
from sqlalchemy.sql import ColumnElement


def utc_now() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current UTC timestamp with timezone info
    """
    return datetime.now(timezone.utc)


def utc_timestamp() -> datetime:
    """
    Alias for utc_now() for backwards compatibility.
    
    Returns:
        datetime: Current UTC timestamp with timezone info
    """
    return utc_now()


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert datetime to UTC if it has timezone info, otherwise assume UTC.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        datetime: UTC datetime with timezone info, or None if input is None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        return dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(timezone.utc)


def db_utc_timestamp() -> ColumnElement:
    """
    Get database-level UTC timestamp function.
    
    This should be used for database defaults to ensure timestamps
    are generated at the database level for consistency.
    
    Returns:
        ColumnElement: SQLAlchemy function for current UTC timestamp
    """
    return func.timezone('UTC', func.now())


def naive_utc_now() -> datetime:
    """
    Get current UTC timestamp without timezone info (naive datetime).
    
    Use this only for legacy compatibility where timezone-naive
    datetimes are required.
    
    Returns:
        datetime: Current UTC timestamp without timezone info
    """
    return datetime.utcnow()


class TimestampMixin:
    """
    Mixin class to provide standard timestamp columns for database models.
    
    Usage:
        class MyModel(TimestampMixin, Base):
            __tablename__ = "my_table"
            id = Column(Integer, primary_key=True)
            # created_at and updated_at are automatically added
    """
    from sqlalchemy import Column, DateTime
    
    # Use timezone-aware datetime with database-level defaults
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.timezone('UTC', func.now()),
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.timezone('UTC', func.now()),
        onupdate=func.timezone('UTC', func.now()),
        nullable=False
    )


def format_timestamp(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S UTC") -> Optional[str]:
    """
    Format timestamp for display.
    
    Args:
        dt: Datetime to format
        format_str: Format string (default: ISO-like format with UTC)
        
    Returns:
        str: Formatted timestamp string, or None if input is None
    """
    if dt is None:
        return None
    
    # Convert to UTC for consistent display
    utc_dt = to_utc(dt)
    return utc_dt.strftime(format_str)


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO format timestamp string to UTC datetime.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        datetime: Parsed UTC datetime with timezone info
        
    Raises:
        ValueError: If timestamp string is invalid
    """
    try:
        # Try parsing with timezone info first
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return to_utc(dt)
    except ValueError:
        # Fall back to assuming UTC if no timezone info
        dt = datetime.fromisoformat(timestamp_str)
        return dt.replace(tzinfo=timezone.utc)


# Constants for common operations
EPOCH_UTC = datetime(1970, 1, 1, tzinfo=timezone.utc)
MAX_TIMESTAMP = datetime(2100, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


def is_expired(expiry_time: Optional[datetime]) -> bool:
    """
    Check if a timestamp has expired (is in the past).
    
    Args:
        expiry_time: Expiry timestamp to check
        
    Returns:
        bool: True if expired or None, False if still valid
    """
    if expiry_time is None:
        return True
    
    return to_utc(expiry_time) < utc_now()


def time_until_expiry(expiry_time: Optional[datetime]) -> Optional[float]:
    """
    Get seconds until expiry.
    
    Args:
        expiry_time: Expiry timestamp
        
    Returns:
        float: Seconds until expiry, or None if already expired or None input
    """
    if expiry_time is None:
        return None
    
    utc_expiry = to_utc(expiry_time)
    now = utc_now()
    
    if utc_expiry <= now:
        return None
    
    return (utc_expiry - now).total_seconds()