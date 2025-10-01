from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.features.vehicles.domain import Vehicle


class ICacheService(ABC):
    """Cache service interface for vehicle performance."""
    
    @abstractmethod
    async def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get cached vehicle."""
        pass
    
    @abstractmethod
    async def set_vehicle(self, vehicle: Vehicle, ttl: int = 3600) -> bool:
        """Cache vehicle data."""
        pass
    
    @abstractmethod
    async def delete_vehicle(self, vehicle_id: str) -> bool:
        """Remove vehicle from cache."""
        pass
    
    @abstractmethod
    async def get_customer_vehicles(
        self,
        customer_id: str,
        include_deleted: bool = False,
    ) -> Optional[List[Vehicle]]:
        """Get cached customer vehicles."""
        pass
    
    @abstractmethod
    async def set_customer_vehicles(
        self,
        customer_id: str,
        vehicles: List[Vehicle],
        include_deleted: bool = False,
        ttl: int = 1800,
    ) -> bool:
        """Cache customer vehicles."""
        pass
    
    @abstractmethod
    async def invalidate_customer_cache(self, customer_id: str) -> bool:
        """Invalidate all cached data for customer."""
        pass


class IEventService(ABC):
    """Event service interface for vehicle domain events."""
    
    @abstractmethod
    async def publish_vehicle_created(self, vehicle: Vehicle) -> bool:
        """Publish vehicle created event."""
        pass
    
    @abstractmethod
    async def publish_vehicle_updated(
        self,
        vehicle: Vehicle,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish vehicle updated event."""
        pass
    
    @abstractmethod
    async def publish_vehicle_deleted(self, vehicle: Vehicle) -> bool:
        """Publish vehicle deleted event."""
        pass
    
    @abstractmethod
    async def publish_default_vehicle_changed(
        self,
        customer_id: str,
        old_vehicle: Optional[Vehicle],
        new_vehicle: Vehicle,
    ) -> bool:
        """Publish default vehicle changed event."""
        pass


class INotificationService(ABC):
    """Notification service interface for vehicle events."""
    
    @abstractmethod
    async def send_vehicle_added_notification(
        self,
        customer_email: str,
        vehicle: Vehicle,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send vehicle added notification."""
        pass
    
    @abstractmethod
    async def send_default_vehicle_changed_notification(
        self,
        customer_email: str,
        old_vehicle: Optional[Vehicle],
        new_vehicle: Vehicle,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send default vehicle changed notification."""
        pass
    
    @abstractmethod
    async def send_vehicle_deleted_notification(
        self,
        customer_email: str,
        vehicle: Vehicle,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send vehicle deleted notification."""
        pass


class IVehicleDataService(ABC):
    """External vehicle data service interface."""
    
    @abstractmethod
    async def get_vehicle_info_by_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by VIN."""
        pass
    
    @abstractmethod
    async def get_make_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get vehicle make suggestions based on query."""
        pass
    
    @abstractmethod
    async def get_model_suggestions(
        self,
        make: str,
        query: str,
        limit: int = 10,
    ) -> List[str]:
        """Get vehicle model suggestions for a make."""
        pass
    
    @abstractmethod
    async def validate_make_model_combination(self, make: str, model: str) -> bool:
        """Validate if make/model combination exists."""
        pass
    
    @abstractmethod
    async def get_typical_colors_for_vehicle(
        self,
        make: str,
        model: str,
        year: int,
    ) -> List[str]:
        """Get typical colors for a specific vehicle."""
        pass


class IAuditService(ABC):
    """Audit service interface for vehicle changes."""
    
    @abstractmethod
    async def log_vehicle_creation(
        self,
        vehicle: Vehicle,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log vehicle creation event."""
        pass
    
    @abstractmethod
    async def log_vehicle_update(
        self,
        vehicle: Vehicle,
        updated_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log vehicle update event."""
        pass
    
    @abstractmethod
    async def log_vehicle_deletion(
        self,
        vehicle: Vehicle,
        deleted_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log vehicle deletion event."""
        pass
    
    @abstractmethod
    async def log_default_vehicle_change(
        self,
        customer_id: str,
        old_vehicle_id: Optional[str],
        new_vehicle_id: str,
        changed_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log default vehicle change event."""
        pass