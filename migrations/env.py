"""Alembic migration environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here for autogenerate support
try:
    from app.features.auth.infrastructure.models import *
except ImportError:
    pass

try:
    from app.features.services.infrastructure.models import *
except ImportError:
    pass

try:
    from app.features.vehicles.infrastructure.models import *
except ImportError:
    pass

try:
    from app.features.bookings.infrastructure.models import *
except ImportError:
    pass

try:
    from app.features.scheduling.adapters.models import *
except ImportError:
    pass

try:
    from app.features.staff.adapters.models import *
except ImportError:
    pass

try:
    from app.features.walkins.adapters.models import *
except ImportError:
    pass

try:
    from app.features.inventory.adapters.models import *
except ImportError:
    pass

try:
    from app.features.expenses.adapters.models import *
except ImportError:
    pass

# Import the base metadata
try:
    from app.core.database import Base
    target_metadata = Base.metadata
except ImportError:
    try:
        from app.core.db.base import Base
        target_metadata = Base.metadata
    except ImportError:
        target_metadata = None


def get_database_url():
    """Get database URL from environment or config."""
    # Try environment variable first
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    
    # Fall back to config
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()