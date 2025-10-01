"""Core dependency injection for the application."""

from app.core.db.session import AsyncSession
from app.core.db.unit_of_work import UnitOfWork


async def get_db_session() -> AsyncSession:
    """Get database session."""
    # This would be implemented with actual DB session management
    pass


async def get_unit_of_work() -> UnitOfWork:
    """Get unit of work."""
    # This would be implemented with actual UoW
    pass


async def get_cache_service():
    """Get cache service."""
    # This would be implemented with actual cache service
    pass


async def get_event_service():
    """Get event service."""
    # This would be implemented with actual event service
    pass


async def get_email_service():
    """Get email service."""
    # This would be implemented with actual email service
    pass


async def get_audit_service():
    """Get audit service."""
    # This would be implemented with actual audit service
    pass


# Re-export auth dependencies
from app.features.auth.api.dependencies import CurrentUser as get_current_user

__all__ = [
    "get_db_session",
    "get_unit_of_work", 
    "get_cache_service",
    "get_event_service",
    "get_email_service",
    "get_audit_service",
    "get_current_user",
]