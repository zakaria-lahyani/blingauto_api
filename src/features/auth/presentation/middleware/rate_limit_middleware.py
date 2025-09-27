"""
Simple rate limiting middleware
"""
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from src.features.auth.config import AuthConfig
from src.features.auth.domain.enums import AuthRole

logger = logging.getLogger(__name__)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config
        self.requests = defaultdict(list)  # {ip: [timestamp, ...]}
        self.user_requests = defaultdict(list)  # {user_id: [timestamp, ...]}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        if not self.config.enable_rate_limiting:
            return await call_next(request)
        
        client_ip = request.client.host
        
        # Get user info if authenticated
        user_info = await self._get_user_from_request(request)
        
        # Apply rate limiting
        if not self._check_rate_limit(client_ip, user_info, request.url.path):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        return response
    
    def _check_rate_limit(self, client_ip: str, user_info: dict, path: str) -> bool:
        """Check if request should be rate limited"""
        
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Determine rate limit based on user role
        if user_info:
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
            
            # Check user-based rate limit
            user_requests = self.user_requests[user_id]
            recent_requests = [req for req in user_requests if req > minute_ago]
            
            if len(recent_requests) >= limit:
                return False
            
            # Record request
            recent_requests.append(now)
            self.user_requests[user_id] = recent_requests
        
        else:
            # Anonymous user - use IP-based limiting
            limit = self.config.client_rate_limit // 2  # Lower limit for anonymous
            
            ip_requests = self.requests[client_ip]
            recent_requests = [req for req in ip_requests if req > minute_ago]
            
            if len(recent_requests) >= limit:
                return False
            
            # Record request
            recent_requests.append(now)
            self.requests[client_ip] = recent_requests
        
        # Apply path-specific limits
        if path.startswith("/auth/login"):
            return self._check_auth_endpoint_limit(client_ip, 5)  # 5 login attempts per minute
        elif path.startswith("/auth/register"):
            return self._check_auth_endpoint_limit(client_ip, 3)  # 3 registration attempts per minute
        
        return True
    
    def _check_auth_endpoint_limit(self, client_ip: str, limit: int) -> bool:
        """Check rate limit for sensitive auth endpoints"""
        
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        auth_key = f"auth_{client_ip}"
        auth_requests = self.requests[auth_key]
        recent_requests = [req for req in auth_requests if req > minute_ago]
        
        if len(recent_requests) >= limit:
            return False
        
        recent_requests.append(now)
        self.requests[auth_key] = recent_requests
        return True
    
    async def _get_user_from_request(self, request: Request) -> dict:
        """Extract user info from request if authenticated"""
        
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            
            # Simple token decode (in production, use proper JWT verification)
            from ...infrastructure.security import JWTHandler
            jwt_handler = JWTHandler(self.config)
            payload = jwt_handler.verify_token(token)
            
            if payload and payload.get("type") == "access":
                return {
                    "user_id": payload.get("sub"),
                    "role": AuthRole(payload.get("role", AuthRole.CLIENT.value))
                }
            
        except Exception:
            pass
        
        return None


# ✅ REMOVED: Global setup function (was applying to entire app)
# Rate limiting is now applied directly to auth router only in auth_module.py
# This ensures rate limiting only affects /auth/* endpoints, not the entire application