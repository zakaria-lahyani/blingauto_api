"""
Global error handlers for the car wash application.
Provides consistent error responses across all features.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Union, TYPE_CHECKING
from datetime import datetime

# Import core errors
from app.core.errors.exceptions import BaseError

# Use TYPE_CHECKING to avoid circular imports at runtime
if TYPE_CHECKING:
    from app.features.auth.domain.exceptions import (
        AuthenticationError as AuthDomainAuthenticationError,
        BusinessRuleViolationError as AuthDomainBusinessRuleError,
        ValidationError as AuthDomainValidationError,
        UserInactiveError as AuthDomainUserInactiveError,
    )

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response structure."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: dict = None,
        status_code: int = 500
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp
            }
        }
        
        if self.details:
            response["error"]["details"] = self.details
        
        return response


# GENERIC ERROR HANDLERS

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors."""
    logger.warning(f"Validation error: {exc}")
    
    validation_details = []
    for error in exc.errors():
        validation_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"validation_errors": validation_details},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    
    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """Handle HTTP exceptions."""
    import traceback

    logger.warning(f"===== HTTP EXCEPTION HANDLER =====")
    logger.warning(f"Request URL: {request.url}")
    logger.warning(f"Request method: {request.method}")
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")

    # For 500 errors, log the full traceback
    if exc.status_code >= 500:
        logger.error(f"Exception type: {type(exc)}")
        logger.error(f"Exception attributes: {dir(exc)}")
        if hasattr(exc, '__traceback__'):
            logger.error("Full traceback:")
            logger.error(''.join(traceback.format_tb(exc.__traceback__)))

    # Map status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }

    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")

    error_response = ErrorResponse(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


async def base_error_handler(request: Request, exc: BaseError) -> JSONResponse:
    """Handle core BaseError exceptions (ConflictError, NotFoundError, etc.)."""
    logger.warning(f"{exc.code}: {exc.message}")

    error_response = ErrorResponse(
        error_code=exc.code,
        message=exc.message,
        details=exc.details if exc.details else None,
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    import traceback
    logger.error(f"===== GENERIC EXCEPTION HANDLER =====")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Exception type: {type(exc)}")
    logger.error(f"Exception message: {exc}")
    logger.error("Full traceback:")
    logger.error(traceback.format_exc())
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


# AUTH DOMAIN EXCEPTION HANDLERS

async def auth_domain_authentication_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle authentication errors from auth domain."""
    logger.warning(f"Authentication error: {exc}")

    error_response = ErrorResponse(
        error_code="UNAUTHORIZED",
        message=str(exc),
        status_code=status.HTTP_401_UNAUTHORIZED
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


async def auth_domain_business_rule_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle business rule violations from auth domain."""
    logger.warning(f"Business rule violation: {exc}")

    details = {}
    if hasattr(exc, 'rule') and exc.rule:
        details['rule'] = exc.rule

    error_response = ErrorResponse(
        error_code="BUSINESS_RULE_VIOLATION",
        message=str(exc),
        details=details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


async def auth_domain_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors from auth domain."""
    logger.warning(f"Validation error: {exc}")

    details = {}
    if hasattr(exc, 'field') and exc.field:
        details['field'] = exc.field

    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message=str(exc),
        details=details,
        status_code=status.HTTP_400_BAD_REQUEST
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


async def auth_domain_user_inactive_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle user inactive errors from auth domain."""
    logger.warning(f"User inactive error: {exc}")

    error_response = ErrorResponse(
        error_code="USER_INACTIVE",
        message=str(exc),
        status_code=status.HTTP_403_FORBIDDEN
    )

    return JSONResponse(
        status_code=error_response.status_code,
        content=error_response.to_dict()
    )


# ERROR HANDLER REGISTRY

def register_error_handlers(app):
    """Register all error handlers with the FastAPI app."""

    # Register specific handlers first
    specific_handlers = {
        RequestValidationError: validation_error_handler,
        HTTPException: http_exception_handler,
        StarletteHTTPException: http_exception_handler,
    }

    for exception_type, handler in specific_handlers.items():
        app.add_exception_handler(exception_type, handler)

    # Register core BaseError handler (for ConflictError, NotFoundError, etc.)
    # Must be before auth domain handlers since some may inherit from BaseError
    app.add_exception_handler(BaseError, base_error_handler)
    logger.info("Registered core BaseError handler")

    # Dynamically import and register all feature domain exception handlers
    # This avoids circular import issues
    domain_exception_count = 0

    # Auth domain exceptions
    try:
        from app.features.auth.domain.exceptions import (
            AuthenticationError as AuthDomainAuthenticationError,
            BusinessRuleViolationError as AuthDomainBusinessRuleError,
            ValidationError as AuthDomainValidationError,
            UserInactiveError as AuthDomainUserInactiveError,
        )

        auth_handlers = {
            AuthDomainAuthenticationError: auth_domain_authentication_error_handler,
            AuthDomainBusinessRuleError: auth_domain_business_rule_error_handler,
            AuthDomainValidationError: auth_domain_validation_error_handler,
            AuthDomainUserInactiveError: auth_domain_user_inactive_error_handler,
        }

        for exception_type, handler in auth_handlers.items():
            app.add_exception_handler(exception_type, handler)

        domain_exception_count += len(auth_handlers)
        logger.info(f"Registered {len(auth_handlers)} auth domain exception handlers")
    except ImportError as e:
        logger.warning(f"Could not register auth domain exception handlers: {e}")

    # Register handlers for other feature domain exceptions
    # These use the generic handlers since they have the same structure
    feature_exceptions = [
        ('bookings', ['ValidationError', 'BusinessRuleViolationError']),
        # Pricing feature removed
        # ('pricing', ['ValidationError', 'BusinessRuleViolationError']),
        ('scheduling', ['ValidationError', 'BusinessRuleViolationError']),
        ('services', ['ValidationError', 'BusinessRuleViolationError']),
        ('vehicles', ['ValidationError', 'BusinessRuleViolationError']),
    ]

    for feature_name, exception_names in feature_exceptions:
        try:
            module = __import__(f'app.features.{feature_name}.domain.exceptions', fromlist=exception_names)
            for exc_name in exception_names:
                if hasattr(module, exc_name):
                    exc_class = getattr(module, exc_name)
                    if exc_name == 'ValidationError':
                        app.add_exception_handler(exc_class, auth_domain_validation_error_handler)
                    elif exc_name == 'BusinessRuleViolationError':
                        app.add_exception_handler(exc_class, auth_domain_business_rule_error_handler)
                    domain_exception_count += 1
            logger.info(f"Registered {feature_name} domain exception handlers")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not register {feature_name} domain exception handlers: {e}")

    logger.info(f"Total domain exception handlers registered: {domain_exception_count}")

    # Register generic Exception handler last (catches all unhandled exceptions)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info(f"Registered all error handlers")