from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.core.errors import ValidationError, BusinessRuleViolationError, NotFoundError
from app.features.vehicles.domain import Vehicle, VehicleValidationPolicy, VehicleBusinessPolicy
from app.features.vehicles.ports import (
    IVehicleRepository,
    ICustomerRepository,
    ICacheService,
    IEventService,
    INotificationService,
    IAuditService,
)


@dataclass
class UpdateVehicleRequest:
    vehicle_id: str
    updated_by: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    license_plate: Optional[str] = None


@dataclass
class UpdateVehicleResponse:
    vehicle_id: str
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    is_default: bool
    display_name: str
    changes_made: list[str]


class UpdateVehicleUseCase:
    """Use case for updating an existing vehicle."""
    
    def __init__(
        self,
        vehicle_repository: IVehicleRepository,
        customer_repository: ICustomerRepository,
        cache_service: ICacheService,
        event_service: IEventService,
        notification_service: INotificationService,
        audit_service: IAuditService,
    ):
        self._vehicle_repository = vehicle_repository
        self._customer_repository = customer_repository
        self._cache_service = cache_service
        self._event_service = event_service
        self._notification_service = notification_service
        self._audit_service = audit_service
    
    def execute(self, request: UpdateVehicleRequest) -> UpdateVehicleResponse:
        """Execute the update vehicle use case."""
        
        # Step 1: Get existing vehicle
        vehicle = self._vehicle_repository.get_by_id(request.vehicle_id)
        if not vehicle:
            raise NotFoundError(f"Vehicle {request.vehicle_id} not found")
        
        # Step 2: Validate vehicle can be updated
        VehicleValidationPolicy.validate_vehicle_update(vehicle)
        
        # Step 3: Track changes
        changes_made = []
        old_values = {}
        
        # Check what fields are being updated
        if request.make is not None and request.make != vehicle.make:
            old_values["make"] = vehicle.make
            changes_made.append("make")
        
        if request.model is not None and request.model != vehicle.model:
            old_values["model"] = vehicle.model
            changes_made.append("model")
        
        if request.year is not None and request.year != vehicle.year:
            old_values["year"] = vehicle.year
            changes_made.append("year")
        
        if request.color is not None and request.color != vehicle.color:
            old_values["color"] = vehicle.color
            changes_made.append("color")
        
        if request.license_plate is not None and request.license_plate != vehicle.license_plate:
            old_values["license_plate"] = vehicle.license_plate
            changes_made.append("license_plate")
        
        # Step 4: Validate license plate uniqueness if being changed
        if request.license_plate is not None and request.license_plate != vehicle.license_plate:
            existing_vehicles = self._vehicle_repository.list_by_customer(
                vehicle.customer_id, include_deleted=False
            )
            
            VehicleBusinessPolicy.validate_license_plate_uniqueness(
                request.license_plate,
                vehicle.customer_id,
                vehicle.id,
                existing_vehicles,
            )
        
        # Step 5: Update vehicle entity if there are changes
        if changes_made:
            vehicle.update_details(
                make=request.make,
                model=request.model,
                year=request.year,
                color=request.color,
                license_plate=request.license_plate,
            )
            
            # Step 6: Save updated vehicle
            updated_vehicle = self._vehicle_repository.update(vehicle)
            
            # Step 7: Clear caches
            self._cache_service.delete_vehicle(vehicle.id)
            self._cache_service.invalidate_customer_cache(vehicle.customer_id)
            
            # Step 8: Publish domain event
            changes_dict = {
                "changed_fields": changes_made,
                "old_values": old_values,
                "new_values": {
                    field: getattr(updated_vehicle, field) for field in changes_made
                }
            }
            self._event_service.publish_vehicle_updated(updated_vehicle, changes_dict)
            
            # Step 9: Log audit event
            self._audit_service.log_vehicle_update(
                updated_vehicle,
                request.updated_by,
                changes_dict,
            )
        else:
            updated_vehicle = vehicle
            changes_made = ["no_changes"]
        
        # Step 10: Prepare response
        return UpdateVehicleResponse(
            vehicle_id=updated_vehicle.id,
            make=updated_vehicle.make,
            model=updated_vehicle.model,
            year=updated_vehicle.year,
            color=updated_vehicle.color,
            license_plate=updated_vehicle.license_plate,
            is_default=updated_vehicle.is_default,
            display_name=updated_vehicle.display_name,
            changes_made=changes_made,
        )