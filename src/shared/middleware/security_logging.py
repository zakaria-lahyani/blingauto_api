"""
Security Event Logging Middleware

Logs security-relevant requests and responses for monitoring and analysis.
"""
import time
import json
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import structlog

logger = structlog.get_logger(__name__)


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging security events and suspicious activities"""
    
    # Sensitive paths that should be logged
    SECURITY_PATHS = {
        '/auth/login',
        '/auth/register', 
        '/auth/refresh',
        '/auth/logout',
        '/auth/forgot-password',
        '/auth/reset-password',
        '/auth/change-password',
        '/auth/verify-email',
        '/admin',
        '/manager'
    }
    
    # Security-relevant status codes
    SECURITY_STATUS_CODES = {
        400, 401, 403, 404, 422, 429, 500
    }
    
    def __init__(self, app, enable_detailed_logging: bool = True):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        logger.info("Security logging middleware initialized", 
                   detailed_logging=enable_detailed_logging)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log security-relevant requests and responses"""
        start_time = time.time()
        
        # Extract request information
        request_info = self._extract_request_info(request)
        
        # Check if this is a security-relevant request
        is_security_relevant = self._is_security_relevant(request)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log security events
            if is_security_relevant or response.status_code in self.SECURITY_STATUS_CODES:
                await self._log_security_event(request_info, response, duration)
            
            # Log suspicious activities
            await self._check_suspicious_activity(request_info, response, duration)
            
            return response
            
        except Exception as exc:
            # Log exceptions as security events
            duration = time.time() - start_time
            await self._log_exception(request_info, exc, duration)
            raise
    
    def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract relevant information from request"""
        # Get client IP (considering proxies)
        client_ip = self._get_client_ip(request)
        
        # Extract user agent
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Extract authorization info (without exposing tokens)
        auth_type = None
        if "authorization" in request.headers:
            auth_header = request.headers["authorization"]
            auth_type = auth_header.split(" ")[0] if " " in auth_header else "Unknown"
        
        return {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "auth_type": auth_type,
            "headers": self._sanitize_headers(dict(request.headers)),
            "timestamp": time.time()
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP considering proxy headers"""
        # Check common proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "Unknown"
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers to remove sensitive information"""
        sensitive_headers = {
            "authorization", "cookie", "set-cookie", 
            "x-api-key", "x-auth-token"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _is_security_relevant(self, request: Request) -> bool:
        """Check if request is security-relevant"""
        path = request.url.path
        
        # Check exact matches
        if path in self.SECURITY_PATHS:
            return True
        
        # Check path prefixes
        for security_path in self.SECURITY_PATHS:
            if path.startswith(security_path):
                return True
        
        # Check for admin/sensitive operations
        if any(keyword in path.lower() for keyword in ['admin', 'user', 'role', 'permission']):
            return True
        
        return False
    
    async def _log_security_event(self, request_info: Dict[str, Any], 
                                 response: Response, duration: float):
        """Log security event"""
        event_data = {
            "event_type": "security_event",
            "request": request_info,
            "response": {
                "status_code": response.status_code,
                "headers": self._sanitize_headers(dict(response.headers)),
                "duration": duration
            }
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"
        
        getattr(logger, log_level)(
            "Security event logged",
            **event_data
        )
    
    async def _check_suspicious_activity(self, request_info: Dict[str, Any], 
                                       response: Response, duration: float):
        """Check for suspicious activity patterns"""
        suspicions = []
        
        # Check for multiple failed login attempts
        if (request_info["path"] == "/auth/login" and 
            response.status_code == 401):
            suspicions.append("failed_login_attempt")
        
        # Check for SQL injection patterns in query params
        for param, value in request_info["query_params"].items():
            if isinstance(value, str):
                if any(pattern in value.lower() for pattern in 
                      ['union select', 'drop table', '1=1', "' or ", '" or ']):
                    suspicions.append("potential_sql_injection")
        
        # Check for XSS patterns
        for param, value in request_info["query_params"].items():
            if isinstance(value, str):
                if any(pattern in value.lower() for pattern in 
                      ['<script', 'javascript:', 'onload=', 'onerror=']):
                    suspicions.append("potential_xss")
        
        # Check for unusual user agents
        user_agent = request_info["user_agent"].lower()
        if any(bot in user_agent for bot in ['bot', 'crawler', 'scanner', 'hack']):
            suspicions.append("suspicious_user_agent")
        
        # Check for rate limiting violations
        if response.status_code == 429:
            suspicions.append("rate_limit_exceeded")
        
        # Check for slow requests (potential DoS)
        if duration > 10.0:  # 10 seconds
            suspicions.append("slow_request")
        
        # Log suspicious activities
        if suspicions:
            logger.warning(
                "Suspicious activity detected",
                event_type="suspicious_activity",
                suspicions=suspicions,
                request=request_info,
                response={
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
    
    async def _log_exception(self, request_info: Dict[str, Any], 
                           exception: Exception, duration: float):
        """Log exception as security event"""
        logger.error(
            "Exception in request processing",
            event_type="exception",
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            request=request_info,
            duration=duration
        )


class SecurityEventLogger:
    """Dedicated logger for security events"""
    
    def __init__(self):
        self.logger = structlog.get_logger("security_events")
    
    def log_authentication_success(self, user_id: str, email: str, 
                                 client_ip: str, user_agent: str):
        """Log successful authentication"""
        self.logger.info(
            "Authentication successful",
            event_type="auth_success",
            user_id=user_id,
            email=email,
            client_ip=client_ip,
            user_agent=user_agent
        )
    
    def log_authentication_failure(self, email: str, reason: str,
                                 client_ip: str, user_agent: str):
        """Log failed authentication"""
        self.logger.warning(
            "Authentication failed",
            event_type="auth_failure",
            email=email,
            reason=reason,
            client_ip=client_ip,
            user_agent=user_agent
        )
    
    def log_account_lockout(self, email: str, client_ip: str, 
                          attempts: int, lockout_duration: int):
        """Log account lockout"""
        self.logger.warning(
            "Account locked due to failed attempts",
            event_type="account_lockout",
            email=email,
            client_ip=client_ip,
            failed_attempts=attempts,
            lockout_duration_minutes=lockout_duration
        )
    
    def log_privilege_escalation(self, user_id: str, old_role: str, 
                               new_role: str, changed_by: str):
        """Log role/privilege changes"""
        self.logger.info(
            "User privilege changed",
            event_type="privilege_change",
            user_id=user_id,
            old_role=old_role,
            new_role=new_role,
            changed_by=changed_by
        )
    
    def log_password_change(self, user_id: str, client_ip: str, 
                           method: str = "self_service"):
        """Log password changes"""
        self.logger.info(
            "Password changed",
            event_type="password_change",
            user_id=user_id,
            client_ip=client_ip,
            method=method
        )
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any],
                              client_ip: str, user_agent: str):
        """Log suspicious activities"""
        self.logger.warning(
            "Suspicious activity detected",
            event_type="suspicious_activity",
            activity_type=activity_type,
            details=details,
            client_ip=client_ip,
            user_agent=user_agent
        )
    
    def log_data_access(self, user_id: str, resource: str, action: str,
                       client_ip: str, success: bool = True):
        """Log sensitive data access"""
        log_level = "info" if success else "warning"
        getattr(self.logger, log_level)(
            "Sensitive data access",
            event_type="data_access",
            user_id=user_id,
            resource=resource,
            action=action,
            client_ip=client_ip,
            success=success
        )


# Global security event logger
security_event_logger = SecurityEventLogger()