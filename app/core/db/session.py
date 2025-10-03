from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def create_db_engine():
    """Create async database engine."""
    if settings.environment == "testing":
        # Use NullPool for tests to avoid connection issues
        return create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            poolclass=NullPool,
        )
    else:
        # Use default async pool for production/development
        return create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
        )


# Create async engine and session factory
engine = create_db_engine()
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency to get database session."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except GeneratorExit:
        # Handle generator cleanup - rollback but don't raise
        await session.rollback()
    except Exception:
        await session.rollback()
        raise
    finally:
        # Ensure session is properly closed
        await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
