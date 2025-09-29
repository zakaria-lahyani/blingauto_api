"""
Standardized error responses and exception handling
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Request
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detailed error information"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class StandardErrorResponse(BaseModel):
    """Standardized error response format"""
    success: bool = False
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    status_code: int
    timestamp: str
    path: str
    request_id: Optional[str] = None
    
    @classmethod
    def from_exception(
        cls, 
        exc: Exception, 
        request: Request, 
        status_code: int = 500,
        message: Optional[str] = None,
        details: Optional[List[ErrorDetail]] = None
    ) -> "StandardErrorResponse":
        """Create error response from exception"""
        return cls(
            error=type(exc).__name__,
            message=message or str(exc),
            details=details or [],
            status_code=status_code,
            timestamp=datetime.utcnow().isoformat() + "Z",
            path=request.url.path,
            request_id=getattr(request.state, "request_id", None)
        )


class AuthenticationError(HTTPException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=401,
            detail=StandardErrorResponse(
                error="AuthenticationError",
                message=message,
                status_code=401,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=[ErrorDetail(message="Please provide valid authentication credentials")]
            ).dict(),
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Authorization related errors"""
    def __init__(self, message: str = "Insufficient permissions", required_role: Optional[str] = None):
        details = [ErrorDetail(message=message)]
        if required_role:
            details.append(ErrorDetail(message=f"Required role: {required_role}", code="INSUFFICIENT_ROLE"))
        
        super().__init__(
            status_code=403,
            detail=StandardErrorResponse(
                error="AuthorizationError",
                message=message,
                status_code=403,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=details
            ).dict()
        )


class ValidationError(HTTPException):
    """Validation related errors"""
    def __init__(self, message: str = "Validation failed", field_errors: Optional[List[ErrorDetail]] = None):
        super().__init__(
            status_code=400,
            detail=StandardErrorResponse(
                error="ValidationError",
                message=message,
                status_code=400,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=field_errors or []
            ).dict()
        )


class ResourceNotFoundError(HTTPException):
    """Resource not found errors"""
    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        
        super().__init__(
            status_code=404,
            detail=StandardErrorResponse(
                error="ResourceNotFoundError",
                message=message,
                status_code=404,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=[ErrorDetail(message=message, code="RESOURCE_NOT_FOUND")]
            ).dict()
        )


class BusinessLogicError(HTTPException):
    """Business logic related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[List[ErrorDetail]] = None):
        if details is None:
            details = [ErrorDetail(message=message, code=error_code)]
        
        super().__init__(
            status_code=422,
            detail=StandardErrorResponse(
                error="BusinessLogicError",
                message=message,
                status_code=422,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=details
            ).dict()
        )


class SessionError(HTTPException):
    """Session related errors"""
    def __init__(self, message: str = "Session expired or invalid"):
        super().__init__(
            status_code=401,
            detail=StandardErrorResponse(
                error="SessionError",
                message=message,
                status_code=401,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=[ErrorDetail(message="Please log in again", code="SESSION_EXPIRED")]
            ).dict(),
            headers={"WWW-Authenticate": "Bearer"}
        )


class TooManyRequestsError(HTTPException):
    """Rate limiting errors"""
    def __init__(self, message: str = "Too many requests", retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=429,
            detail=StandardErrorResponse(
                error="TooManyRequestsError",
                message=message,
                status_code=429,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=[ErrorDetail(message="Please try again later", code="RATE_LIMIT_EXCEEDED")]
            ).dict(),
            headers=headers
        )


class InternalServerError(HTTPException):
    """Internal server errors"""
    def __init__(self, message: str = "An internal error occurred", include_details: bool = False):
        details = [ErrorDetail(message="Please try again later or contact support")]
        if include_details:
            details.append(ErrorDetail(message=message, code="INTERNAL_ERROR"))
        
        super().__init__(
            status_code=500,
            detail=StandardErrorResponse(
                error="InternalServerError",
                message="An internal error occurred. Please try again later.",
                status_code=500,
                timestamp=datetime.utcnow().isoformat() + "Z",
                path="",  # Will be set by middleware
                details=details
            ).dict()
        )


# Error message constants for better consistency
class ErrorMessages:
    """Centralized error messages"""
    
    # Authentication
    AUTH_REQUIRED = "Authentication required"
    AUTH_INVALID_CREDENTIALS = "Invalid authentication credentials"
    AUTH_TOKEN_EXPIRED = "Authentication token has expired"
    AUTH_TOKEN_INVALID = "Invalid authentication token"
    
    # Authorization
    AUTHZ_INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
    AUTHZ_ADMIN_REQUIRED = "Administrator privileges required"
    AUTHZ_MANAGER_REQUIRED = "Manager or administrator privileges required"
    AUTHZ_STAFF_REQUIRED = "Staff privileges required"
    AUTHZ_OWNER_REQUIRED = "You can only access your own resources"
    
    # Validation
    VALIDATION_REQUIRED_FIELD = "This field is required"
    VALIDATION_INVALID_FORMAT = "Invalid format"
    VALIDATION_EMAIL_INVALID = "Invalid email address"
    VALIDATION_PASSWORD_WEAK = "Password does not meet security requirements"
    VALIDATION_UUID_INVALID = "Invalid UUID format"
    
    # Resource
    RESOURCE_NOT_FOUND = "Resource not found"
    USER_NOT_FOUND = "User not found"
    VEHICLE_NOT_FOUND = "Vehicle not found"
    BOOKING_NOT_FOUND = "Booking not found"
    SERVICE_NOT_FOUND = "Service not found"
    
    # Business Logic
    BUSINESS_EMAIL_ALREADY_EXISTS = "An account with this email already exists"
    BUSINESS_VEHICLE_LIMIT_EXCEEDED = "Maximum vehicle limit reached"
    BUSINESS_BOOKING_CONFLICT = "Booking time conflicts with existing booking"
    BUSINESS_BOOKING_PAST_TIME = "Cannot book appointments in the past"
    BUSINESS_INACTIVE_USER = "User account is inactive"
    
    # Session
    SESSION_EXPIRED = "Your session has expired. Please log in again"
    SESSION_INVALID = "Invalid session. Please log in again"
    SESSION_REQUIRED = "Active session required"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "Too many requests. Please try again later"
    
    # Server
    INTERNAL_ERROR = "An internal error occurred. Please try again later"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    DATABASE_ERROR = "Database operation failed"


def create_validation_error_details(errors: List[Dict[str, Any]]) -> List[ErrorDetail]:
    """Convert validation errors to ErrorDetail objects"""
    details = []
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Validation error")
        code = error.get("type", "VALIDATION_ERROR")
        
        details.append(ErrorDetail(
            field=field,
            message=message,
            code=code
        ))
    
    return details