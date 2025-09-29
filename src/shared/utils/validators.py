"""
Validation Utilities

Clean validation functions following Single Responsibility Principle:
- One validator per concern
- Pure functions
- Clear error messages
"""

import re
from typing import Optional, List
from email_validator import validate_email, EmailNotValidError


def is_valid_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    try:
        validate_email(email)
        return True
    except (EmailNotValidError, ValueError):
        return False


def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number format (basic validation)
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid, False otherwise
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Phone should have 10-15 digits
    return 10 <= len(digits_only) <= 15


def is_strong_password(password: str) -> bool:
    """
    Validate password strength
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter  
    - Contains digit
    - Contains special character
    
    Args:
        password: Password to validate
        
    Returns:
        True if password is strong, False otherwise
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    return all([has_upper, has_lower, has_digit, has_special])


def get_password_strength_errors(password: str) -> List[str]:
    """
    Get specific password validation errors
    
    Args:
        password: Password to validate
        
    Returns:
        List of error messages
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return errors


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")
    
    # Strip whitespace
    sanitized = value.strip()
    
    # Remove null characters
    sanitized = sanitized.replace('\x00', '')
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def is_valid_license_plate(plate: str) -> bool:
    """
    Validate license plate format (basic validation)
    
    Args:
        plate: License plate to validate
        
    Returns:
        True if plate is valid, False otherwise
    """
    if not plate:
        return False
    
    # Remove whitespace and convert to uppercase
    plate = plate.strip().upper()
    
    # Basic validation: 2-10 alphanumeric characters
    return bool(re.match(r'^[A-Z0-9]{2,10}$', plate))


def is_valid_vin(vin: str) -> bool:
    """
    Validate Vehicle Identification Number (VIN)
    
    Args:
        vin: VIN to validate
        
    Returns:
        True if VIN is valid, False otherwise
    """
    if not vin:
        return False
    
    # Remove whitespace and convert to uppercase
    vin = vin.strip().upper()
    
    # VIN should be exactly 17 characters
    if len(vin) != 17:
        return False
    
    # VIN should only contain alphanumeric characters (excluding I, O, Q)
    if not re.match(r'^[ABCDEFGHJKLMNPRSTUVWXYZ0-9]{17}$', vin):
        return False
    
    return True


def is_valid_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def validate_positive_integer(value: int, field_name: str = "value") -> None:
    """
    Validate that a value is a positive integer
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValueError: If value is not a positive integer
    """
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")
    
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def validate_non_empty_string(value: str, field_name: str = "value") -> None:
    """
    Validate that a string is not empty
    
    Args:
        value: String to validate
        field_name: Name of the field for error messages
        
    Raises:
        ValueError: If string is empty or only whitespace
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    
    if not value.strip():
        raise ValueError(f"{field_name} cannot be empty")