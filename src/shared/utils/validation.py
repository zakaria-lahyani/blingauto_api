"""
Input Validation and Sanitization Utilities

Provides comprehensive validation and sanitization for user inputs
to prevent injection attacks and ensure data integrity.
"""
import re
import html
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import bleach

logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
        r"(;|\-\-|/\*|\*/)",
        r"(\b(or|and)\s+\d+\s*=\s*\d+)",
        r"(\b(or|and)\s+[\"'].*[\"']\s*=\s*[\"'].*[\"'])",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig)\b",
        r"\.\.\/",
        r"\/etc\/passwd",
        r"\/bin\/",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Normalize whitespace
        value = ' '.join(value.split())
        
        # HTML escape
        value = html.escape(value)
        
        # Limit length
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and sanitize email"""
        if not email or not isinstance(email, str):
            raise ValueError("Email is required")
        
        email = email.strip().lower()
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        # Check for suspicious patterns
        if cls._contains_injection_patterns(email):
            raise ValueError("Email contains suspicious patterns")
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValueError("Email too long")
        
        return email
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            raise ValueError("Password is required")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if len(password) > 128:
            raise ValueError("Password too long")
        
        # Check for basic complexity
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'[0-9]', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>/?]', password))
        
        complexity_count = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity_count < 3:
            raise ValueError("Password must contain at least 3 of: uppercase, lowercase, digits, special characters")
        
        return password
    
    @classmethod
    def validate_name(cls, name: str, field_name: str = "Name") -> str:
        """Validate and sanitize name fields"""
        if not name or not isinstance(name, str):
            raise ValueError(f"{field_name} is required")
        
        name = name.strip()
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValueError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes")
        
        if len(name) < 1:
            raise ValueError(f"{field_name} cannot be empty")
        
        if len(name) > 50:
            raise ValueError(f"{field_name} too long (max 50 characters)")
        
        # Check for suspicious patterns
        if cls._contains_injection_patterns(name):
            raise ValueError(f"{field_name} contains suspicious patterns")
        
        return cls.sanitize_string(name, 50)
    
    @classmethod
    def validate_phone(cls, phone: Optional[str]) -> Optional[str]:
        """Validate and sanitize phone number"""
        if not phone:
            return None
        
        if not isinstance(phone, str):
            raise ValueError("Phone must be a string")
        
        # Remove all non-digit characters except + for international numbers
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # Basic phone validation
        if not re.match(r'^\+?[\d]{7,15}$', cleaned_phone):
            raise ValueError("Invalid phone number format")
        
        if len(cleaned_phone) > 20:
            raise ValueError("Phone number too long")
        
        return cleaned_phone
    
    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validate URL"""
        if not url or not isinstance(url, str):
            raise ValueError("URL is required")
        
        url = url.strip()
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            
            # Only allow http and https
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("URL must use http or https")
            
        except Exception:
            raise ValueError("Invalid URL format")
        
        if len(url) > 2048:
            raise ValueError("URL too long")
        
        # Check for suspicious patterns
        if cls._contains_injection_patterns(url):
            raise ValueError("URL contains suspicious patterns")
        
        return url
    
    @classmethod
    def sanitize_html(cls, content: str, allowed_tags: Optional[List[str]] = None) -> str:
        """Sanitize HTML content"""
        if not content:
            return ""
        
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
        
        # Default allowed tags for rich text
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        
        # Use bleach to sanitize HTML
        cleaned = bleach.clean(
            content,
            tags=allowed_tags,
            attributes={},
            strip=True
        )
        
        return cleaned
    
    @classmethod
    def validate_json_input(cls, data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """Validate JSON input for depth and content"""
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        def check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise ValueError(f"JSON depth exceeds maximum of {max_depth}")
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(key, str) and cls._contains_injection_patterns(key):
                        raise ValueError(f"Suspicious pattern in key: {key}")
                    check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1)
            elif isinstance(obj, str):
                if cls._contains_injection_patterns(obj):
                    raise ValueError(f"Suspicious pattern in value: {obj[:100]}")
        
        check_depth(data)
        return data
    
    @classmethod
    def _contains_injection_patterns(cls, value: str) -> bool:
        """Check if value contains potential injection patterns"""
        value_lower = value.lower()
        
        # Check SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return True
        
        # Check XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {pattern}")
                return True
        
        # Check command injection patterns
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                logger.warning(f"Command injection pattern detected: {pattern}")
                return True
        
        return False
    
    @classmethod
    def validate_file_upload(cls, filename: str, content_type: str, max_size: int = 10485760) -> str:
        """Validate file upload"""
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename is required")
        
        # Sanitize filename
        filename = re.sub(r'[^\w\.-]', '_', filename)
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.csv']
        extension = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if extension not in allowed_extensions:
            raise ValueError(f"File type not allowed: {extension}")
        
        # Validate content type
        allowed_content_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf', 'text/plain', 'text/csv'
        ]
        
        if content_type not in allowed_content_types:
            raise ValueError(f"Content type not allowed: {content_type}")
        
        return filename


# Global validator instance
validator = InputValidator()