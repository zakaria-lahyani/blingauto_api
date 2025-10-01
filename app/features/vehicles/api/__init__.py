from .schemas import (
    CreateVehicleSchema,
    UpdateVehicleSchema,
    VehicleResponseSchema,
    VehicleListResponseSchema,
    SetDefaultVehicleSchema,
)
from .router import router as vehicle_router

__all__ = [
    # Schemas
    "CreateVehicleSchema",
    "UpdateVehicleSchema",
    "VehicleResponseSchema",
    "VehicleListResponseSchema",
    "SetDefaultVehicleSchema",
    # Router
    "vehicle_router",
]