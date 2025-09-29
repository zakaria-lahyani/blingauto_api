"""
Central registry for all database models
Import all models here to ensure relationships are properly established
"""

# Import Base first
from src.shared.database.base import Base

# Import all models in dependency order
# Auth models (no dependencies on other features)
from src.features.auth.infrastructure.database.models import AuthUserModel

# Service models (no dependencies on other features)  
try:
    from src.features.services.infrastructure.database.models import (
        ServiceCategoryModel,
        ServiceModel
    )
except ImportError:
    pass

# Vehicle models (depends on auth)
try:
    from src.features.vehicles.infrastructure.database.models import VehicleModel
except ImportError:
    pass

# Scheduling models (may depend on auth)
try:
    from src.features.scheduling.infrastructure.database.models import (
        BusinessHoursModel,
        TimeSlotModel,
        SchedulingConfigurationModel,
        SchedulingResourceModel,
        ResourceScheduleModel,
        SchedulingConflictModel,
        WashBayModel,
        MobileWashTeamModel,
        WashFacilityConfigurationModel,
        CapacityAllocationModel
    )
except ImportError:
    pass

# Booking models (depends on auth, vehicles, services)
try:
    from src.features.bookings.infrastructure.database.models import (
        BookingModel,
        BookingServiceModel, 
        BookingEventModel
    )
except ImportError:
    pass

# Export all models
__all__ = [
    'Base',
    'AuthUserModel',
    'VehicleModel',
    'BookingModel',
    'ServiceModel',
    'ServiceCategoryModel',
    'BookingServiceModel',
    'BookingEventModel'
]

def get_all_models():
    """Return all registered models"""
    return Base.metadata.tables.keys()