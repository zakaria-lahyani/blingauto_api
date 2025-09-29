"""
Helper Utilities

Pure utility functions following functional programming principles:
- Pure functions (no side effects)
- Single responsibility
- Composable
"""

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypeVar, Callable
from urllib.parse import urlparse


T = TypeVar('T')


def generate_uuid() -> str:
    """
    Generate a new UUID4 string
    
    Returns:
        UUID4 string
    """
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """
    Generate a short random ID
    
    Args:
        length: Length of the ID
        
    Returns:
        Random ID string
    """
    return uuid.uuid4().hex[:length]


def utc_now() -> datetime:
    """
    Get current UTC datetime
    
    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def timestamp_to_datetime(timestamp: float) -> datetime:
    """
    Convert timestamp to datetime
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Datetime object
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> float:
    """
    Convert datetime to timestamp
    
    Args:
        dt: Datetime object
        
    Returns:
        Unix timestamp
    """
    return dt.timestamp()


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm
    
    Args:
        value: String to hash
        algorithm: Hash algorithm (sha256, md5, etc.)
        
    Returns:
        Hexadecimal hash string
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(value.encode('utf-8'))
    return hash_obj.hexdigest()


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix




def remove_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove keys with None values from dictionary
    
    Args:
        d: Dictionary to clean
        
    Returns:
        Dictionary without None values
    """
    return {k: v for k, v in d.items() if v is not None}


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary
    
    Args:
        dictionary: Dictionary to search
        key: Key to get (supports dot notation)
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    keys = key.split('.')
    value = dictionary
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value






def is_valid_json_string(value: str) -> bool:
    """
    Check if string is valid JSON
    
    Args:
        value: String to check
        
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        import json
        json.loads(value)
        return True
    except (ValueError, TypeError):
        return False


def extract_domain_from_url(url: str) -> Optional[str]:
    """
    Extract domain from URL
    
    Args:
        url: URL to parse
        
    Returns:
        Domain name or None if invalid
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc or None
    except Exception:
        return None


