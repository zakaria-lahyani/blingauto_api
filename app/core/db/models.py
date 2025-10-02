"""
Central registry for all database models.
This ensures all models are properly imported for migrations.
"""

# Core database setup
from .base import Base

# Auth feature models
try:
    from app.features.auth.adapters.models import (
        UserModel, PasswordResetTokenModel, EmailVerificationTokenModel, RefreshTokenModel
    )
    print("✓ Auth models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import auth models: {e}")

# Services feature models
try:
    from app.features.services.adapters.models import (
        Category, Service
    )
    print("✓ Services models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import services models: {e}")

# Vehicles feature models
try:
    from app.features.vehicles.adapters.models import (
        Vehicle
    )
    print("✓ Vehicles models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import vehicles models: {e}")

# Bookings feature models
try:
    from app.features.bookings.adapters.models import (
        Booking, BookingService
    )
    print("✓ Bookings models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import bookings models: {e}")

# Scheduling feature models
try:
    from app.features.scheduling.adapters.models import (
        WashBay, MobileTeam, TimeSlot, SchedulingConstraints, BusinessHours
    )
    print("✓ Scheduling models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import scheduling models: {e}")

# Export metadata for migrations
metadata = Base.metadata

# Model registry for introspection - only include successfully imported models
ALL_MODELS = []

# Add auth models if imported
try:
    ALL_MODELS.extend([UserModel, PasswordResetTokenModel, EmailVerificationTokenModel, RefreshTokenModel])
except NameError:
    pass

# Add services models if imported
try:
    ALL_MODELS.extend([Category, Service])
except NameError:
    pass

# Add vehicles models if imported
try:
    ALL_MODELS.append(Vehicle)
except NameError:
    pass

# Add bookings models if imported
try:
    ALL_MODELS.extend([Booking, BookingService])
except NameError:
    pass

# Add scheduling models if imported
try:
    ALL_MODELS.extend([WashBay, MobileTeam, TimeSlot, SchedulingConstraints, BusinessHours])
except NameError:
    pass

print(f"📊 Total models registered: {len(ALL_MODELS)}")

__all__ = [
    "Base", "metadata", "ALL_MODELS",
]