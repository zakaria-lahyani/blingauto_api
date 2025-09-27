"""
Auth Middleware Dependencies

Since FastAPI routers don't support middleware directly, we implement 
middleware functionality as route dependencies that can be applied 
to individual endpoints or endpoint groups.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib import request

from fastapi import Request, HTTPException, Depends
from starlette.responses import Response

from src.features.auth.config import AuthConfig
from src.features.auth.domain.enums import AuthRole

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("auth.security")


class AuthRateLimiter:
    """Auth-specific rate limiting as a dependency"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        # In-memory storage (in production, use Redis)
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.user_requests: Dict[str, List[datetime]] = defaultdict(list)
        self.endpoint_requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        if "X-Forwarded-For" in request.headers:
            return request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in request.headers:
            return request.headers["X-Real-IP"]
        elif request.client:
            return request.client.host
        else:
            return "unknown"
    
    async def _get_user_from_request(self, request: Request) -> Optional[dict]:
        """Extract authenticated user info from request"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            
            # Verify JWT token using auth infrastructure
            from ...infrastructure.security import JWTHandler
            jwt_handler = JWTHandler(self.config)
            payload = jwt_handler.verify_token(token)
            
            if payload and payload.get("type") == "access":
                return {
                    "user_id": payload.get("sub"),
                    "role": AuthRole(payload.get("role", AuthRole.CLIENT.value))
                }
            
        except Exception as e:
            logger.debug(f"Failed to extract user from request: {e}")
        
        return None
    
    def _check_time_window_limit(self, key: str, limit: int, window: timedelta,
                               now: datetime, storage: Dict[str, List[datetime]]) -> bool:
        """Generic time window rate limiting check"""
        
        window_start = now - window
        
        # Get existing requests for this key
        requests = storage[key]
        
        # Remove expired requests
        recent_requests = [req for req in requests if req > window_start]
        
        # Check if limit exceeded
        if len(recent_requests) >= limit:
            return False
        
        # Record this request
        recent_requests.append(now)
        storage[key] = recent_requests
        
        return True
    
    async def check_rate_limit(self, request: Request, endpoint_limit: Optional[int] = None) -> None:
        """Check rate limit for auth endpoints"""
        
        if not self.config.enable_rate_limiting:
            return
        
        now = datetime.utcnow()
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method
        
        # Get user info if authenticated
        user_info = await self._get_user_from_request(request)
        
        # Check endpoint-specific limits first
        if endpoint_limit:
            storage_key = f"{path}:{method}:{client_ip}"
            if not self._check_time_window_limit(
                storage_key, 
                endpoint_limit, 
                timedelta(minutes=1), 
                now, 
                self.endpoint_requests
            ):
                logger.warning(f"Endpoint rate limit exceeded: {method} {path} from {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Endpoint rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60", "X-RateLimit-Type": "endpoint"}
                )
        
        # Check general rate limits
        if user_info:
            # Authenticated user - use role-based limits
            user_id = user_info.get("user_id")
            role = user_info.get("role", AuthRole.CLIENT)
            
            # Get role-based limit
            if role == AuthRole.ADMIN:
                limit = self.config.admin_rate_limit
            elif role == AuthRole.MANAGER:
                limit = self.config.manager_rate_limit
            elif role == AuthRole.WASHER:
                limit = self.config.washer_rate_limit
            else:
                limit = self.config.client_rate_limit
            
            if not self._check_time_window_limit(
                user_id,
                limit,
                timedelta(minutes=1),
                now,
                self.user_requests
            ):
                logger.warning(f"User rate limit exceeded: {method} {path} for user {user_id}")
                raise HTTPException(
                    status_code=429,
                    detail="User rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60", "X-RateLimit-Type": "user"}
                )
        else:
            # Anonymous user - use IP-based limiting
            limit = self.config.client_rate_limit // 2
            
            if not self._check_time_window_limit(
                client_ip,
                limit,
                timedelta(minutes=1),
                now,
                self.requests
            ):
                logger.warning(f"IP rate limit exceeded: {method} {path} from {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60", "X-RateLimit-Type": "ip"}
                )


class AuthSecurityLogger:
    """Auth-specific security logging as a dependency"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        if "X-Forwarded-For" in request.headers:
            return request.headers["X-Forwarded-For"].split(",")[0].strip()
        elif "X-Real-IP" in request.headers:
            return request.headers["X-Real-IP"]
        elif request.client:
            return request.client.host
        else:
            return "unknown"
    
    async def log_security_event(self, request: Request, response: Optional[Response] = None, 
                                event_type: str = "request", details: Dict = None) -> None:
        """Log security-relevant events"""
        
        if not self.config.enable_security_logging:
            return
        
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method
        user_agent = request.headers.get("User-Agent", "unknown")[:100]
        
        # Base log message
        log_message = f"{event_type.upper()}: {method} {path} from {client_ip}"
        
        # Add response status if available
        if response:
            log_message += f" - Status: {response.status_code}"
        
        # Add additional details
        if details:
            detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            log_message += f" - {detail_str}"
        
        # Add user agent for context
        log_message += f" - UA: {user_agent}"
        
        # Determine log level based on event type and status
        if response and response.status_code >= 400:
            if response.status_code >= 500:
                log_level = logging.ERROR
            else:
                log_level = logging.WARNING
        elif event_type in ["failed_login", "lockout", "suspicious"]:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        security_logger.log(log_level, log_message)


# Global instances (one per application)
_rate_limiter = None
_security_logger = None


def get_auth_rate_limiter(auth_module) -> AuthRateLimiter:
    """Get or create auth rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AuthRateLimiter(auth_module.config)
    return _rate_limiter


def get_auth_security_logger(auth_module) -> AuthSecurityLogger:
    """Get or create auth security logger instance"""
    global _security_logger
    if _security_logger is None:
        _security_logger = AuthSecurityLogger(auth_module.config)
    return _security_logger


# Dependency factory functions
def auth_rate_limit(endpoint_limit: Optional[int] = None):
    """Create a rate limiting dependency for auth endpoints"""
    async def rate_limit_dependency(
        request: Request,
        auth_module=Depends(lambda: request.app.state.auth)
    ):
        rate_limiter = get_auth_rate_limiter(auth_module)
        await rate_limiter.check_rate_limit(request, endpoint_limit)
    
    return rate_limit_dependency


def auth_security_log(event_type: str = "request", **details):
    """Create a security logging dependency for auth endpoints"""
    async def security_log_dependency(
        request: Request,
        auth_module=Depends(lambda: request.app.state.auth)
    ):
        security_logger = get_auth_security_logger(auth_module)
        await security_logger.log_security_event(request, event_type=event_type, details=details)
    
    return security_log_dependency


# Predefined dependencies for common endpoints
login_rate_limit = auth_rate_limit(5)  # 5 login attempts per minute
register_rate_limit = auth_rate_limit(3)  # 3 registration attempts per minute
password_reset_rate_limit = auth_rate_limit(2)  # 2 password reset requests per minute
general_auth_rate_limit = auth_rate_limit()  # General auth rate limiting

login_security_log = auth_security_log("auth_attempt")
register_security_log = auth_security_log("registration")
password_security_log = auth_security_log("password_operation")