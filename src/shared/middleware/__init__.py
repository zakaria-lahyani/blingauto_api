"""
Shared Middleware Components

This module provides global middleware components that apply to the entire application,
as opposed to feature-specific middleware that applies only to specific route groups.
"""

from src.shared.middleware.global_middleware import setup_global_middleware
from src.shared.middleware.security_headers import SecurityHeadersMiddleware
from src.shared.middleware.request_logging import RequestLoggingMiddleware
from src.shared.middleware.error_handling import GlobalErrorHandlingMiddleware

__all__ = [
    'setup_global_middleware',
    'SecurityHeadersMiddleware', 
    'RequestLoggingMiddleware',
    'GlobalErrorHandlingMiddleware'
]