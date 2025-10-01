"""
Central registry for all database models.
This ensures all models are properly imported for migrations.
"""

# Core database setup
from .base import Base

# Auth feature models
try:
    from app.features.auth.infrastructure.models import (
        UserModel, SessionModel, EmailVerificationModel, 
        PasswordResetModel, LoginAttemptModel
    )
    print("✓ Auth models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import auth models: {e}")

# Services feature models  
try:
    from app.features.services.infrastructure.models import (
        Category, Service
    )
    print("✓ Services models imported successfully")
except ImportError as e:
    print(f"✗ Failed to import services models: {e}")

# Vehicles feature models
try:
    from app.features.vehicles.infrastructure.models import (
        Vehicle
    )
    print("✓ Vehicles models imported successfully") 
except ImportError as e:
    print(f"✗ Failed to import vehicles models: {e}")

# Bookings feature models
try:
    from app.features.bookings.infrastructure.models import (
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

# Model registry for introspection
ALL_MODELS = [
    # Auth models
    UserModel, SessionModel, EmailVerificationModel, 
    PasswordResetModel, LoginAttemptModel,
    
    # Services models
    Category, Service,
    
    # Vehicles models  
    Vehicle,
    
    # Bookings models
    Booking, BookingService,
    
    # Scheduling models
    WashBay, MobileTeam, TimeSlot, SchedulingConstraints, BusinessHours,
]

print(f"📊 Total models registered: {len(ALL_MODELS)}")

__all__ = [
    "Base", "metadata", "ALL_MODELS",
    # Auth models
    "UserModel", "SessionModel", "EmailVerificationModel", 
    "PasswordResetModel", "LoginAttemptModel",
    # Services models
    "Category", "Service", 
    # Vehicles models
    "Vehicle",
    # Bookings models
    "Booking", "BookingService",
    # Scheduling models
    "WashBay", "MobileTeam", "TimeSlot", "SchedulingConstraints", "BusinessHours",
]