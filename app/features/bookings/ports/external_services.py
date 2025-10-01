"""Consumer-owned ports for external service calls (cross-feature communication)."""

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal


class IExternalServiceValidator(ABC):
    """Consumer-owned port for validating services from the services feature.
    
    This port is owned by the bookings feature but implemented by an adapter
    that calls the services feature's public use cases.
    """
    
    @abstractmethod
    def validate_customer_exists(self, customer_id: str) -> bool:
        """Validate that a customer exists."""
        pass
    
    @abstractmethod
    def get_services_data(self, service_ids: List[str]) -> List[dict]:
        """Get service data for multiple services."""
        pass
    
    @abstractmethod
    def get_customer_data(self, customer_id: str) -> Optional[dict]:
        """Get customer data."""
        pass
    
    @abstractmethod
    async def validate_service_exists(self, service_id: str) -> bool:
        """Validate that a service exists and is active."""
        pass
    
    @abstractmethod
    async def get_service_details(self, service_id: str) -> Optional['ServiceDetails']:
        """Get service details needed for booking."""
        pass
    
    @abstractmethod
    async def get_services_details(self, service_ids: List[str]) -> List['ServiceDetails']:
        """Get details for multiple services."""
        pass


class ServiceDetails:
    """DTO for service information needed by bookings feature.
    
    This is owned by the bookings feature, not the services feature.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        price: Decimal,
        duration_minutes: int,
        is_active: bool,
        category_name: str,
    ):
        self.id = id
        self.name = name
        self.price = price
        self.duration_minutes = duration_minutes
        self.is_active = is_active
        self.category_name = category_name


class IExternalVehicleValidator(ABC):
    """Consumer-owned port for validating vehicles from the vehicles feature."""
    
    @abstractmethod
    def validate_customer_vehicle(self, customer_id: str, vehicle_id: str) -> bool:
        """Validate that a vehicle belongs to the specified customer."""
        pass
    
    @abstractmethod
    def get_vehicle_data(self, vehicle_id: str) -> Optional[dict]:
        """Get vehicle data."""
        pass
    
    @abstractmethod
    async def validate_vehicle_belongs_to_customer(
        self, 
        vehicle_id: str, 
        customer_id: str
    ) -> bool:
        """Validate that a vehicle belongs to the specified customer."""
        pass
    
    @abstractmethod
    async def get_vehicle_details(self, vehicle_id: str) -> Optional['VehicleDetails']:
        """Get vehicle details needed for booking."""
        pass


class VehicleDetails:
    """DTO for vehicle information needed by bookings feature."""
    
    def __init__(
        self,
        id: str,
        make: str,
        model: str,
        year: int,
        color: str,
        license_plate: str,
        customer_id: str,
        is_active: bool,
    ):
        self.id = id
        self.make = make
        self.model = model
        self.year = year
        self.color = color
        self.license_plate = license_plate
        self.customer_id = customer_id
        self.is_active = is_active