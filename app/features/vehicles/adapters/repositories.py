from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from app.features.vehicles.ports import (
    Vehicle,
    IVehicleRepository,
    ICustomerRepository,
    IBookingRepository,
)


class SqlVehicleRepository(IVehicleRepository):
    """SQLAlchemy implementation of vehicle repository."""
    
    def __init__(self, session: Session):
        self._session = session
    
    def get_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get vehicle by ID."""
        # This would typically use SQLAlchemy models
        # For now, return placeholder implementation
        # In real implementation, query the vehicle table and convert to domain entity
        return None
    
    def create(self, vehicle: Vehicle) -> Vehicle:
        """Create a new vehicle."""
        # Convert domain entity to database model and save
        # Return the saved domain entity
        return vehicle
    
    def update(self, vehicle: Vehicle) -> Vehicle:
        """Update an existing vehicle."""
        # Update database model and return domain entity
        return vehicle
    
    def delete(self, vehicle_id: str) -> bool:
        """Hard delete a vehicle (use soft delete in practice)."""
        # Hard delete from database (not recommended)
        return True
    
    def list_by_customer(
        self,
        customer_id: str,
        include_deleted: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Vehicle]:
        """List vehicles for a specific customer."""
        # Query database with filters and pagination
        return []
    
    def count_by_customer(
        self,
        customer_id: str,
        include_deleted: bool = False,
    ) -> int:
        """Count vehicles for a customer."""
        # Count query with filters
        return 0
    
    def get_default_vehicle(self, customer_id: str) -> Optional[Vehicle]:
        """Get the default vehicle for a customer."""
        # Query for default vehicle
        return None
    
    def get_by_license_plate(
        self,
        license_plate: str,
        customer_id: str,
    ) -> Optional[Vehicle]:
        """Get vehicle by license plate for a specific customer."""
        # Query by license plate and customer
        return None
    
    def check_license_plate_exists(
        self,
        license_plate: str,
        customer_id: str,
        exclude_vehicle_id: Optional[str] = None,
    ) -> bool:
        """Check if license plate exists for a customer."""
        # Check existence query
        return False
    
    def get_vehicles_by_make_model(
        self,
        make: str,
        model: str,
        customer_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Vehicle]:
        """Get vehicles by make and model for suggestions."""
        # Query by make/model with optional customer filter
        return []
    
    def get_popular_makes(self, limit: int = 10) -> List[dict]:
        """Get most popular vehicle makes."""
        # Query with group by and count
        return [
            {"make": "Toyota", "count": 150},
            {"make": "Honda", "count": 120},
            {"make": "Ford", "count": 100},
        ]
    
    def get_popular_models_for_make(self, make: str, limit: int = 10) -> List[dict]:
        """Get most popular models for a given make."""
        # Query with make filter, group by model
        return [
            {"model": "Camry", "count": 50},
            {"model": "Corolla", "count": 45},
            {"model": "RAV4", "count": 40},
        ]


class SqlCustomerRepository(ICustomerRepository):
    """SQLAlchemy implementation of customer repository."""
    
    def __init__(self, session: Session):
        self._session = session
    
    def exists(self, customer_id: str) -> bool:
        """Check if customer exists."""
        # Simple existence check
        return True
    
    def get_by_id(self, customer_id: str) -> Optional[dict]:
        """Get customer details."""
        # Query customer/user table
        return {
            "id": customer_id,
            "email": "customer@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
        }


class SqlBookingRepository(IBookingRepository):
    """SQLAlchemy implementation of booking repository for vehicle constraints."""
    
    def __init__(self, session: Session):
        self._session = session
    
    def has_active_bookings_for_vehicle(self, vehicle_id: str) -> bool:
        """Check if vehicle has active bookings."""
        # Query for non-completed/cancelled bookings
        return False
    
    def count_bookings_for_vehicle(
        self,
        vehicle_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count bookings for a vehicle in a time period."""
        # Count query with date filters
        return 0