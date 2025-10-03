"""
HTTP API Interface - FastAPI application factory
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.settings import settings
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.security_headers import SecurityHeadersMiddleware
from app.core.middleware.rate_limit import RateLimitMiddleware
from app.core.errors.handlers import register_error_handlers
from app.interfaces.health import router as health_router
from app.interfaces.openapi import configure_openapi
from app.shared.auth import register_auth_adapter

# Import all models to ensure relationships are properly configured
# This must be imported before any feature routers
import app.core.db.models  # noqa: F401

# Feature routers - each feature provides its own router
try:
    from app.features.auth.api.router import router as auth_router
    print("Successfully loaded auth router")
except ImportError as e:
    print(f"Failed to load auth router: {e}")
    from fastapi import APIRouter
    auth_router = APIRouter()
    
try:
    from app.features.bookings.api.router import router as bookings_router
    print("Successfully loaded bookings router")
except ImportError as e:
    print(f"Failed to load bookings router: {e}")
    from fastapi import APIRouter
    bookings_router = APIRouter()

try:
    from app.features.services.api.router import router as services_router
    print("Successfully loaded services router")
except ImportError as e:
    print(f"Failed to load services router: {e}")
    from fastapi import APIRouter
    services_router = APIRouter()

try:
    from app.features.vehicles.api.router import router as vehicles_router
    print("Successfully loaded vehicles router")
except ImportError as e:
    print(f"Failed to load vehicles router: {e}")
    from fastapi import APIRouter
    vehicles_router = APIRouter()

# Pricing feature removed
# pricing_router is no longer available

try:
    from app.features.scheduling.api.router import router as scheduling_router
    print("Successfully loaded scheduling router")
except ImportError as e:
    print(f"Failed to load scheduling router: {e}")
    from fastapi import APIRouter
    scheduling_router = APIRouter()

try:
    from app.features.facilities.api import wash_bays_router, mobile_teams_router
    print("Successfully loaded facilities routers")
except ImportError as e:
    print(f"Failed to load facilities routers: {e}")
    from fastapi import APIRouter
    wash_bays_router = APIRouter()
    mobile_teams_router = APIRouter()

try:
    from app.features.staff.api.router import router as staff_router
    print("Successfully loaded staff router")
except ImportError as e:
    print(f"Failed to load staff router: {e}")
    from fastapi import APIRouter
    staff_router = APIRouter()

try:
    from app.features.walkins.api.router import router as walkins_router
    print("Successfully loaded walkins router")
except ImportError as e:
    print(f"Failed to load walkins router: {e}")
    from fastapi import APIRouter
    walkins_router = APIRouter()

try:
    from app.features.inventory.api.router import router as inventory_router
    print("Successfully loaded inventory router")
except ImportError as e:
    print(f"Failed to load inventory router: {e}")
    from fastapi import APIRouter
    inventory_router = APIRouter()

try:
    from app.features.expenses.api.router import router as expenses_router
    print("Successfully loaded expenses router")
except ImportError as e:
    print(f"Failed to load expenses router: {e}")
    from fastapi import APIRouter
    expenses_router = APIRouter()

try:
    from app.features.analytics.api.router import router as analytics_router
    print("Successfully loaded analytics router")
except ImportError as e:
    print(f"Failed to load analytics router: {e}")
    from fastapi import APIRouter
    analytics_router = APIRouter()


def _setup_auth_adapter():
    """
    NOTE: This function is deprecated and does nothing.
    Authentication now uses per-request dependency injection via get_auth_adapter.
    Keeping this function to avoid breaking the startup flow.
    """
    print("Authentication is configured to use per-request dependency injection")
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Car Wash Management System API",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )

    # Register authentication adapter for shared dependencies
    _setup_auth_adapter()

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Add custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    if settings.rate_limit_enabled:
        app.add_middleware(RateLimitMiddleware)
    
    # Setup error handlers
    register_error_handlers(app)
    
    # Include routers
    # Health endpoints (no versioning, no prefix)
    app.include_router(health_router, tags=["Health"])
    
    # API v1 endpoints
    API_V1_PREFIX = "/api/v1"
    app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
    app.include_router(bookings_router, prefix=f"{API_V1_PREFIX}/bookings", tags=["Bookings"])
    app.include_router(services_router, prefix=f"{API_V1_PREFIX}/services", tags=["Services"])
    app.include_router(vehicles_router, prefix=f"{API_V1_PREFIX}/vehicles", tags=["Vehicles"])
    # Pricing router removed
    # app.include_router(pricing_router, prefix=f"{API_V1_PREFIX}/pricing", tags=["Pricing"])
    app.include_router(scheduling_router, prefix=f"{API_V1_PREFIX}/scheduling", tags=["Scheduling"])
    app.include_router(wash_bays_router, prefix=f"{API_V1_PREFIX}/facilities/wash-bays", tags=["Facilities - Wash Bays"])
    app.include_router(mobile_teams_router, prefix=f"{API_V1_PREFIX}/facilities/mobile-teams", tags=["Facilities - Mobile Teams"])
    app.include_router(staff_router, prefix=f"{API_V1_PREFIX}/staff", tags=["Staff Management"])
    app.include_router(walkins_router, prefix=f"{API_V1_PREFIX}/walkins", tags=["Walk-in Services"])
    app.include_router(inventory_router, prefix=f"{API_V1_PREFIX}/inventory", tags=["Inventory Management"])
    app.include_router(expenses_router, prefix=f"{API_V1_PREFIX}/expenses", tags=["Expense Management"])
    app.include_router(analytics_router, prefix=f"{API_V1_PREFIX}/analytics", tags=["Analytics & Reporting"])

    # Configure OpenAPI documentation
    configure_openapi(app)
    
    return app