"""
Auth Security Logging Middleware

Security-focused logging middleware specifically for authentication endpoints.
Applied only to auth routes (/auth/*) via router-level middleware.

This middleware logs:
- Failed login attempts with details
- Suspicious authentication patterns
- Security-relevant events (password changes, etc.)
- Potential brute force attacks
- Account lockout events
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.features.auth.config import AuthConfig

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("auth.security")


class AuthSecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Security logging middleware for authentication endpoints"""
    
    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        logger.info("Auth security logging middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log security-relevant auth events"""
        
        if not self.config.enable_security_logging:
            return await call_next(request)
        
        # Extract request information
        request_info = await self._extract_security_info(request)
        
        # Log request start for sensitive endpoints
        if self._is_sensitive_endpoint(request.url.path, request.method):
            security_logger.info(
                f"AUTH_REQUEST_START: {request_info['method']} {request_info['path']} "
                f"from {request_info['client_ip']} - User-Agent: {request_info['user_agent'][:100]}"
            )
        
        # Process request
        response = await call_next(request)
        
        # Log response based on outcome
        await self._log_security_response(request_info, response)
        
        return response
    
    async def _extract_security_info(self, request: Request) -> Dict[str, Any]:
        """Extract security-relevant information from request"""
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Get authentication header info (without exposing the token)
        auth_header = request.headers.get("Authorization", "")
        has_auth_header = bool(auth_header.startswith("Bearer "))
        
        # Extract request body for specific endpoints (be careful with sensitive data)
        request_body_summary = await self._get_safe_request_summary(request)
        
        return {
            "method": request.method,
            "path": request.url.path,
            "full_url": str(request.url),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "has_auth_header": has_auth_header,
            "request_body_summary": request_body_summary,
            "timestamp": datetime.utcnow().isoformat(),
            "headers": {
                "content-type": request.headers.get("Content-Type", ""),
                "origin": request.headers.get("Origin", ""),
                "referer": request.headers.get("Referer", ""),
            }
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address safely"""
        
        if "X-Forwarded-For" in request.headers:
            return request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in request.headers:
            return request.headers["X-Real-IP"]
        elif request.client:
            return request.client.host
        else:
            return "unknown"
    
    async def _get_safe_request_summary(self, request: Request) -> Dict[str, Any]:
        """Get safe summary of request body (without exposing sensitive data)"""
        
        try:
            # Only process certain content types
            content_type = request.headers.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                return {"type": "non-json", "content_type": content_type}
            
            body = await request.body()
            if not body:
                return {"type": "empty"}
            
            # Parse JSON safely
            try:
                json_data = json.loads(body.decode())
                
                # Create safe summary (don't log sensitive fields)
                safe_summary = {}
                for key, value in json_data.items():
                    if key.lower() in ['password', 'token', 'secret', 'key']:
                        safe_summary[key] = "[REDACTED]"
                    elif isinstance(value, str) and len(value) > 100:
                        safe_summary[key] = f"[STRING:{len(value)} chars]"
                    elif key.lower() in ['email', 'username']:
                        # Log these but mask part of them
                        if isinstance(value, str) and '@' in value:
                            parts = value.split('@')
                            if len(parts) == 2:
                                safe_summary[key] = f"{parts[0][:2]}***@{parts[1]}"
                            else:
                                safe_summary[key] = value[:3] + "***"
                        else:
                            safe_summary[key] = str(value)[:3] + "***" if len(str(value)) > 3 else value
                    else:
                        safe_summary[key] = value
                
                return {"type": "json", "fields": list(json_data.keys()), "summary": safe_summary}
                
            except json.JSONDecodeError:
                return {"type": "invalid-json", "size": len(body)}
            
        except Exception as e:
            return {"type": "error", "error": str(e)}
    
    def _is_sensitive_endpoint(self, path: str, method: str) -> bool:
        """Check if this is a security-sensitive endpoint"""
        
        sensitive_endpoints = [
            ("/auth/login", "POST"),
            ("/auth/register", "POST"),
            ("/auth/reset-password", "POST"),
            ("/auth/change-password", "POST"),
            ("/auth/verify-email", "POST"),
            ("/auth/refresh", "POST"),
            ("/auth/logout", "POST"),
        ]
        
        return (path, method) in sensitive_endpoints
    
    async def _log_security_response(self, request_info: Dict[str, Any], response: Response):
        """Log security events based on response"""
        
        path = request_info["path"]
        method = request_info["method"]
        client_ip = request_info["client_ip"]
        status_code = response.status_code
        
        # Determine log level and message based on endpoint and status
        if path == "/auth/login" and method == "POST":
            if status_code == 200:
                security_logger.info(
                    f"LOGIN_SUCCESS: User logged in successfully from {client_ip} "
                    f"- User-Agent: {request_info['user_agent'][:50]}"
                )
            elif status_code == 401:
                security_logger.warning(
                    f"LOGIN_FAILED: Failed login attempt from {client_ip} "
                    f"- Email: {request_info['request_body_summary'].get('summary', {}).get('email', 'unknown')} "
                    f"- User-Agent: {request_info['user_agent'][:50]}"
                )
            elif status_code == 423:
                security_logger.error(
                    f"LOGIN_BLOCKED: Account locked login attempt from {client_ip} "
                    f"- Email: {request_info['request_body_summary'].get('summary', {}).get('email', 'unknown')}"
                )
            elif status_code == 429:
                security_logger.warning(
                    f"LOGIN_RATE_LIMITED: Rate limited login attempt from {client_ip}"
                )
        
        elif path == "/auth/register" and method == "POST":
            if status_code == 201:
                security_logger.info(
                    f"REGISTER_SUCCESS: New user registered from {client_ip} "
                    f"- Email: {request_info['request_body_summary'].get('summary', {}).get('email', 'unknown')}"
                )
            elif status_code == 409:
                security_logger.warning(
                    f"REGISTER_DUPLICATE: Duplicate registration attempt from {client_ip} "
                    f"- Email: {request_info['request_body_summary'].get('summary', {}).get('email', 'unknown')}"
                )
            elif status_code == 429:
                security_logger.warning(
                    f"REGISTER_RATE_LIMITED: Rate limited registration attempt from {client_ip}"
                )
        
        elif path == "/auth/reset-password" and method == "POST":
            if status_code == 200:
                security_logger.info(
                    f"PASSWORD_RESET_REQUESTED: Password reset requested from {client_ip} "
                    f"- Email: {request_info['request_body_summary'].get('summary', {}).get('email', 'unknown')}"
                )
            elif status_code == 429:
                security_logger.warning(
                    f"PASSWORD_RESET_RATE_LIMITED: Rate limited password reset from {client_ip}"
                )
        
        elif path == "/auth/change-password" and method == "POST":
            if status_code == 200:
                security_logger.info(
                    f"PASSWORD_CHANGED: Password changed successfully from {client_ip}"
                )
            elif status_code == 401:
                security_logger.warning(
                    f"PASSWORD_CHANGE_FAILED: Failed password change attempt from {client_ip}"
                )
        
        elif path == "/auth/verify-email" and method == "POST":
            if status_code == 200:
                security_logger.info(
                    f"EMAIL_VERIFIED: Email verification successful from {client_ip}"
                )
            elif status_code == 400:
                security_logger.warning(
                    f"EMAIL_VERIFICATION_FAILED: Invalid email verification attempt from {client_ip}"
                )
        
        # Log any 4xx/5xx responses from auth endpoints as potential security events
        elif self._is_sensitive_endpoint(path, method) and status_code >= 400:
            log_level = logging.ERROR if status_code >= 500 else logging.WARNING
            security_logger.log(
                log_level,
                f"AUTH_ERROR: {method} {path} returned {status_code} "
                f"from {client_ip} - User-Agent: {request_info['user_agent'][:50]}"
            )
        
        # Log successful operations on sensitive endpoints
        elif self._is_sensitive_endpoint(path, method) and 200 <= status_code < 300:
            security_logger.info(
                f"AUTH_SUCCESS: {method} {path} successful from {client_ip}"
            )