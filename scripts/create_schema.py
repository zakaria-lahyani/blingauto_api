#!/usr/bin/env python
"""Create database schema from SQLAlchemy models."""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine

# Import all models
from app.features.auth.adapters.models import *
from app.features.services.adapters.models import *
from app.features.vehicles.adapters.models import *
from app.features.bookings.adapters.models import *
from app.features.facilities.adapters.models import *
from app.features.scheduling.adapters.models import *
from app.features.staff.adapters.models import *
from app.features.walkins.adapters.models import *
from app.features.inventory.adapters.models import *
from app.features.expenses.adapters.models import *

# Import base
from app.core.db import Base

# Get database URL
database_url = os.getenv("DATABASE_URL", "postgresql://blingauto_user:blingauto_pass@blingauto-postgres:5432/blingauto")
# Remove asyncpg for sync engine
database_url = database_url.replace("+asyncpg", "")

print("Creating database schema...")
print(f"Database URL: {database_url.replace('blingauto_pass', '***')}")

# Create engine
engine = create_engine(database_url)

# Create all tables
Base.metadata.create_all(engine)

print("✓ Schema created successfully!")
print(f"✓ Created {len(Base.metadata.tables)} tables")
