from typing import List
from datetime import datetime

from .exceptions import ValidationError, BusinessRuleViolationError
from .entities import Vehicle


class VehicleValidationPolicy:
    """Policy class for vehicle validation rules."""
    
    @staticmethod
    def validate_vehicle_creation(vehicle: Vehicle) -> None:
        """Validate vehicle creation according to business rules."""
        if not vehicle.customer_id or not vehicle.customer_id.strip():
            raise ValidationError("Vehicle must belong to a customer")
        
        if not vehicle.make or not vehicle.make.strip():
            raise ValidationError("Vehicle make is required")
        
        if not vehicle.model or not vehicle.model.strip():
            raise ValidationError("Vehicle model is required")
        
        if not vehicle.color or not vehicle.color.strip():
            raise ValidationError("Vehicle color is required")
        
        if not vehicle.license_plate or not vehicle.license_plate.strip():
            raise ValidationError("License plate is required")
        
        if vehicle.year <= 0:
            raise ValidationError("Vehicle year must be positive")
    
    @staticmethod
    def validate_vehicle_update(vehicle: Vehicle) -> None:
        """Validate vehicle update according to business rules."""
        if vehicle.is_deleted:
            raise BusinessRuleViolationError("Cannot update deleted vehicle")
        
        VehicleValidationPolicy.validate_vehicle_creation(vehicle)
    
    @staticmethod
    def validate_make_format(make: str) -> str:
        """Validate and normalize vehicle make (RG-VEH-001)."""
        if not make or len(make.strip()) < 2:
            raise ValidationError("Vehicle make must be at least 2 characters")
        if len(make) > 50:
            raise ValidationError("Vehicle make cannot exceed 50 characters")
        
        return make.strip().title()
    
    @staticmethod
    def validate_model_format(model: str) -> str:
        """Validate and normalize vehicle model (RG-VEH-002)."""
        if not model or len(model.strip()) < 1:
            raise ValidationError("Vehicle model cannot be empty")
        if len(model) > 50:
            raise ValidationError("Vehicle model cannot exceed 50 characters")
        
        return model.strip().title()
    
    @staticmethod
    def validate_year_range(year: int) -> None:
        """Validate vehicle year range (RG-VEH-003)."""
        current_year = datetime.now().year
        
        if year < 1900:
            raise ValidationError("Vehicle year cannot be before 1900")
        if year > current_year + 2:
            raise ValidationError(
                f"Vehicle year cannot be more than 2 years in the future (max: {current_year + 2})"
            )
    
    @staticmethod
    def validate_color_format(color: str) -> str:
        """Validate and normalize vehicle color (RG-VEH-004)."""
        if not color or len(color.strip()) < 2:
            raise ValidationError("Vehicle color must be at least 2 characters")
        if len(color) > 30:
            raise ValidationError("Vehicle color cannot exceed 30 characters")
        
        return color.strip().title()
    
    @staticmethod
    def validate_license_plate_format(license_plate: str) -> str:
        """Validate and normalize license plate (RG-VEH-005)."""
        if not license_plate or len(license_plate.strip()) < 2:
            raise ValidationError("License plate must be at least 2 characters")
        if len(license_plate) > 20:
            raise ValidationError("License plate cannot exceed 20 characters")
        
        return license_plate.strip().upper()


class VehicleBusinessPolicy:
    """Policy class for vehicle business rules."""
    
    @staticmethod
    def validate_default_vehicle_rules(
        vehicles: List[Vehicle], 
        target_vehicle: Vehicle,
        operation: str
    ) -> None:
        """Validate default vehicle business rules (RG-VEH-006)."""
        active_vehicles = [v for v in vehicles if not v.is_deleted]
        default_vehicles = [v for v in active_vehicles if v.is_default]
        
        if operation == "set_default":
            # Can only have one default vehicle per customer
            if default_vehicles and not any(v.id == target_vehicle.id for v in default_vehicles):
                # There's already a default vehicle that's not the target
                existing_default = default_vehicles[0]
                raise BusinessRuleViolationError(
                    f"Customer already has a default vehicle: {existing_default.display_name}. "
                    "Please unset the current default before setting a new one."
                )
        
        elif operation == "delete":
            # Cannot delete default vehicle if there are other active vehicles
            if target_vehicle.is_default and len(active_vehicles) > 1:
                other_vehicles = [v for v in active_vehicles if v.id != target_vehicle.id]
                raise BusinessRuleViolationError(
                    f"Cannot delete default vehicle when other vehicles exist. "
                    f"Please set one of the following vehicles as default first: "
                    f"{', '.join(v.display_name for v in other_vehicles[:3])}"
                )
        
        elif operation == "auto_set_default":
            # Auto-set as default if it's the first vehicle
            if not default_vehicles and len(active_vehicles) == 1:
                target_vehicle.set_as_default()
    
    @staticmethod
    def validate_license_plate_uniqueness(
        license_plate: str,
        customer_id: str,
        vehicle_id: str,
        existing_vehicles: List[Vehicle]
    ) -> None:
        """Validate license plate uniqueness per customer (RG-VEH-005)."""
        normalized_plate = license_plate.strip().upper()
        
        # Check for duplicate license plates for the same customer
        for vehicle in existing_vehicles:
            if (vehicle.customer_id == customer_id and 
                vehicle.id != vehicle_id and 
                not vehicle.is_deleted and
                vehicle.license_plate.upper() == normalized_plate):
                raise ValidationError(
                    f"License plate '{normalized_plate}' is already registered for this customer"
                )
    
    @staticmethod
    def validate_deletion_constraints(
        vehicle: Vehicle,
        has_active_bookings: bool = False
    ) -> None:
        """Validate vehicle deletion constraints (RG-VEH-007)."""
        if vehicle.is_deleted:
            raise BusinessRuleViolationError("Vehicle is already deleted")
        
        if has_active_bookings:
            raise BusinessRuleViolationError(
                "Cannot delete vehicle with active bookings. "
                "Please complete or cancel all active bookings first."
            )
        
        # Note: Default vehicle deletion is handled in validate_default_vehicle_rules
    
    @staticmethod
    def calculate_vehicle_usage_stats(vehicles: List[Vehicle]) -> dict:
        """Calculate vehicle usage statistics for business insights."""
        active_vehicles = [v for v in vehicles if not v.is_deleted]
        
        if not active_vehicles:
            return {
                "total_vehicles": 0,
                "active_vehicles": 0,
                "deleted_vehicles": len(vehicles),
                "default_vehicle": None,
                "vehicle_age_distribution": {},
                "make_distribution": {},
                "color_distribution": {},
            }
        
        # Calculate age distribution
        current_year = datetime.now().year
        age_distribution = {}
        for vehicle in active_vehicles:
            age = current_year - vehicle.year
            age_range = self._get_age_range(age)
            age_distribution[age_range] = age_distribution.get(age_range, 0) + 1
        
        # Calculate make distribution
        make_distribution = {}
        for vehicle in active_vehicles:
            make = vehicle.make
            make_distribution[make] = make_distribution.get(make, 0) + 1
        
        # Calculate color distribution
        color_distribution = {}
        for vehicle in active_vehicles:
            color = vehicle.color
            color_distribution[color] = color_distribution.get(color, 0) + 1
        
        # Find default vehicle
        default_vehicle = next((v for v in active_vehicles if v.is_default), None)
        
        return {
            "total_vehicles": len(vehicles),
            "active_vehicles": len(active_vehicles),
            "deleted_vehicles": len(vehicles) - len(active_vehicles),
            "default_vehicle": default_vehicle.display_name if default_vehicle else None,
            "vehicle_age_distribution": age_distribution,
            "make_distribution": make_distribution,
            "color_distribution": color_distribution,
        }
    
    @staticmethod
    def _get_age_range(age: int) -> str:
        """Get age range category for statistics."""
        if age < 0:
            return "Future"
        elif age <= 2:
            return "0-2 years"
        elif age <= 5:
            return "3-5 years"
        elif age <= 10:
            return "6-10 years"
        elif age <= 15:
            return "11-15 years"
        else:
            return "15+ years"


class VehicleRecommendationPolicy:
    """Policy class for vehicle recommendations and suggestions."""
    
    @staticmethod
    def suggest_default_vehicle(vehicles: List[Vehicle]) -> Vehicle:
        """Suggest which vehicle should be default based on business logic."""
        active_vehicles = [v for v in vehicles if not v.is_deleted]
        
        if not active_vehicles:
            raise BusinessRuleViolationError("No active vehicles available")
        
        if len(active_vehicles) == 1:
            return active_vehicles[0]
        
        # Prefer newest vehicle
        newest_vehicle = max(active_vehicles, key=lambda v: v.year)
        
        # If multiple vehicles from same year, prefer the first created
        same_year_vehicles = [v for v in active_vehicles if v.year == newest_vehicle.year]
        if len(same_year_vehicles) > 1:
            return min(same_year_vehicles, key=lambda v: v.created_at)
        
        return newest_vehicle
    
    @staticmethod
    def validate_vehicle_for_service(vehicle: Vehicle, service_requirements: dict) -> bool:
        """Validate if vehicle is suitable for a specific service."""
        if vehicle.is_deleted:
            return False
        
        # Could implement size-based validation here
        # For now, all active vehicles are suitable for all services
        return True