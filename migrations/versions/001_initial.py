"""initial

Revision ID: 001
Revises:
Create Date: 2025-10-02 13:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables using SQLAlchemy metadata."""
    # Import all models to register them with Base.metadata
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from app.core.db import Base
    from app.features.auth.adapters import models as auth_models
    from app.features.services.adapters import models as services_models
    from app.features.vehicles.adapters import models as vehicles_models
    from app.features.bookings.adapters import models as bookings_models
    from app.features.facilities.adapters import models as facilities_models
    from app.features.staff.adapters import models as staff_models
    from app.features.walkins.adapters import models as walkins_models
    from app.features.inventory.adapters import models as inventory_models
    from app.features.expenses.adapters import models as expenses_models

    # Create all tables from metadata
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop all tables."""
    pass
