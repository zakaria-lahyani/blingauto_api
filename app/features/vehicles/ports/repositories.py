from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from app.features.vehicles.domain import Vehicle


class IVehicleRepository(ABC):
    """Vehicle repository interface."""
    
    @abstractmethod
    async def get_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get vehicle by ID."""
        pass
    
    @abstractmethod
    async def create(self, vehicle: Vehicle) -> Vehicle:
        """Create a new vehicle."""
        pass
    
    @abstractmethod
    async def update(self, vehicle: Vehicle) -> Vehicle:
        """Update an existing vehicle."""
        pass
    
    @abstractmethod
    async def delete(self, vehicle_id: str) -> bool:
        """Hard delete a vehicle (use soft delete in practice)."""
        pass
    
    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Vehicle]:
        """List vehicles for a specific customer."""
        pass
    
    @abstractmethod
    async def count_by_customer(
        self,
        customer_id: str,
        include_deleted: bool = False,
    ) -> int:
        """Count vehicles for a customer."""
        pass
    
    @abstractmethod
    async def get_default_vehicle(self, customer_id: str) -> Optional[Vehicle]:
        """Get the default vehicle for a customer."""
        pass
    
    @abstractmethod
    async def get_by_license_plate(
        self,
        license_plate: str,
        customer_id: str,
    ) -> Optional[Vehicle]:
        """Get vehicle by license plate for a specific customer."""
        pass
    
    @abstractmethod
    async def check_license_plate_exists(
        self,
        license_plate: str,
        customer_id: str,
        exclude_vehicle_id: Optional[str] = None,
    ) -> bool:
        """Check if license plate exists for a customer."""
        pass
    
    @abstractmethod
    async def get_vehicles_by_make_model(
        self,
        make: str,
        model: str,
        customer_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Vehicle]:
        """Get vehicles by make and model for suggestions."""
        pass
    
    @abstractmethod
    async def get_popular_makes(self, limit: int = 10) -> List[dict]:
        """Get most popular vehicle makes."""
        pass
    
    @abstractmethod
    async def get_popular_models_for_make(self, make: str, limit: int = 10) -> List[dict]:
        """Get most popular models for a given make."""
        pass


class ICustomerRepository(ABC):
    """Customer repository interface for vehicle validation."""
    
    @abstractmethod
    async def exists(self, customer_id: str) -> bool:
        """Check if customer exists."""
        pass
    
    @abstractmethod
    async def get_by_id(self, customer_id: str) -> Optional[dict]:
        """Get customer details."""
        pass


class IBookingRepository(ABC):
    """Booking repository interface for vehicle constraints."""
    
    @abstractmethod
    async def has_active_bookings_for_vehicle(self, vehicle_id: str) -> bool:
        """Check if vehicle has active bookings."""
        pass
    
    @abstractmethod
    async def count_bookings_for_vehicle(
        self,
        vehicle_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count bookings for a vehicle in a time period."""
        pass