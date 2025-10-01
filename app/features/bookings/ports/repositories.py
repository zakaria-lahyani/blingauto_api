from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.features.bookings.domain import Booking, BookingService


class IBookingRepository(ABC):
    """Booking repository interface."""
    
    @abstractmethod
    async def get_by_id(self, booking_id: str) -> Optional[Booking]:
        """Get booking by ID."""
        pass
    
    @abstractmethod
    async def create(self, booking: Booking) -> Booking:
        """Create a new booking."""
        pass
    
    @abstractmethod
    async def update(self, booking: Booking) -> Booking:
        """Update an existing booking."""
        pass
    
    @abstractmethod
    async def delete(self, booking_id: str) -> bool:
        """Delete a booking."""
        pass
    
    @abstractmethod
    async def list_by_customer(
        self,
        customer_id: str,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Booking]:
        """List bookings for a specific customer."""
        pass
    
    @abstractmethod
    async def list_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Booking]:
        """List bookings within date range."""
        pass
    
    @abstractmethod
    async def list_by_status(
        self,
        status: str,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Booking]:
        """List bookings by status."""
        pass
    
    @abstractmethod
    async def count_by_customer(
        self,
        customer_id: str,
        status: Optional[str] = None,
    ) -> int:
        """Count bookings for a customer."""
        pass
    
    @abstractmethod
    async def find_conflicting_bookings(
        self,
        scheduled_at: datetime,
        duration_minutes: int,
        booking_type: str,
        exclude_booking_id: Optional[str] = None,
    ) -> List[Booking]:
        """Find bookings that might conflict with the given time slot."""
        pass


class IServiceRepository(ABC):
    """Service repository interface for booking services."""
    
    @abstractmethod
    async def get_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service by ID."""
        pass
    
    @abstractmethod
    async def get_multiple_by_ids(self, service_ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple services by their IDs."""
        pass
    
    @abstractmethod
    async def list_active_services(
        self,
        category_id: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List active services."""
        pass


class IVehicleRepository(ABC):
    """Vehicle repository interface for booking validation."""
    
    @abstractmethod
    async def get_by_id(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Get vehicle by ID."""
        pass
    
    @abstractmethod
    async def get_customer_vehicles(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all vehicles for a customer."""
        pass
    
    @abstractmethod
    async def validate_customer_vehicle(self, customer_id: str, vehicle_id: str) -> bool:
        """Validate that vehicle belongs to customer."""
        pass


class ICustomerRepository(ABC):
    """Customer repository interface for booking validation."""
    
    @abstractmethod
    async def get_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        pass
    
    @abstractmethod
    async def exists(self, customer_id: str) -> bool:
        """Check if customer exists."""
        pass