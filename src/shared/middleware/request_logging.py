"""
Request Logging Middleware

Logs all HTTP requests and responses with performance metrics.
Applied globally to all routes.
"""
import time
import logging
import json
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.shared.config import LoggingConfig

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""
    
    def __init__(self, app, config: LoggingConfig):
        super().__init__(app)
        self.config = config
        logger.info("Request logging middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response with timing"""
        
        # Start timing
        start_time = time.time()
        
        # Extract request information
        request_info = await self._extract_request_info(request)
        
        # Log request start
        if self.config.enable_request_logging:
            logger.info(
                f"REQUEST START: {request_info['method']} {request_info['url']} "
                f"- Client: {request_info['client_ip']} "
                f"- User-Agent: {request_info['user_agent'][:100]}..."
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            # Log response
            await self._log_response(request_info, response, process_time)
            
            return response
            
        except Exception as exc:
            # Calculate processing time for errors
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"REQUEST ERROR: {request_info['method']} {request_info['url']} "
                f"- Error: {str(exc)} - Time: {process_time:.3f}s"
            )
            
            # Re-raise the exception
            raise
    
    async def _extract_request_info(self, request: Request) -> dict:
        """Extract relevant information from request"""
        
        # Get client IP (handle proxy headers)
        client_ip = request.client.host if request.client else "unknown"
        if "X-Forwarded-For" in request.headers:
            client_ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in request.headers:
            client_ip = request.headers["X-Real-IP"]
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Get request body if configured to log it
        request_body = None
        if self.config.log_request_body:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON for better logging
                    try:
                        request_body = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_body = f"<binary data: {len(body)} bytes>"
                else:
                    request_body = "<empty>"
            except Exception:
                request_body = "<error reading body>"
        
        return {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "request_body": request_body
        }
    
    async def _log_response(self, request_info: dict, response: Response, process_time: float):
        """Log response information"""
        
        if not self.config.enable_request_logging:
            return
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # Check if this is a slow request
        is_slow = process_time > self.config.slow_request_threshold
        if is_slow and self.config.log_slow_requests:
            log_level = logging.WARNING
        
        # Prepare log message
        log_message = (
            f"REQUEST COMPLETE: {request_info['method']} {request_info['path']} "
            f"- Status: {response.status_code} "
            f"- Time: {process_time:.3f}s "
            f"- Client: {request_info['client_ip']}"
        )
        
        if is_slow:
            log_message += " [SLOW REQUEST]"
        
        # Log the response
        logger.log(log_level, log_message)
        
        # Log additional details for errors
        if response.status_code >= 400:
            logger.log(log_level, 
                f"REQUEST DETAILS: URL={request_info['url']}, "
                f"Query={request_info['query_params']}, "
                f"User-Agent={request_info['user_agent'][:50]}..."
            )
        
        # Log response body if configured (be careful with sensitive data)
        if self.config.log_response_body and response.status_code >= 400:
            try:
                # Only log response body for errors and if it's text-based
                response_headers = dict(response.headers)
                content_type = response_headers.get("content-type", "")
                
                if "application/json" in content_type or "text/" in content_type:
                    logger.log(log_level, f"RESPONSE BODY: <response body logging enabled but not implemented for security>")
            except Exception:
                pass  # Don't fail request if logging fails