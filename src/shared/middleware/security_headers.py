"""
Security Headers Middleware

Adds security-related HTTP headers to all responses to improve application security.
Applied globally to all routes.
"""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.shared.config import SecurityConfig

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        logger.info("Security headers middleware initialized")
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response"""
        
        response = await call_next(request)
        
        # X-Content-Type-Options: Prevent MIME type sniffing
        if self.config.enable_x_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevent clickjacking
        if self.config.enable_x_frame_options:
            response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: Enable XSS filtering
        if self.config.enable_x_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: Control browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # Strict-Transport-Security: Force HTTPS
        if self.config.enable_hsts:
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Content-Security-Policy: Prevent XSS and injection attacks
        if self.config.enable_csp:
            response.headers["Content-Security-Policy"] = self.config.csp_policy
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        
        return response