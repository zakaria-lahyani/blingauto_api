# Re-export domain entities through ports so adapters don't import domain directly
from ..domain.entities import Vehicle

from .repositories import (
    IVehicleRepository,
    ICustomerRepository,
    IBookingRepository,
)
from .services import (
    ICacheService,
    IEventService,
    INotificationService,
    IVehicleDataService,
    IAuditService,
)

__all__ = [
    # Domain entities (re-exported)
    "Vehicle",
    # Repositories
    "IVehicleRepository",
    "ICustomerRepository",
    "IBookingRepository",
    # Services
    "ICacheService",
    "IEventService",
    "INotificationService",
    "IVehicleDataService",
    "IAuditService",
]