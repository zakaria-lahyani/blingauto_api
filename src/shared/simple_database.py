"""
Session de base de données simplifiée
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from contextlib import asynccontextmanager
import logging

from .simple_config import get_config
# Import the correct Base from shared.database
from .database.base import Base

logger = logging.getLogger(__name__)

# Engine et session factory globaux
_engine = None
_session_factory = None


def init_database():
    """Initialise le moteur de base de données"""
    global _engine, _session_factory
    
    config = get_config()
    
    _engine = create_async_engine(
        config.database_url,
        echo=config.debug,
        pool_pre_ping=True,
        pool_recycle=300
    )
    
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    logger.info("Database initialized")


async def create_tables():
    """Crée toutes les tables"""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    # Import all models through the registry to ensure they're registered with Base
    # This is crucial for table creation and proper relationship resolution
    logger.info("Importing database models...")
    
    # Import the models registry which loads all models in correct order
    from src.shared.database import models_registry
    
    # Now create tables with all models registered
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info(f"Database tables created. Registered tables: {', '.join(Base.metadata.tables.keys())}")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager pour les sessions de base de données"""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency pour les sessions de base de données"""
    async with get_db_session() as session:
        yield session


async def close_database():
    """Ferme les connexions de base de données"""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("Database connections closed")