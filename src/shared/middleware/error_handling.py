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
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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
            
        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise
            
        except Exception as exc:
            # Log the unhandled exception
            logger.error(
                f"UNHANDLED EXCEPTION: {request.method} {request.url.path} - "
                f"Error: {str(exc)}\n{traceback.format_exc()}"
            )
            
            # Create error response
            error_response = self._create_error_response(exc, request)
            
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers={"X-Error-Type": "UnhandledException"}
            )
    
    def _create_error_response(self, exc: Exception, request: Request) -> Dict[str, Any]:
        """Create standardized error response"""
        
        # Base error response
        error_response = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
            "timestamp": self._get_timestamp(),
            "path": request.url.path,
            "method": request.method
        }
        
        # Add debug information in development
        if self.debug:
            error_response.update({
                "debug": {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "traceback": traceback.format_exc().split("\n")
                }
            })
        
        return error_response
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"