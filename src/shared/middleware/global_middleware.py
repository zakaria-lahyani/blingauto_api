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

from src.shared.config import GlobalConfig
from src.shared.middleware.security_headers import SecurityHeadersMiddleware
from src.shared.middleware.request_logging import RequestLoggingMiddleware
from src.shared.middleware.error_handling import GlobalErrorHandlingMiddleware

logger = logging.getLogger(__name__)


def setup_global_middleware(app: FastAPI, config: GlobalConfig) -> None:
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
    
    # 4. Request Logging Middleware
    _setup_request_logging_middleware(app, config)
    
    # 5. Compression Middleware
    _setup_compression_middleware(app, config)
    
    # 6. Global Error Handling Middleware (LAST - catches everything)
    _setup_error_handling_middleware(app, config)
    
    logger.info("Global middleware setup completed")


def _setup_cors_middleware(app: FastAPI, config: GlobalConfig) -> None:
    """Setup CORS middleware"""
    
    cors_origins = config.get_cors_origins()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
        expose_headers=config.cors.expose_headers,
    )
    
    logger.info(f"CORS middleware configured with origins: {cors_origins}")


def _setup_security_headers_middleware(app: FastAPI, config: GlobalConfig) -> None:
    """Setup security headers middleware"""
    
    app.add_middleware(
        SecurityHeadersMiddleware,
        config=config.security
    )
    
    logger.info("Security headers middleware configured")


def _setup_trusted_host_middleware(app: FastAPI, config: GlobalConfig) -> None:
    """Setup trusted host middleware (production only)"""
    
    if config.is_production and config.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config.allowed_hosts
        )
        logger.info(f"Trusted host middleware configured for hosts: {config.allowed_hosts}")
    else:
        logger.info("Trusted host middleware skipped (not production or no allowed hosts)")


def _setup_request_logging_middleware(app: FastAPI, config: GlobalConfig) -> None:
    """Setup request logging middleware"""
    
    if config.logging.enable_request_logging:
        app.add_middleware(
            RequestLoggingMiddleware,
            config=config.logging
        )
        logger.info("Request logging middleware configured")
    else:
        logger.info("Request logging middleware skipped (disabled)")


def _setup_compression_middleware(app: FastAPI, config: GlobalConfig) -> None:
    """Setup response compression middleware"""
    
    if config.compression.enable_gzip:
        app.add_middleware(
            GZipMiddleware,
            minimum_size=config.compression.gzip_minimum_size
        )
        logger.info(f"GZIP compression middleware configured (min size: {config.compression.gzip_minimum_size})")
    else:
        logger.info("GZIP compression middleware skipped (disabled)")


def _setup_error_handling_middleware(app: FastAPI, config: GlobalConfig) -> None:
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