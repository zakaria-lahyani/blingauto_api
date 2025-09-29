"""
Vehicle application service
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from src.features.vehicles.domain.entities import Vehicle
from src.features.vehicles.domain.enums import VehicleStatus
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository


class VehicleApplicationService:
    """Application service for vehicle business operations"""
    
    def __init__(self, vehicle_repository: VehicleRepository):
        self.vehicle_repo = vehicle_repository
    
    async def create_vehicle(
        self,
        user_id: UUID,
        make: str,
        model: str,
        year: int,
        license_plate: str,
        color: str,
        is_default: bool = False
    ) -> Vehicle:
        """Create a new vehicle for a user"""
        try:
            vehicle = Vehicle(
                user_id=user_id,
                make=make,
                model=model,
                year=year,
                license_plate=license_plate,
                color=color,
                is_default=is_default
            )
            
            return await self.vehicle_repo.create(vehicle)
            
        except Exception as e:
            raise ValueError(f"Failed to create vehicle: {str(e)}")
    
    async def get_vehicle(self, vehicle_id: UUID, user_id: Optional[UUID] = None) -> Optional[Vehicle]:
        """Get a vehicle by ID with optional user verification"""
        vehicle = await self.vehicle_repo.get_by_id(vehicle_id)
        
        if vehicle and user_id and vehicle.user_id != user_id:
            return None  # User doesn't own this vehicle
        
        return vehicle
    
    async def get_user_vehicles(
        self,
        user_id: UUID,
        status: Optional[VehicleStatus] = None,
        search: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[Vehicle]:
        """Get all vehicles for a user with optional filtering"""
        return await self.vehicle_repo.list_by_user(
            user_id=user_id,
            status=status,
            search=search,
            include_inactive=include_inactive
        )
    
    async def get_default_vehicle(self, user_id: UUID) -> Optional[Vehicle]:
        """Get the default vehicle for a user"""
        return await self.vehicle_repo.get_default_vehicle(user_id)
    
    async def update_vehicle(
        self,
        vehicle_id: UUID,
        user_id: UUID,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        license_plate: Optional[str] = None,
        color: Optional[str] = None
    ) -> Optional[Vehicle]:
        """Update a vehicle's details"""
        vehicle = await self.get_vehicle(vehicle_id, user_id)
        if not vehicle:
            raise ValueError("Vehicle not found or access denied")
        
        if vehicle.status != VehicleStatus.ACTIVE:
            raise ValueError("Cannot update inactive or deleted vehicle")
        
        try:
            vehicle.update_details(
                make=make,
                model=model,
                year=year,
                license_plate=license_plate,
                color=color
            )
            
            return await self.vehicle_repo.update(vehicle)
            
        except Exception as e:
            raise ValueError(f"Failed to update vehicle: {str(e)}")
    
    async def set_default_vehicle(self, vehicle_id: UUID, user_id: UUID) -> bool:
        """Set a vehicle as the default for a user"""
        vehicle = await self.get_vehicle(vehicle_id, user_id)
        if not vehicle:
            raise ValueError("Vehicle not found or access denied")
        
        if vehicle.status != VehicleStatus.ACTIVE:
            raise ValueError("Cannot set inactive vehicle as default")
        
        return await self.vehicle_repo.set_default_vehicle(vehicle_id, user_id)
    
    async def deactivate_vehicle(self, vehicle_id: UUID, user_id: UUID) -> bool:
        """Deactivate a vehicle (soft delete)"""
        vehicle = await self.get_vehicle(vehicle_id, user_id)
        if not vehicle:
            raise ValueError("Vehicle not found or access denied")
        
        if vehicle.status == VehicleStatus.DELETED:
            raise ValueError("Vehicle is already deleted")
        
        # Check if this is the only active vehicle
        active_count = await self.vehicle_repo.get_vehicle_count_by_user(user_id)
        if active_count <= 1:
            raise ValueError("Cannot deactivate the only active vehicle. Add another vehicle first.")
        
        vehicle.deactivate()
        updated_vehicle = await self.vehicle_repo.update(vehicle)
        return updated_vehicle is not None
    
    async def activate_vehicle(self, vehicle_id: UUID, user_id: UUID) -> bool:
        """Activate a vehicle"""
        vehicle = await self.get_vehicle(vehicle_id, user_id)
        if not vehicle:
            raise ValueError("Vehicle not found or access denied")
        
        if vehicle.status == VehicleStatus.DELETED:
            raise ValueError("Cannot activate deleted vehicle")
        
        if vehicle.status == VehicleStatus.ACTIVE:
            return True  # Already active
        
        vehicle.activate()
        updated_vehicle = await self.vehicle_repo.update(vehicle)
        return updated_vehicle is not None
    
    async def delete_vehicle(self, vehicle_id: UUID, user_id: UUID) -> bool:
        """Delete a vehicle (soft delete)"""
        vehicle = await self.get_vehicle(vehicle_id, user_id)
        if not vehicle:
            raise ValueError("Vehicle not found or access denied")
        
        if vehicle.status == VehicleStatus.DELETED:
            return True  # Already deleted
        
        # Check if this is the only active vehicle
        if vehicle.status == VehicleStatus.ACTIVE:
            active_count = await self.vehicle_repo.get_vehicle_count_by_user(user_id)
            if active_count <= 1:
                raise ValueError("Cannot delete the only active vehicle. Add another vehicle first.")
        
        return await self.vehicle_repo.delete(vehicle_id)
    
    async def search_vehicles(
        self,
        user_id: UUID,
        search_term: str
    ) -> List[Vehicle]:
        """Search vehicles by various criteria"""
        return await self.vehicle_repo.list_by_user(
            user_id=user_id,
            search=search_term,
            include_inactive=False
        )
    
    async def get_vehicle_analytics(self, user_id: UUID) -> Dict[str, Any]:
        """Get vehicle analytics for a user"""
        all_vehicles = await self.vehicle_repo.list_by_user(
            user_id=user_id,
            include_inactive=True
        )
        
        active_vehicles = [v for v in all_vehicles if v.status == VehicleStatus.ACTIVE]
        inactive_vehicles = [v for v in all_vehicles if v.status == VehicleStatus.INACTIVE]
        deleted_vehicles = [v for v in all_vehicles if v.status == VehicleStatus.DELETED]
        
        return {
            "total_vehicles": len(all_vehicles),
            "active_vehicles": len(active_vehicles),
            "inactive_vehicles": len(inactive_vehicles),
            "deleted_vehicles": len(deleted_vehicles),
            "default_vehicle_id": next((v.id for v in active_vehicles if v.is_default), None),
            "newest_vehicle_year": max((v.year for v in active_vehicles), default=None),
            "oldest_vehicle_year": min((v.year for v in active_vehicles), default=None)
        }