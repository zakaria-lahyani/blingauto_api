from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json

from app.features.vehicles.domain import Vehicle
from app.features.vehicles.ports import (
    ICacheService,
    IEventService,
    INotificationService,
    IVehicleDataService,
    IAuditService,
)


class RedisCacheService(ICacheService):
    """Redis-based cache service implementation for vehicles."""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    async def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        """Get cached vehicle."""
        try:
            data = await self._redis.get(f"vehicle:{vehicle_id}")
            if data:
                # Deserialize vehicle data back to domain entity
                # This would require custom serialization logic
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_vehicle(self, vehicle: Vehicle, ttl: int = 3600) -> bool:
        """Cache vehicle data."""
        try:
            # Serialize vehicle to JSON
            data = json.dumps({
                "id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year,
                "color": vehicle.color,
                "license_plate": vehicle.license_plate,
                "is_default": vehicle.is_default,
                "is_deleted": vehicle.is_deleted,
                "created_at": vehicle.created_at.isoformat(),
                "updated_at": vehicle.updated_at.isoformat(),
            })
            
            await self._redis.setex(f"vehicle:{vehicle.id}", ttl, data)
            return True
        except Exception:
            return False
    
    async def delete_vehicle(self, vehicle_id: str) -> bool:
        """Remove vehicle from cache."""
        try:
            await self._redis.delete(f"vehicle:{vehicle_id}")
            return True
        except Exception:
            return False
    
    async def get_customer_vehicles(
        self,
        customer_id: str,
        include_deleted: bool = False,
    ) -> Optional[List[Vehicle]]:
        """Get cached customer vehicles."""
        try:
            key = f"customer_vehicles:{customer_id}:{'all' if include_deleted else 'active'}"
            data = await self._redis.get(key)
            if data:
                # Deserialize list of vehicles
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_customer_vehicles(
        self,
        customer_id: str,
        vehicles: List[Vehicle],
        include_deleted: bool = False,
        ttl: int = 1800,
    ) -> bool:
        """Cache customer vehicles."""
        try:
            key = f"customer_vehicles:{customer_id}:{'all' if include_deleted else 'active'}"
            # Serialize list of vehicles
            data = json.dumps([
                {
                    "id": v.id,
                    "make": v.make,
                    "model": v.model,
                    "year": v.year,
                    "color": v.color,
                    "license_plate": v.license_plate,
                    "is_default": v.is_default,
                    "is_deleted": v.is_deleted,
                    "display_name": v.display_name,
                }
                for v in vehicles
            ])
            await self._redis.setex(key, ttl, data)
            return True
        except Exception:
            return False
    
    async def invalidate_customer_cache(self, customer_id: str) -> bool:
        """Invalidate all cached data for customer."""
        try:
            pattern = f"customer_vehicles:{customer_id}:*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            return True
        except Exception:
            return False


class EventBusService(IEventService):
    """Event bus service implementation for vehicles."""
    
    def __init__(self, event_bus):
        self._event_bus = event_bus
    
    async def publish_vehicle_created(self, vehicle: Vehicle) -> bool:
        """Publish vehicle created event."""
        try:
            event_data = {
                "event_type": "vehicle_created",
                "vehicle_id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year,
                "is_default": vehicle.is_default,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("vehicle.created", event_data)
            return True
        except Exception:
            return False
    
    async def publish_vehicle_updated(
        self,
        vehicle: Vehicle,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish vehicle updated event."""
        try:
            event_data = {
                "event_type": "vehicle_updated",
                "vehicle_id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "changes": changes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("vehicle.updated", event_data)
            return True
        except Exception:
            return False
    
    async def publish_vehicle_deleted(self, vehicle: Vehicle) -> bool:
        """Publish vehicle deleted event."""
        try:
            event_data = {
                "event_type": "vehicle_deleted",
                "vehicle_id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("vehicle.deleted", event_data)
            return True
        except Exception:
            return False
    
    async def publish_default_vehicle_changed(
        self,
        customer_id: str,
        old_vehicle: Optional[Vehicle],
        new_vehicle: Vehicle,
    ) -> bool:
        """Publish default vehicle changed event."""
        try:
            event_data = {
                "event_type": "default_vehicle_changed",
                "customer_id": customer_id,
                "old_vehicle_id": old_vehicle.id if old_vehicle else None,
                "new_vehicle_id": new_vehicle.id,
                "old_vehicle_name": old_vehicle.display_name if old_vehicle else None,
                "new_vehicle_name": new_vehicle.display_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("vehicle.default_changed", event_data)
            return True
        except Exception:
            return False


class EmailNotificationService(INotificationService):
    """Email-based notification service implementation for vehicles."""
    
    def __init__(self, email_service):
        self._email_service = email_service
    
    async def send_vehicle_added_notification(
        self,
        customer_email: str,
        vehicle: Vehicle,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send vehicle added notification."""
        try:
            subject = f"Vehicle Added - {vehicle.display_name}"
            
            body = f"""
            Dear {customer_data['first_name']},
            
            Your vehicle has been successfully added to your account!
            
            Vehicle Details:
            - Vehicle: {vehicle.display_name}
            - Color: {vehicle.color}
            - License Plate: {vehicle.license_plate}
            - Default Vehicle: {'Yes' if vehicle.is_default else 'No'}
            
            You can now use this vehicle for bookings.
            
            Thank you for choosing our service!
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False
    
    async def send_default_vehicle_changed_notification(
        self,
        customer_email: str,
        old_vehicle: Optional[Vehicle],
        new_vehicle: Vehicle,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send default vehicle changed notification."""
        try:
            subject = "Default Vehicle Changed"
            
            old_name = old_vehicle.display_name if old_vehicle else "None"
            
            body = f"""
            Dear {customer_data['first_name']},
            
            Your default vehicle has been changed.
            
            Previous Default: {old_name}
            New Default: {new_vehicle.display_name}
            
            This vehicle will now be pre-selected for new bookings.
            
            Thank you.
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False
    
    async def send_vehicle_deleted_notification(
        self,
        customer_email: str,
        vehicle: Vehicle,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send vehicle deleted notification."""
        try:
            subject = f"Vehicle Removed - {vehicle.display_name}"
            
            body = f"""
            Dear {customer_data['first_name']},
            
            Your vehicle {vehicle.display_name} has been removed from your account.
            
            If you have any questions, please contact us.
            
            Thank you.
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False


class VehicleDataService(IVehicleDataService):
    """External vehicle data service implementation."""
    
    def __init__(self, external_api_client=None):
        self._api_client = external_api_client
    
    async def get_vehicle_info_by_vin(self, vin: str) -> Optional[Dict[str, Any]]:
        """Get vehicle information by VIN."""
        try:
            # Would call external VIN decoder API
            return {
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "trim": "LE",
                "engine": "2.5L 4-Cylinder",
            }
        except Exception:
            return None
    
    async def get_make_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get vehicle make suggestions based on query."""
        # Static list for demo - would query external API
        all_makes = [
            "Toyota", "Honda", "Ford", "Chevrolet", "Nissan",
            "BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Hyundai",
            "Kia", "Mazda", "Subaru", "Lexus", "Acura"
        ]
        
        query_lower = query.lower()
        suggestions = [make for make in all_makes if query_lower in make.lower()]
        return suggestions[:limit]
    
    async def get_model_suggestions(
        self,
        make: str,
        query: str,
        limit: int = 10,
    ) -> List[str]:
        """Get vehicle model suggestions for a make."""
        # Static mapping for demo - would query external API
        make_models = {
            "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Prius", "Tacoma"],
            "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit", "Ridgeline"],
            "Ford": ["F-150", "Escape", "Explorer", "Mustang", "Focus", "Fusion"],
        }
        
        models = make_models.get(make, [])
        query_lower = query.lower()
        suggestions = [model for model in models if query_lower in model.lower()]
        return suggestions[:limit]
    
    async def validate_make_model_combination(self, make: str, model: str) -> bool:
        """Validate if make/model combination exists."""
        # Would validate against external database
        return True
    
    async def get_typical_colors_for_vehicle(
        self,
        make: str,
        model: str,
        year: int,
    ) -> List[str]:
        """Get typical colors for a specific vehicle."""
        # Common vehicle colors
        return [
            "White", "Black", "Silver", "Gray", "Red",
            "Blue", "Green", "Brown", "Gold", "Orange"
        ]


class AuditService(IAuditService):
    """Audit service implementation for vehicle changes."""
    
    def __init__(self, audit_logger):
        self._logger = audit_logger
    
    async def log_vehicle_creation(
        self,
        vehicle: Vehicle,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log vehicle creation event."""
        try:
            log_entry = {
                "action": "vehicle_created",
                "vehicle_id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "created_by": created_by,
                "vehicle_details": {
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "license_plate": vehicle.license_plate,
                    "is_default": vehicle.is_default,
                },
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_vehicle_update(
        self,
        vehicle: Vehicle,
        updated_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log vehicle update event."""
        try:
            log_entry = {
                "action": "vehicle_updated",
                "vehicle_id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "updated_by": updated_by,
                "changes": changes,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_vehicle_deletion(
        self,
        vehicle: Vehicle,
        deleted_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log vehicle deletion event."""
        try:
            log_entry = {
                "action": "vehicle_deleted",
                "vehicle_id": vehicle.id,
                "customer_id": vehicle.customer_id,
                "deleted_by": deleted_by,
                "reason": reason,
                "vehicle_details": {
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "license_plate": vehicle.license_plate,
                },
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_default_vehicle_change(
        self,
        customer_id: str,
        old_vehicle_id: Optional[str],
        new_vehicle_id: str,
        changed_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log default vehicle change event."""
        try:
            log_entry = {
                "action": "default_vehicle_changed",
                "customer_id": customer_id,
                "old_vehicle_id": old_vehicle_id,
                "new_vehicle_id": new_vehicle_id,
                "changed_by": changed_by,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False