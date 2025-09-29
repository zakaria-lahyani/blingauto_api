"""
Database session management
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
import os
import logging

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine = None
_async_session_maker = None


def init_database(database_url: str = None):
    """Initialize database connection with SSL/TLS enforcement"""
    global _engine, _async_session_maker
    
    if not database_url:
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./refactored_carwash.db")
    
    # Ensure we're using the correct async driver for PostgreSQL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
    
    # Enforce SSL/TLS for PostgreSQL connections in production
    if "postgresql" in database_url:
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        # Check if SSL parameters are already in URL
        if "sslmode=" not in database_url and "ssl=" not in database_url:
            if environment == "production":
                # Require SSL in production
                separator = "&" if "?" in database_url else "?"
                database_url += f"{separator}sslmode=require"
                logger.info("SSL/TLS enforced for production PostgreSQL connection")
            elif environment != "development":
                # Prefer SSL in staging/test environments
                separator = "&" if "?" in database_url else "?"
                database_url += f"{separator}sslmode=prefer"
                logger.info("SSL/TLS preferred for PostgreSQL connection")
    
    logger.info(f"Initializing database: {database_url.split('@')[0]}@***")  # Hide credentials in logs
    
    # Validate that we have an async-compatible URL
    if "postgresql" in database_url and "asyncpg" not in database_url:
        raise ValueError(
            f"PostgreSQL URL must use asyncpg driver for async support. "
            f"Got: {database_url.split('@')[0]}@***. "
            f"Use: postgresql+asyncpg://..."
        )
    
    try:
        # Connection pool settings for security and performance
        connect_args = {}
        
        # Additional SSL settings for PostgreSQL
        if "postgresql" in database_url:
            # Set connection timeout
            connect_args.setdefault("server_settings", {})
            connect_args["server_settings"]["application_name"] = "carwash_api"
            
            # Set statement timeout to prevent long-running queries
            connect_args["server_settings"]["statement_timeout"] = "300000"  # 5 minutes
            
            # SSL verification settings for production
            environment = os.getenv("ENVIRONMENT", "development").lower()
            if environment == "production":
                connect_args["ssl"] = "require"
        
        _engine = create_async_engine(
            database_url, 
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_pre_ping=True,
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            connect_args=connect_args
        )
        _async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)
        logger.info("Database engine created successfully with security configurations")
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise


def get_engine():
    """Get database engine"""
    global _engine
    if _engine is None:
        init_database()
    return _engine


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """Get database session context manager"""
    global _async_session_maker
    
    if _async_session_maker is None:
        init_database()
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncSession:
    """FastAPI dependency for getting database session"""
    global _async_session_maker
    
    if _async_session_maker is None:
        init_database()
    
    async with _async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables():
    """Create all database tables from all features"""
    from src.shared.database.base import Base
    
    # Import all models to ensure they're registered with SQLAlchemy metadata
    _import_all_models()
    
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("All database tables created successfully")


def _import_all_models():
    """Import all database models from all features to register them with SQLAlchemy"""
    try:
        # Import auth models
        from src.features.auth.infrastructure.database.models import AuthUserModel
        logger.info("Auth models imported successfully")
        
        # Import services models
        from src.features.services.infrastructure.database.models import ServiceCategoryModel, ServiceModel
        logger.info("Services models imported successfully")
        
        # Import booking models
        from src.features.bookings.infrastructure.database.models import BookingModel, BookingServiceModel, BookingEventModel
        logger.info("Booking models imported successfully")
        
        # Import vehicle models
        from src.features.vehicles.infrastructure.database.models import VehicleModel
        logger.info("Vehicle models imported successfully")
        
        
    except ImportError as e:
        logger.warning(f"Some models could not be imported: {e}")
        # Continue anyway - tables for available features will still be created