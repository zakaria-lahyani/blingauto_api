import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request details
        request_id = getattr(request.state, "request_id", "unknown")
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        
        # Log request
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query": query,
                "client": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {method} {path} - {response.status_code} ({duration:.3f}s)",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "duration": duration,
            }
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response