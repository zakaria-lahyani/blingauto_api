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

try:
    from app.features.pricing.api.router import router as pricing_router
    print("Successfully loaded pricing router")
except ImportError as e:
    print(f"Failed to load pricing router: {e}")
    from fastapi import APIRouter
    pricing_router = APIRouter()

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


def _setup_auth_adapter():
    """Setup and register the authentication adapter for shared dependencies."""
    try:
        from app.features.auth.adapters.http_auth import HttpAuthenticationAdapter
        from app.features.auth.use_cases.authenticate_user import AuthenticateUserUseCase
        from app.features.auth.use_cases.check_authorization import (
            CheckRoleUseCase, CheckPermissionUseCase, CheckStaffUseCase
        )
        from app.features.auth.adapters.repositories import UserRepository
        from app.features.auth.adapters.services import TokenService
        from app.core.db import get_db

        # Create instances (in production, use proper DI container)
        db = next(get_db())
        user_repo = UserRepository(db)
        token_service = TokenService()

        authenticate_use_case = AuthenticateUserUseCase(user_repo, token_service)
        check_role_use_case = CheckRoleUseCase()
        check_permission_use_case = CheckPermissionUseCase()
        check_staff_use_case = CheckStaffUseCase()

        adapter = HttpAuthenticationAdapter(
            authenticate_use_case,
            check_role_use_case,
            check_permission_use_case,
            check_staff_use_case,
        )

        # Register with shared auth dependencies
        register_auth_adapter(adapter)
        print("Successfully registered authentication adapter")

    except Exception as e:
        print(f"Warning: Failed to setup auth adapter: {e}")
        print("Authentication will not work until this is resolved")


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
    # Health endpoints (no versioning)
    app.include_router(health_router, prefix="/health", tags=["Health"])
    
    # API v1 endpoints
    API_V1_PREFIX = "/api/v1"
    app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
    app.include_router(bookings_router, prefix=f"{API_V1_PREFIX}/bookings", tags=["Bookings"])
    app.include_router(services_router, prefix=f"{API_V1_PREFIX}/services", tags=["Services"])
    app.include_router(vehicles_router, prefix=f"{API_V1_PREFIX}/vehicles", tags=["Vehicles"])
    app.include_router(pricing_router, prefix=f"{API_V1_PREFIX}/pricing", tags=["Pricing"])
    app.include_router(scheduling_router, prefix=f"{API_V1_PREFIX}/scheduling", tags=["Scheduling"])
    app.include_router(wash_bays_router, prefix=f"{API_V1_PREFIX}/facilities/wash-bays", tags=["Facilities - Wash Bays"])
    app.include_router(mobile_teams_router, prefix=f"{API_V1_PREFIX}/facilities/mobile-teams", tags=["Facilities - Mobile Teams"])
    
    # Configure OpenAPI documentation
    configure_openapi(app)
    
    return app