"""
Auth Feature Middleware

Feature-specific middleware components for authentication.
These are applied only to auth routes (/auth/*) via router-level middleware.
"""

from src.features.auth.presentation.middleware.auth_rate_limiting import AuthRateLimitingMiddleware

__all__ = [
    'AuthRateLimitingMiddleware'
]