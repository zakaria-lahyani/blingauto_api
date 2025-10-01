from dataclasses import dataclass

from app.core.errors import BusinessRuleViolationError, NotFoundError
from app.features.vehicles.domain import Vehicle, VehicleBusinessPolicy
from app.features.vehicles.ports import (
    IVehicleRepository,
    IBookingRepository,
    ICustomerRepository,
    ICacheService,
    IEventService,
    INotificationService,
    IAuditService,
)


@dataclass
class DeleteVehicleRequest:
    vehicle_id: str
    deleted_by: str
    reason: str = "deleted_by_customer"


@dataclass
class DeleteVehicleResponse:
    vehicle_id: str
    deleted: bool
    message: str


class DeleteVehicleUseCase:
    """Use case for deleting a vehicle (soft delete)."""
    
    def __init__(
        self,
        vehicle_repository: IVehicleRepository,
        booking_repository: IBookingRepository,
        customer_repository: ICustomerRepository,
        cache_service: ICacheService,
        event_service: IEventService,
        notification_service: INotificationService,
        audit_service: IAuditService,
    ):
        self._vehicle_repository = vehicle_repository
        self._booking_repository = booking_repository
        self._customer_repository = customer_repository
        self._cache_service = cache_service
        self._event_service = event_service
        self._notification_service = notification_service
        self._audit_service = audit_service
    
    def execute(self, request: DeleteVehicleRequest) -> DeleteVehicleResponse:
        """Execute the delete vehicle use case."""
        
        # Step 1: Get existing vehicle
        vehicle = self._vehicle_repository.get_by_id(request.vehicle_id)
        if not vehicle:
            raise NotFoundError(f"Vehicle {request.vehicle_id} not found")
        
        # Step 2: Check if vehicle has active bookings (RG-VEH-007)
        has_active_bookings = self._booking_repository.has_active_bookings_for_vehicle(
            request.vehicle_id
        )
        
        VehicleBusinessPolicy.validate_deletion_constraints(
            vehicle, has_active_bookings
        )
        
        # Step 3: Get all customer vehicles to validate default vehicle rules
        customer_vehicles = self._vehicle_repository.list_by_customer(
            vehicle.customer_id, include_deleted=False
        )
        
        VehicleBusinessPolicy.validate_default_vehicle_rules(
            customer_vehicles, vehicle, "delete"
        )
        
        # Step 4: Soft delete the vehicle
        vehicle.soft_delete()
        
        # Step 5: Save updated vehicle
        deleted_vehicle = self._vehicle_repository.update(vehicle)
        
        # Step 6: If this was the default vehicle and there are other vehicles,
        # suggest setting another as default
        remaining_vehicles = [v for v in customer_vehicles if v.id != vehicle.id]
        if vehicle.is_default and remaining_vehicles:
            # Auto-set a new default vehicle
            from app.features.vehicles.domain import VehicleRecommendationPolicy
            suggested_default = VehicleRecommendationPolicy.suggest_default_vehicle(remaining_vehicles)
            suggested_default.set_as_default()
            self._vehicle_repository.update(suggested_default)
            
            # Publish default vehicle change event
            self._event_service.publish_default_vehicle_changed(
                vehicle.customer_id, vehicle, suggested_default
            )
        
        # Step 7: Clear caches
        self._cache_service.delete_vehicle(vehicle.id)
        self._cache_service.invalidate_customer_cache(vehicle.customer_id)
        
        # Step 8: Publish domain event
        self._event_service.publish_vehicle_deleted(deleted_vehicle)
        
        # Step 9: Log audit event
        self._audit_service.log_vehicle_deletion(
            deleted_vehicle,
            request.deleted_by,
            request.reason,
            {
                "had_active_bookings": has_active_bookings,
                "was_default": vehicle.is_default,
                "remaining_vehicles_count": len(remaining_vehicles),
            }
        )
        
        # Step 10: Send notification (async, don't block)
        customer_data = self._customer_repository.get_by_id(vehicle.customer_id)
        if customer_data:
            self._notification_service.send_vehicle_deleted_notification(
                customer_data["email"],
                deleted_vehicle,
                customer_data,
            )
        
        # Step 11: Prepare response
        message = f"Vehicle {deleted_vehicle.display_name} has been deleted successfully."
        if vehicle.is_default and remaining_vehicles:
            new_default = next((v for v in remaining_vehicles if v.is_default), None)
            if new_default:
                message += f" {new_default.display_name} is now your default vehicle."
        
        return DeleteVehicleResponse(
            vehicle_id=deleted_vehicle.id,
            deleted=True,
            message=message,
        )