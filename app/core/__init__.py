"""
Core infrastructure module.
Contains transversal technical components without business logic.
"""

from .config import settings
from .db import Base, engine, get_db, UnitOfWork
from .cache import redis_client, rate_limiter, distributed_lock
from .security import password_hasher, jwt_handler, Role, Permission, rbac_service
from .errors import register_error_handlers
from .middleware import register_middlewares
from .observability import health_checker, metrics_collector

__all__ = [
    "settings",
    "Base",
    "engine",
    "get_db",
    "UnitOfWork",
    "redis_client",
    "rate_limiter",
    "distributed_lock",
    "password_hasher",
    "jwt_handler",
    "Role",
    "Permission",
    "rbac_service",
    "register_error_handlers",
    "register_middlewares",
    "health_checker",
    "metrics_collector",
]