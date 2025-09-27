#!/usr/bin/env python3
"""
Standalone Car Wash API with Feature-Based Auth Module

This demonstrates how to integrate the refactored auth module
into any FastAPI application with just a few lines of code.

Usage:
    python main.py

The auth module provides complete authentication with:
- User registration/login with email verification
- Password reset functionality
- Account lockout protection 
- JWT token rotation
- Role-based access control (Admin, Manager, Washer, Client)
- Rate limiting per user role
- Admin setup automation
"""

import sys
import asyncio
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the refactored_api directory
current_dir = Path(__file__).parent
env_file = current_dir / ".env"
print(f"[DEBUG] Loading env from: {env_file}")
print(f"[DEBUG] Env file exists: {env_file.exists()}")

# Force override system environment with .env file values
load_dotenv(env_file, override=True)

# Explicitly set critical environment variables from .env to override system defaults
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key == 'AUTH_JWT_SECRET_KEY':
                    os.environ[key] = value
                    print(f"[DEBUG] Override {key} from .env file")
print(f"[DEBUG] Current AUTH_JWT_SECRET_KEY: {os.environ.get('AUTH_JWT_SECRET_KEY', 'NOT SET')[:20]}...")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Import the auth module - This is all you need!
from src.features.auth import AuthModule, AuthConfig, AuthRole, AuthUser
from src.features.services import services_module
from src.shared.database import init_database

# Import global middleware setup
from src.shared.middleware import setup_global_middleware
from src.shared.config import GlobalConfig

# Import services
from src.shared.services.email_service import init_email_service
from src.shared.services.secrets_manager import init_secrets_manager
from src.shared.services.cache_service import init_cache_service
from src.shared.services.rate_limiter import init_rate_limiter
from src.shared.services.encryption_service import init_encryption_service

# Global auth module instance
auth_module = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    # Startup
    print("[STARTUP] Initializing services...")
    
    # Initialize secrets manager first
    init_secrets_manager()
    print("[SUCCESS] Secrets manager initialized")
    
    # Load secrets into auth config
    await auth_module.config.load_secrets()
    print("[SUCCESS] Secrets loaded")
    
    # Validate configuration
    auth_module.config.validate_required_secrets()
    is_ready, issues = auth_module.config.is_production_ready()
    if not is_ready:
        print(f"[WARNING] Configuration issues: {issues}")
    else:
        print("[SUCCESS] Configuration is production ready")
    
    # Create all database tables from all features
    from src.shared.database import create_all_tables
    await create_all_tables()
    print("[SUCCESS] All database tables created successfully")
    
    # Initialize auth module
    await auth_module.initialize()
    print("[SUCCESS] Auth module initialized and ready!")
    
    # Initialize services module
    await services_module.initialize()
    print("[SUCCESS] Services module initialized and ready!")
    
    print(f"[DOCS] API documentation: http://localhost:8001/docs")
    print(f"[AUTH] Auth endpoints available at: /auth/*")
    print(f"[SERVICES] Services endpoints available at: /services/*")
    print(f"[FEATURES] Features enabled: {list(auth_module.get_feature_status().keys())}")
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Cleaning up services...")
    # Add cleanup code here if needed


def create_app() -> FastAPI:
    """Create FastAPI app with auth module integrated"""
    
    # Create FastAPI app
    app = FastAPI(
        lifespan=lifespan,
        title="Car Wash API",
        description="Feature-based API with secure distributed architecture",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Setup global middleware (CORS, security headers, logging, etc.)
    global_config = GlobalConfig()
    setup_global_middleware(app, global_config)
    
    # Initialize database with SSL/TLS enforcement
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback for development - use environment variables
        db_user = os.getenv("POSTGRES_USER", "carwash")
        db_password = os.getenv("POSTGRES_PASSWORD", "password")
        db_name = os.getenv("POSTGRES_DB", "carwash_db")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        
        database_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        print(f"[WARNING] Using constructed database URL from environment variables")
    
    init_database(database_url)
    print(f"[SUCCESS] Database initialized with security configurations")
    
    # Create auth configuration
    global auth_module
    auth_config = AuthConfig()
    
    # Initialize distributed cache service
    redis_url = auth_config.redis_url or os.getenv("REDIS_URL")
    if redis_url:
        cache_service = init_cache_service(redis_url)
        print(f"[SUCCESS] Cache service initialized with Redis")
        
        # Initialize rate limiter with Redis
        # We need to get the Redis client from the cache service
        redis_client = cache_service.provider._redis if hasattr(cache_service.provider, '_redis') else None
        if redis_client:
            init_rate_limiter(redis_client)
            print(f"[SUCCESS] Rate limiter initialized with Redis")
        else:
            # Lazy initialize Redis client for rate limiter
            async def init_redis_rate_limiter():
                from redis.asyncio import from_url
                redis_client = from_url(redis_url)
                init_rate_limiter(redis_client)
            
            # Store for later initialization
            app.state.init_redis_rate_limiter = init_redis_rate_limiter
    else:
        # Fallback to in-memory for development
        init_cache_service()
        init_rate_limiter()
        print(f"[WARNING] Using in-memory cache and rate limiting (not recommended for production)")
    
    # Initialize encryption service for sensitive data
    encryption_key = os.getenv("ENCRYPTION_KEY") or os.getenv("AUTH_ENCRYPTION_KEY")
    if encryption_key:
        init_encryption_service(encryption_key)
        print(f"[SUCCESS] Encryption service initialized")
    else:
        print(f"[WARNING] No encryption key provided - refresh tokens will not be encrypted")
    
    # Initialize email service with auth config
    email_config = {
        "email_provider": auth_config.email_provider,
        "smtp_host": auth_config.smtp_host,
        "smtp_port": auth_config.smtp_port,
        "smtp_username": auth_config.smtp_username,
        "smtp_password": auth_config.smtp_password,
        "smtp_use_tls": auth_config.smtp_use_tls,
        "from_email": auth_config.from_email,
        "support_email": auth_config.support_email,
        "app_url": auth_config.app_url
    }
    init_email_service(email_config)
    print(f"[SUCCESS] Email service initialized")
    
    # Create and setup auth module
    auth_module = AuthModule(auth_config)
    auth_module.setup(app, prefix="/auth")
    
    # Store auth module in app state for access in endpoints
    app.state.auth = auth_module
    app.state.services = services_module
    
    # Setup services router (public endpoints only for now)
    from src.features.services.presentation.api.public_router import router as services_router
    app.include_router(services_router)
    
    # Add basic health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "auth_features": auth_module.get_feature_status(),
            "version": "2.0.0"
        }
    
    # Add root endpoint with API info
    @app.get("/")
    async def root():
        """API information"""
        return {
            "name": "Car Wash API - Feature-Based Architecture",
            "version": "2.0.0",
            "architecture": "Hybrid middleware approach",
            "auth": "Standalone auth module with feature-specific middleware",
            "docs": "/docs",
            "health": "/health",
            "auth_endpoints": "/auth/docs (see /docs for full list)",
            "features": list(auth_module.get_feature_status().keys()),
            "middleware": {
                "global": "CORS, Security Headers, Request Logging, Compression, Error Handling",
                "auth_specific": "Rate Limiting, Security Logging"
            },
            "examples": {
                "public": "/",
                "authenticated": "/profile",
                "admin_only": "/admin/users",
                "manager_plus": "/manager/reports", 
                "custom_role": "/washer/dashboard"
            }
        }
    
    # EXAMPLE: Custom endpoints using auth dependencies
    # These demonstrate how easy it is to add protected endpoints
    
    @app.get("/profile")
    async def get_profile(current_user: AuthUser = Depends(auth_module.get_current_user)):
        """Get current user profile - REQUIRES AUTHENTICATION"""
        return {
            "message": "This endpoint requires authentication",
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "role": current_user.role.value,
                "email_verified": current_user.email_verified
            }
        }
    
    @app.get("/admin/users")
    async def admin_users(current_user: AuthUser = Depends(auth_module.get_current_admin)):
        """Admin-only endpoint - REQUIRES ADMIN ROLE"""
        return {
            "message": "This endpoint requires admin role",
            "admin": current_user.email,
            "note": "Only admins can access this endpoint"
        }
    
    @app.get("/manager/reports")
    async def manager_reports(current_user: AuthUser = Depends(auth_module.get_current_manager)):
        """Manager+ endpoint - REQUIRES MANAGER OR ADMIN ROLE"""
        return {
            "message": "This endpoint requires manager or admin role",
            "user": current_user.email,
            "role": current_user.role.value,
            "note": "Managers and admins can access this endpoint"
        }
    
    @app.get("/washer/dashboard")
    async def washer_dashboard(current_user: AuthUser = Depends(auth_module.require_role(AuthRole.WASHER))):
        """Washer-only endpoint - REQUIRES SPECIFIC WASHER ROLE"""
        return {
            "message": "This endpoint requires washer role specifically",
            "washer": current_user.email,
            "note": "Only washers can access this endpoint"
        }
    
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    print("=" * 60)
    print("[START] STARTING CAR WASH API - HYBRID MIDDLEWARE ARCHITECTURE")
    print("=" * 60)
    print("[AUTH] Authentication: Standalone auth module")
    print("[DB] Database: PostgreSQL with async support")
    print("[ARCH] Architecture: Feature-based with hybrid middleware")
    print("[MIDDLEWARE] Global: CORS, Security, Logging, Compression")
    print("[MIDDLEWARE] Feature: Rate limiting (auth only), Security logging")
    print("[DOCS] Documentation: http://localhost:8000/docs")
    print("=" * 60)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )