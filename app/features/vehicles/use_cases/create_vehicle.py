from dataclasses import dataclass
from typing import Optional

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
class CreateVehicleRequest:
    customer_id: str
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    is_default: bool = False
    created_by: str = ""


@dataclass
class CreateVehicleResponse:
    vehicle_id: str
    make: str
    model: str
    year: int
    color: str
    license_plate: str
    is_default: bool
    display_name: str


class CreateVehicleUseCase:
    """Use case for creating a new vehicle."""
    
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
    
    def execute(self, request: CreateVehicleRequest) -> CreateVehicleResponse:
        """Execute the create vehicle use case."""
        
        # Step 1: Validate customer exists
        customer_exists = self._customer_repository.exists(request.customer_id)
        if not customer_exists:
            raise NotFoundError(f"Customer {request.customer_id} not found")
        
        # Step 2: Validate license plate uniqueness
        existing_vehicles = self._vehicle_repository.list_by_customer(
            request.customer_id, include_deleted=False
        )
        
        VehicleBusinessPolicy.validate_license_plate_uniqueness(
            request.license_plate,
            request.customer_id,
            "",  # No vehicle ID for new vehicle
            existing_vehicles,
        )
        
        # Step 3: Create vehicle entity
        vehicle = Vehicle.create(
            customer_id=request.customer_id,
            make=request.make,
            model=request.model,
            year=request.year,
            color=request.color,
            license_plate=request.license_plate,
            is_default=request.is_default,
        )
        
        # Step 4: Handle default vehicle logic (RG-VEH-006)
        if request.is_default:
            # Validate default vehicle rules
            VehicleBusinessPolicy.validate_default_vehicle_rules(
                existing_vehicles, vehicle, "set_default"
            )
            
            # Unset current default vehicle
            current_default = self._vehicle_repository.get_default_vehicle(request.customer_id)
            if current_default and current_default.id != vehicle.id:
                current_default.unset_as_default()
                self._vehicle_repository.update(current_default)
        else:
            # Auto-set as default if it's the first vehicle
            if not existing_vehicles:
                vehicle.set_as_default()
        
        # Step 5: Save vehicle to repository
        saved_vehicle = self._vehicle_repository.create(vehicle)
        
        # Step 6: Clear customer cache
        self._cache_service.invalidate_customer_cache(request.customer_id)
        
        # Step 7: Publish domain event
        self._event_service.publish_vehicle_created(saved_vehicle)
        
        # Step 8: Log audit event
        self._audit_service.log_vehicle_creation(
            saved_vehicle,
            request.created_by or request.customer_id,
            {"is_first_vehicle": not existing_vehicles}
        )
        
        # Step 9: Send notification (async, don't block)
        customer_data = self._customer_repository.get_by_id(request.customer_id)
        if customer_data:
            self._notification_service.send_vehicle_added_notification(
                customer_data["email"],
                saved_vehicle,
                customer_data,
            )
        
        # Step 10: Prepare response
        return CreateVehicleResponse(
            vehicle_id=saved_vehicle.id,
            make=saved_vehicle.make,
            model=saved_vehicle.model,
            year=saved_vehicle.year,
            color=saved_vehicle.color,
            license_plate=saved_vehicle.license_plate,
            is_default=saved_vehicle.is_default,
            display_name=saved_vehicle.display_name,
        )