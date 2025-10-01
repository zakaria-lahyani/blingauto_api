"""Adapters for cross-feature communication via consumer-owned ports."""

from typing import List, Optional

from app.features.bookings.ports.external_services import (
    IExternalServiceValidator,
    IExternalVehicleValidator,
    ServiceDetails,
    VehicleDetails,
)

# Import public use cases from other features (this is the ONLY allowed cross-feature import)
from app.features.services.use_cases.get_service import GetServiceUseCase
from app.features.services.use_cases.list_services import ListServicesUseCase
from app.features.vehicles.use_cases.get_vehicle import GetVehicleUseCase


class ExternalServiceValidatorAdapter(IExternalServiceValidator):
    """Adapter that calls services feature's public use cases.
    
    This is the ONLY place where cross-feature calls are allowed.
    It implements the consumer-owned port by calling public use cases.
    """
    
    def __init__(
        self,
        get_service_use_case: GetServiceUseCase,
        list_services_use_case: ListServicesUseCase,
    ):
        self._get_service = get_service_use_case
        self._list_services = list_services_use_case
    
    async def validate_service_exists(self, service_id: str) -> bool:
        """Validate service exists by calling services feature."""
        try:
            service = await self._get_service.execute(service_id)
            return service is not None and service.is_active
        except Exception:
            return False
    
    async def get_service_details(self, service_id: str) -> Optional[ServiceDetails]:
        """Get service details by calling services feature."""
        try:
            service = await self._get_service.execute(service_id)
            if not service or not service.is_active:
                return None
            
            # Convert domain entity to booking feature's DTO
            return ServiceDetails(
                id=service.id,
                name=service.name,
                price=service.price,
                duration_minutes=service.duration_minutes,
                is_active=service.is_active,
                category_name="",  # Would need category lookup if needed
            )
        except Exception:
            return None
    
    async def get_services_details(self, service_ids: List[str]) -> List[ServiceDetails]:
        """Get multiple service details."""
        details = []
        for service_id in service_ids:
            detail = await self.get_service_details(service_id)
            if detail:
                details.append(detail)
        return details


class ExternalVehicleValidatorAdapter(IExternalVehicleValidator):
    """Adapter that calls vehicles feature's public use cases."""
    
    def __init__(
        self,
        get_vehicle_use_case: GetVehicleUseCase,
    ):
        self._get_vehicle = get_vehicle_use_case
    
    async def validate_vehicle_belongs_to_customer(
        self, 
        vehicle_id: str, 
        customer_id: str
    ) -> bool:
        """Validate vehicle ownership by calling vehicles feature."""
        try:
            vehicle = await self._get_vehicle.execute(vehicle_id, customer_id)
            return vehicle is not None and vehicle.is_active
        except Exception:
            return False
    
    async def get_vehicle_details(self, vehicle_id: str) -> Optional[VehicleDetails]:
        """Get vehicle details by calling vehicles feature."""
        try:
            # Note: This would need customer_id too in real implementation
            vehicle = await self._get_vehicle.execute(vehicle_id, "")
            if not vehicle or not vehicle.is_active:
                return None
            
            # Convert domain entity to booking feature's DTO
            return VehicleDetails(
                id=vehicle.id,
                make=vehicle.make,
                model=vehicle.model,
                year=vehicle.year,
                color=vehicle.color,
                license_plate=vehicle.license_plate,
                customer_id=vehicle.customer_id,
                is_active=vehicle.is_active,
            )
        except Exception:
            return None