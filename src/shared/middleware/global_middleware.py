"""
Global Middleware Setup

Centralized configuration and setup of all global middleware components.
This ensures consistent middleware ordering and configuration across the application.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.shared.simple_config import AppConfig
from src.shared.middleware.security_headers import SecurityHeadersMiddleware
from src.shared.middleware.request_logging import RequestLoggingMiddleware
from src.shared.middleware.error_handling import GlobalErrorHandlingMiddleware
from src.shared.middleware.security_logging import SecurityLoggingMiddleware

logger = logging.getLogger(__name__)


def setup_global_middleware(app: FastAPI, config: AppConfig) -> None:
    """
    Setup global middleware for the entire application.
    
    Middleware order is important! They are applied in REVERSE order for responses.
    
    Order (first to last):
    1. CORS - Handle preflight requests first
    2. Security Headers - Add security headers to all responses
    3. Trusted Host - Validate host headers (production only)
    4. Request Logging - Log all requests and responses
    5. Compression - Compress responses (before content headers)
    6. Error Handling - Catch any unhandled exceptions (last)
    
    Args:
        app: FastAPI application instance
        config: Global configuration object
    """
    
    logger.info("Setting up global middleware...")
    
    # 1. CORS Middleware (FIRST - handles preflight OPTIONS requests)
    _setup_cors_middleware(app, config)
    
    # 2. Security Headers Middleware
    _setup_security_headers_middleware(app, config)
    
    # 3. Trusted Host Middleware (production only)
    _setup_trusted_host_middleware(app, config)
    
    # 4. Security Event Logging Middleware
    _setup_security_logging_middleware(app, config)
    
    # 5. Request Logging Middleware
    _setup_request_logging_middleware(app, config)
    
    # 6. Compression Middleware
    _setup_compression_middleware(app, config)
    
    # 7. Global Error Handling Middleware (LAST - catches everything)
    _setup_error_handling_middleware(app, config)
    
    logger.info("Global middleware setup completed")


def _setup_cors_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup CORS middleware"""
    
    # Simple CORS setup for development
    cors_origins = ["http://localhost:3000", "http://localhost:8000"] if config.debug else []
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info(f"CORS middleware configured with origins: {cors_origins}")


def _setup_security_headers_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup security headers middleware"""
    
    app.add_middleware(
        SecurityHeadersMiddleware,
        config=config
    )
    
    logger.info("Security headers middleware configured")


def _setup_trusted_host_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup trusted host middleware (production only)"""
    
    if config.environment == "production":
        # In production, you would set specific allowed hosts
        allowed_hosts = ["*"]  # This should be configured based on your production setup
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        logger.info(f"Trusted host middleware configured for hosts: {allowed_hosts}")
    else:
        logger.info("Trusted host middleware skipped (not production)")


def _setup_request_logging_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup request logging middleware"""
    
    # Enable request logging in debug mode
    if config.debug:
        app.add_middleware(
            RequestLoggingMiddleware,
            config=config
        )
        logger.info("Request logging middleware configured")
    else:
        logger.info("Request logging middleware skipped (disabled)")


def _setup_compression_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup response compression middleware"""
    
    # Enable GZIP compression in production
    if config.environment == "production":
        app.add_middleware(
            GZipMiddleware,
            minimum_size=1000
        )
        logger.info("GZIP compression middleware configured (min size: 1000)")
    else:
        logger.info("GZIP compression middleware skipped (disabled in development)")


def _setup_security_logging_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup security event logging middleware"""
    
    # Enable security logging if specified in config
    enable_security_logging = getattr(config, 'enable_security_logging', True)
    
    if enable_security_logging:
        app.add_middleware(
            SecurityLoggingMiddleware,
            enable_detailed_logging=config.debug
        )
        logger.info("Security event logging middleware configured")
    else:
        logger.info("Security event logging middleware skipped (disabled)")


def _setup_error_handling_middleware(app: FastAPI, config: AppConfig) -> None:
    """Setup global error handling middleware"""
    
    app.add_middleware(
        GlobalErrorHandlingMiddleware,
        debug=config.debug
    )
    
    logger.info(f"Global error handling middleware configured (debug={config.debug})")


def get_middleware_info() -> dict:
    """Get information about configured middleware (for debugging)"""
    
    return {
        "middleware_order": [
            "CORSMiddleware (global)",
            "SecurityHeadersMiddleware (global)",
            "TrustedHostMiddleware (global, production only)",
            "RequestLoggingMiddleware (global)",
            "GZipMiddleware (global)",
            "GlobalErrorHandlingMiddleware (global)",
            "Feature-specific middleware (router-level)",
        ],
        "description": "Middleware is applied in the order listed above. Feature-specific middleware is applied at the router level and only affects routes within that feature."
    }