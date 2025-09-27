"""
Auth-Specific Rate Limiting Middleware

Rate limiting middleware specifically designed for authentication endpoints.
Applied only to auth routes (/auth/*) via router-level middleware.

This middleware provides:
- Role-based rate limiting for authenticated users
- IP-based rate limiting for anonymous users  
- Endpoint-specific limits for sensitive operations (login, register)
- Integration with auth JWT verification
- Distributed rate limiting using Redis
"""
import logging
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.features.auth.config import AuthConfig
from src.features.auth.domain.enums import AuthRole
from src.shared.services.rate_limiter import get_endpoint_rate_limiter, get_rate_limiter, RateLimitResult

logger = logging.getLogger(__name__)


class AuthRateLimitingMiddleware(BaseHTTPMiddleware):
    """Auth-specific rate limiting middleware for authentication endpoints using Redis"""
    
    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        
        logger.info("Auth rate limiting middleware initialized with distributed backend")
    
    async def dispatch(self, request: Request, call_next):
        """Apply auth-specific rate limiting using distributed rate limiter"""
        
        if not self.config.enable_rate_limiting:
            return await call_next(request)
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method
        
        # Get authenticated user info if available
        user_info = await self._get_user_from_request(request)
        
        # Determine identifier for rate limiting
        if user_info:
            identifier = f"user:{user_info['user_id']}"
            user_role = user_info.get('role')
        else:
            identifier = f"ip:{client_ip}"
            user_role = None
        
        try:
            # Check endpoint-specific rate limits
            endpoint_limiter = get_endpoint_rate_limiter()
            result = await endpoint_limiter.check_endpoint_limit(
                identifier=identifier,
                method=method,
                path=path,
                user_role=user_role
            )
            
            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Auth rate limit exceeded. Please try again later.",
                    headers={
                        "Retry-After": str(result.retry_after or 60),
                        "X-RateLimit-Type": "auth-endpoint",
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "X-RateLimit-Reset": str(int(result.reset_time))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            self._add_rate_limit_headers(response, result)
            
            return response
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            
            # Log error but don't block request if rate limiter fails
            logger.error(f"Rate limiting error: {e}")
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address, handling proxy headers"""
        
        # Check for forwarded IP headers (common in load balancers/proxies)
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
                    "role": payload.get("role", AuthRole.CLIENT.value)
                }
            
        except Exception as e:
            logger.debug(f"Failed to extract user from request: {e}")
        
        return None
    
    def _add_rate_limit_headers(self, response, result: RateLimitResult):
        """Add rate limiting information to response headers"""
        
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_time))
        response.headers["X-RateLimit-Window"] = "60"  # 60 seconds
        response.headers["X-RateLimit-Scope"] = "auth-endpoints"