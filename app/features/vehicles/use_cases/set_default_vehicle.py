from dataclasses import dataclass

from app.core.errors import BusinessRuleViolationError, NotFoundError
from app.features.vehicles.domain import Vehicle, VehicleBusinessPolicy
from app.features.vehicles.ports import (
    IVehicleRepository,
    ICustomerRepository,
    ICacheService,
    IEventService,
    INotificationService,
    IAuditService,
)


@dataclass
class SetDefaultVehicleRequest:
    vehicle_id: str
    customer_id: str
    changed_by: str


@dataclass
class SetDefaultVehicleResponse:
    vehicle_id: str
    display_name: str
    is_default: bool
    previous_default_vehicle: str = None


class SetDefaultVehicleUseCase:
    """Use case for setting a vehicle as default."""
    
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
    
    def execute(self, request: SetDefaultVehicleRequest) -> SetDefaultVehicleResponse:
        """Execute the set default vehicle use case."""
        
        # Step 1: Get the vehicle to be set as default
        vehicle = self._vehicle_repository.get_by_id(request.vehicle_id)
        if not vehicle:
            raise NotFoundError(f"Vehicle {request.vehicle_id} not found")
        
        # Step 2: Validate ownership
        if vehicle.customer_id != request.customer_id:
            raise BusinessRuleViolationError("Vehicle does not belong to this customer")
        
        # Step 3: Validate vehicle is not deleted
        if vehicle.is_deleted:
            raise BusinessRuleViolationError("Cannot set deleted vehicle as default")
        
        # Step 4: Check if already default
        if vehicle.is_default:
            return SetDefaultVehicleResponse(
                vehicle_id=vehicle.id,
                display_name=vehicle.display_name,
                is_default=True,
                previous_default_vehicle=None,
            )
        
        # Step 5: Get current default vehicle
        current_default = self._vehicle_repository.get_default_vehicle(request.customer_id)
        
        # Step 6: Get all customer vehicles for validation
        customer_vehicles = self._vehicle_repository.list_by_customer(
            request.customer_id, include_deleted=False
        )
        
        # Step 7: Validate default vehicle business rules
        VehicleBusinessPolicy.validate_default_vehicle_rules(
            customer_vehicles, vehicle, "set_default"
        )
        
        # Step 8: Unset current default vehicle
        if current_default:
            current_default.unset_as_default()
            self._vehicle_repository.update(current_default)
        
        # Step 9: Set new default vehicle
        vehicle.set_as_default()
        updated_vehicle = self._vehicle_repository.update(vehicle)
        
        # Step 10: Clear caches
        self._cache_service.delete_vehicle(vehicle.id)
        if current_default:
            self._cache_service.delete_vehicle(current_default.id)
        self._cache_service.invalidate_customer_cache(request.customer_id)
        
        # Step 11: Publish domain event
        self._event_service.publish_default_vehicle_changed(
            request.customer_id, current_default, updated_vehicle
        )
        
        # Step 12: Log audit event
        self._audit_service.log_default_vehicle_change(
            request.customer_id,
            current_default.id if current_default else None,
            updated_vehicle.id,
            request.changed_by,
            {
                "previous_default": current_default.display_name if current_default else None,
                "new_default": updated_vehicle.display_name,
            }
        )
        
        # Step 13: Send notification (async, don't block)
        customer_data = self._customer_repository.get_by_id(request.customer_id)
        if customer_data:
            self._notification_service.send_default_vehicle_changed_notification(
                customer_data["email"],
                current_default,
                updated_vehicle,
                customer_data,
            )
        
        # Step 14: Prepare response
        return SetDefaultVehicleResponse(
            vehicle_id=updated_vehicle.id,
            display_name=updated_vehicle.display_name,
            is_default=updated_vehicle.is_default,
            previous_default_vehicle=current_default.display_name if current_default else None,
        )