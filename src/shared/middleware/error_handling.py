"""
Global Error Handling Middleware

Catches and handles unhandled exceptions across the entire application.
Applied globally as the last middleware in the chain.
"""
import logging
import traceback
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.shared.exceptions import (
    StandardErrorResponse,
    ValidationError,
    InternalServerError,
    create_validation_error_details
)

logger = logging.getLogger(__name__)


class GlobalErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware for unhandled exceptions"""
    
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug
        logger.info(f"Global error handling middleware initialized (debug={debug})")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Handle any unhandled exceptions"""
        
        try:
            response = await call_next(request)
            return response
            
        except RequestValidationError as exc:
            # Handle Pydantic validation errors
            logger.warning(
                f"VALIDATION ERROR: {request.method} {request.url.path} - "
                f"Errors: {exc.errors()}"
            )
            
            error_details = create_validation_error_details(exc.errors())
            error_response = StandardErrorResponse(
                error="ValidationError",
                message="Request validation failed",
                status_code=422,
                timestamp=self._get_timestamp(),
                path=request.url.path,
                details=error_details
            )
            
            return JSONResponse(
                status_code=422,
                content=error_response.dict(),
                headers={"X-Error-Type": "ValidationError"}
            )
            
        except HTTPException as exc:
            # Handle HTTP exceptions with standardized format
            if isinstance(exc.detail, dict) and "error" in exc.detail:
                # Already standardized, just pass through
                return JSONResponse(
                    status_code=exc.status_code,
                    content=exc.detail,
                    headers=getattr(exc, "headers", {})
                )
            else:
                # Convert to standardized format
                error_response = StandardErrorResponse(
                    error="HTTPException",
                    message=str(exc.detail),
                    status_code=exc.status_code,
                    timestamp=self._get_timestamp(),
                    path=request.url.path
                )
                
                return JSONResponse(
                    status_code=exc.status_code,
                    content=error_response.dict(),
                    headers=getattr(exc, "headers", {})
                )
            
        except Exception as exc:
            # Log the unhandled exception
            logger.error(
                f"UNHANDLED EXCEPTION: {request.method} {request.url.path} - "
                f"Error: {str(exc)}\n{traceback.format_exc()}"
            )
            
            # Create standardized error response
            error_response = self._create_error_response(exc, request)
            
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers={"X-Error-Type": "UnhandledException"}
            )
    
    def _create_error_response(self, exc: Exception, request: Request) -> Dict[str, Any]:
        """Create standardized error response"""
        
        # Use standardized error response
        error_response = StandardErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred. Please try again later.",
            status_code=500,
            timestamp=self._get_timestamp(),
            path=request.url.path
        )
        
        # Add debug information in development
        if self.debug:
            # Convert to dict and add debug info
            response_dict = error_response.dict()
            response_dict["debug"] = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc().split("\n")
            }
            return response_dict
        
        return error_response.dict()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"