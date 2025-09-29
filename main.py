#!/usr/bin/env python3
"""
Car Wash API - Clean Architecture

A clean, maintainable, and scalable API built with feature-based architecture,
auto-discovery, and minimal dependencies.

Key Principles Applied:
- Single Responsibility Principle
- Open/Closed Principle  
- Dependency Inversion Principle
- Clean Architecture
- SOLID Principles
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.shared.simple_config import get_config
from src.shared.simple_database import (
    init_database, 
    create_tables, 
    close_database, 
    get_db_session
)
from src.shared.simple_events import publish_event
from src.shared.feature_discovery import FeatureInfo, get_enabled_features
# Skip complex middleware for now - use simple error handling

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApplicationLifecycleManager:
    """Manages application startup and shutdown lifecycle"""
    
    def __init__(self):
        self.features: List[FeatureInfo] = []
        self.initialized = False
    
    async def startup(self) -> None:
        """Execute startup sequence"""
        try:
            logger.info("🚀 Starting Car Wash API - Clean Architecture")
            
            await self._initialize_configuration()
            await self._initialize_database()
            await self._discover_and_initialize_features()
            await self._publish_startup_event()
            
            self.initialized = True
            logger.info("🎉 Application started successfully")
            
        except Exception as e:
            logger.error(f"💥 Startup failed: {e}", exc_info=True)
            raise
    
    async def shutdown(self) -> None:
        """Execute shutdown sequence"""
        try:
            logger.info("🛑 Shutting down application...")
            
            await self._cleanup_features()
            await self._close_database()
            await self._publish_shutdown_event()
            
            logger.info("✅ Application shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}", exc_info=True)
    
    async def _initialize_configuration(self) -> None:
        """Initialize application configuration"""
        config = get_config()
        logger.info(f"📋 Environment: {config.environment}")
        logger.info(f"🔧 Debug mode: {config.debug}")
    
    async def _initialize_database(self) -> None:
        """Initialize database connection and tables"""
        init_database()
        await create_tables()
        logger.info("🗄️ Database initialized")
        
        # Test database connection
        from sqlalchemy import text
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified")
    
    async def _discover_and_initialize_features(self) -> None:
        """Discover and initialize all enabled features"""
        self.features = get_enabled_features()
        logger.info(f"🔍 Discovered {len(self.features)} enabled features: {[f.name for f in self.features]}")
        
        for feature in self.features:
            await self._initialize_feature(feature)
    
    async def _initialize_feature(self, feature: FeatureInfo) -> None:
        """Initialize a single feature"""
        try:
            await feature.initialize()
            logger.info(f"✅ Feature '{feature.name}' initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize feature '{feature.name}': {e}")
            raise
    
    async def _cleanup_features(self) -> None:
        """Clean up all features"""
        for feature in self.features:
            try:
                await feature.shutdown()
                logger.info(f"🧹 Feature '{feature.name}' cleaned up")
            except Exception as e:
                logger.error(f"⚠️ Error cleaning up feature '{feature.name}': {e}")
    
    async def _close_database(self) -> None:
        """Close database connections"""
        await close_database()
        logger.info("🗄️ Database connections closed")
    
    async def _publish_startup_event(self) -> None:
        """Publish application startup event"""
        config = get_config()
        await publish_event("app.started", {
            "features": [f.name for f in self.features],
            "environment": config.environment,
            "version": config.version
        }, source="application")
    
    async def _publish_shutdown_event(self) -> None:
        """Publish application shutdown event"""
        await publish_event("app.stopped", {
            "features": [f.name for f in self.features]
        }, source="application")


class FeatureRouterManager:
    """Manages feature router registration"""
    
    def __init__(self, app: FastAPI):
        self.app = app
    
    def register_feature_routers(self, features: List[FeatureInfo]) -> None:
        """Register routers for all features"""
        for feature in features:
            self._register_feature_router(feature)
    
    def _register_feature_router(self, feature: FeatureInfo) -> None:
        """Register router for a single feature"""
        try:
            router = feature.get_router()
            if router is None:
                logger.warning(f"⚠️ Feature '{feature.name}' has no router")
                return
            
            prefix = self._determine_router_prefix(router, feature)
            self.app.include_router(
                router,
                prefix=prefix if not router.prefix else ""
            )
            logger.info(f"📍 Router for '{feature.name}' included with prefix '{prefix}'")
            
        except Exception as e:
            logger.error(f"❌ Failed to include router for feature '{feature.name}': {e}")
    
    def _determine_router_prefix(self, router, feature: FeatureInfo) -> str:
        """Determine the appropriate prefix for a router"""
        if hasattr(router, 'prefix') and router.prefix:
            return router.prefix
        return f"/{feature.name}"


def create_lifespan_manager(lifecycle_manager: ApplicationLifecycleManager):
    """Create lifespan context manager"""
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await lifecycle_manager.startup()
        yield
        await lifecycle_manager.shutdown()
    
    return lifespan


def configure_error_handling(app: FastAPI) -> None:
    """Configure basic error handling"""
    config = get_config()
    
    # First, handle our standardized exceptions
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP exception in {request.method} {request.url}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": "2025-09-29T00:00:00Z",
                "path": str(request.url.path)
            }
        )
    
    # Handle our custom standardized exceptions
    try:
        from src.shared.exceptions import (
            ValidationError, AuthenticationError, AuthorizationError, 
            ResourceNotFoundError, BusinessLogicError, InternalServerError
        )
        
        @app.exception_handler(ValidationError)
        async def validation_error_handler(request: Request, exc: ValidationError):
            logger.warning(f"Validation error in {request.method} {request.url}: {exc.detail}")
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        
        @app.exception_handler(AuthenticationError)
        async def auth_error_handler(request: Request, exc: AuthenticationError):
            logger.warning(f"Auth error in {request.method} {request.url}: {exc.detail}")
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        
        @app.exception_handler(BusinessLogicError)
        async def business_error_handler(request: Request, exc: BusinessLogicError):
            logger.warning(f"Business logic error in {request.method} {request.url}: {exc.detail}")
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        
        @app.exception_handler(InternalServerError)
        async def internal_error_handler(request: Request, exc: InternalServerError):
            logger.error(f"Internal error in {request.method} {request.url}: {exc.detail}")
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        
        logger.info("✅ Standardized exception handlers configured")
        
    except ImportError as e:
        logger.warning(f"Could not import standardized exceptions: {e}")
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions with detailed debugging"""
        logger.error(f"Unhandled exception in {request.method} {request.url}: {exc}", exc_info=True)
        
        # Provide detailed error information for debugging
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "message": str(exc) if config.debug else "An unexpected error occurred",
                "type": type(exc).__name__,
                "status_code": 500,
                "timestamp": "2025-09-29T00:00:00Z",  # Simplified timestamp
                "path": str(request.url.path)
            }
        )
    
    logger.info("✅ Basic error handling configured")


def create_health_endpoints(app: FastAPI, lifecycle_manager: ApplicationLifecycleManager) -> None:
    """Create health check and info endpoints"""
    
    @app.get("/")
    async def api_info():
        """API information and feature status"""
        config = get_config()
        
        return {
            "name": config.app_name,
            "version": config.version,
            "environment": config.environment,
            "architecture": "Clean Architecture with Auto-Discovery",
            "features": {
                "enabled": [f.name for f in lifecycle_manager.features],
                "total": len(lifecycle_manager.features)
            },
            "principles": [
                "Single Responsibility",
                "Open/Closed",
                "Dependency Inversion",
                "Clean Architecture"
            ],
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "events": "/events/stats"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Comprehensive health check"""
        try:
            config = get_config()
            
            # Test database
            from sqlalchemy import text
            async with get_db_session() as session:
                await session.execute(text("SELECT 1"))
            
            return {
                "status": "healthy",
                "timestamp": "2025-01-28T00:00:00Z",
                "environment": config.environment,
                "version": config.version,
                "features": {
                    "count": len(lifecycle_manager.features),
                    "enabled": [f.name for f in lifecycle_manager.features]
                },
                "database": "connected",
                "initialized": lifecycle_manager.initialized
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": "2025-01-28T00:00:00Z"
                }
            )


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application
    
    This function follows the Factory Pattern and applies Clean Architecture principles:
    - Single Responsibility: Each manager handles one concern
    - Dependency Inversion: Depends on abstractions, not concretions
    - Open/Closed: Easy to extend with new features
    """
    # Initialize lifecycle manager
    lifecycle_manager = ApplicationLifecycleManager()
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Car Wash API - Clean Architecture",
        description="A clean, maintainable, and scalable car wash management API",
        version="4.0.0",
        lifespan=create_lifespan_manager(lifecycle_manager),
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure error handling
    configure_error_handling(app)
    
    # Create health endpoints
    create_health_endpoints(app, lifecycle_manager)
    
    # Register feature routers
    features = get_enabled_features()
    router_manager = FeatureRouterManager(app)
    router_manager.register_feature_routers(features)
    
    return app


# Create the application instance
app = create_application()


def main() -> None:
    """Main entry point"""
    logger.info("🏁 Starting Car Wash API - Clean Architecture")
    logger.info("📚 Principles: SOLID, Clean Architecture, Auto-Discovery")
    logger.info("🔧 Dependency Management: Simplified Factory Pattern")
    logger.info("📁 Architecture: Feature-Based with Clean Separation")
    logger.info("🚀 Starting server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()