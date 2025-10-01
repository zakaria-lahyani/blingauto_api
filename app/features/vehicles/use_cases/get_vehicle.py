from dataclasses import dataclass
from typing import Optional

from app.core.errors import NotFoundError, BusinessRuleViolationError
from app.features.vehicles.domain import Vehicle
from app.features.vehicles.ports import (
    IVehicleRepository,
    ICacheService,
)


@dataclass
class GetVehicleRequest:
    vehicle_id: str
    requested_by: str
    is_admin: bool = False


@dataclass
class GetVehicleResponse:
    id: str
    customer_id: str
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    is_default: bool
    is_deleted: bool
    display_name: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None


class GetVehicleUseCase:
    """Use case for retrieving a specific vehicle."""
    
    def __init__(
        self,
        vehicle_repository: IVehicleRepository,
        cache_service: ICacheService,
    ):
        self._vehicle_repository = vehicle_repository
        self._cache_service = cache_service
    
    def execute(self, request: GetVehicleRequest) -> GetVehicleResponse:
        """Execute the get vehicle use case."""
        
        # Step 1: Try to get from cache first
        vehicle = self._cache_service.get_vehicle(request.vehicle_id)
        
        if not vehicle:
            # Step 2: Get from repository if not cached
            vehicle = self._vehicle_repository.get_by_id(request.vehicle_id)
            if not vehicle:
                raise NotFoundError(f"Vehicle {request.vehicle_id} not found")
            
            # Cache the vehicle for future requests
            self._cache_service.set_vehicle(vehicle, ttl=3600)
        
        # Step 3: Validate access permissions
        if not request.is_admin and vehicle.customer_id != request.requested_by:
            raise BusinessRuleViolationError(
                "You can only view your own vehicles"
            )
        
        # Step 4: Build response
        response = GetVehicleResponse(
            id=vehicle.id,
            customer_id=vehicle.customer_id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            license_plate=vehicle.license_plate,
            is_default=vehicle.is_default,
            is_deleted=vehicle.is_deleted,
            display_name=vehicle.display_name,
            created_at=vehicle.created_at.isoformat(),
            updated_at=vehicle.updated_at.isoformat(),
        )
        
        # Add deletion timestamp if vehicle is deleted
        if vehicle.deleted_at:
            response.deleted_at = vehicle.deleted_at.isoformat()
        
        return response