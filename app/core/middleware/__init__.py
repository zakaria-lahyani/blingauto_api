from .request_id import RequestIdMiddleware
from .logging import LoggingMiddleware
from .cors import setup_cors
from .rate_limit import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware

__all__ = [
    "RequestIdMiddleware",
    "LoggingMiddleware",
    "setup_cors",
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
]


def register_middlewares(app):
    """Register all middlewares with the FastAPI app."""
    # Order matters: these are executed in reverse order for requests
    # and in forward order for responses
    
    # CORS should be early to handle preflight requests
    setup_cors(app)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware)
    
    # Request ID should be early to be available for other middlewares
    app.add_middleware(RequestIdMiddleware)
    
    # Logging should be last to log the complete request/response cycle
    app.add_middleware(LoggingMiddleware)