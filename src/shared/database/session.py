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
    """Initialize database connection"""
    global _engine, _async_session_maker
    
    if not database_url:
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./refactored_carwash.db")
    
    # Ensure we're using the correct async driver for PostgreSQL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
    
    logger.info(f"Initializing database: {database_url}")
    
    # Validate that we have an async-compatible URL
    if "postgresql" in database_url and "asyncpg" not in database_url:
        raise ValueError(
            f"PostgreSQL URL must use asyncpg driver for async support. "
            f"Got: {database_url}. "
            f"Use: postgresql+asyncpg://..."
        )
    
    try:
        _engine = create_async_engine(
            database_url, 
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_pre_ping=True
        )
        _async_session_maker = async_sessionmaker(_engine, expire_on_commit=False)
        logger.info("Database engine created successfully")
        
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


async def create_all_tables():
    """Create all database tables"""
    from src.shared.database.base import Base
    
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)