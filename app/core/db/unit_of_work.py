from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.core.db.session import AsyncSessionLocal


class UnitOfWork:
    """Async Unit of Work pattern implementation for transaction management."""

    def __init__(self, session_factory=AsyncSessionLocal):
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None

    async def __aenter__(self):
        self._session = self.session_factory()
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    @property
    def session(self) -> AsyncSession:
        if not self._session:
            raise RuntimeError("UnitOfWork context not active")
        return self._session

    async def commit(self):
        if self._session:
            await self._session.commit()

    async def rollback(self):
        if self._session:
            await self._session.rollback()

    async def refresh(self, instance):
        if self._session:
            await self._session.refresh(instance)

    @asynccontextmanager
    async def savepoint(self):
        """Create a savepoint for nested transactions."""
        if not self._session:
            raise RuntimeError("UnitOfWork context not active")

        async with self._session.begin_nested() as savepoint:
            try:
                yield
            except:
                await savepoint.rollback()
                raise


def get_unit_of_work() -> UnitOfWork:
    """Get a UnitOfWork instance for dependency injection."""
    return UnitOfWork()
