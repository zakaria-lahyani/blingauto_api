"""
Facilities domain entities.
Re-exports entities from scheduling feature for facilities management.

Implements:
- RG-FAC-001: Wash bay configuration
- RG-FAC-002: Vehicle size compatibility
- RG-FAC-003: Mobile team configuration
- RG-FAC-004: Service radius calculations
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from app.core.errors import ValidationError


class VehicleSize(str, Enum):
    """Vehicle size categories for compatibility checks - RG-FAC-002"""
    COMPACT = "compact"
    STANDARD = "standard"
    LARGE = "large"
    OVERSIZED = "oversized"


class ResourceStatus(str, Enum):
    """Resource status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


@dataclass
class Location:
    """GPS location for mobile services"""
    latitude: Decimal
    longitude: Decimal

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate GPS coordinates"""
        if not (-90 <= float(self.latitude) <= 90):
            raise ValidationError("Latitude must be between -90 and 90")

        if not (-180 <= float(self.longitude) <= 180):
            raise ValidationError("Longitude must be between -180 and 180")

    def distance_to(self, other: "Location") -> Decimal:
        """Calculate approximate distance to another location in kilometers"""
        import math

        # Haversine formula for accurate distance calculation
        lat1_rad = math.radians(float(self.latitude))
        lat2_rad = math.radians(float(other.latitude))
        delta_lat = math.radians(float(other.latitude - self.latitude))
        delta_lon = math.radians(float(other.longitude - self.longitude))

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Earth's radius in kilometers
        earth_radius_km = 6371.0
        distance = Decimal(str(earth_radius_km * c))

        return distance


@dataclass
class WashBay:
    """
    Wash bay resource entity.

    Implements:
    - RG-FAC-001: Bay configuration with number, capacity, equipment
    - RG-FAC-002: Vehicle size compatibility hierarchy
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    bay_number: str = ""
    max_vehicle_size: VehicleSize = VehicleSize.STANDARD
    equipment_types: List[str] = field(default_factory=list)
    status: ResourceStatus = ResourceStatus.ACTIVE
    location: Optional[Location] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Business rule constants - RG-FAC-002
    VEHICLE_SIZE_HIERARCHY = {
        VehicleSize.COMPACT: 1,
        VehicleSize.STANDARD: 2,
        VehicleSize.LARGE: 3,
        VehicleSize.OVERSIZED: 4
    }

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate wash bay constraints"""
        if not self.bay_number or not self.bay_number.strip():
            raise ValidationError("Bay number cannot be empty")

    @classmethod
    def create(
        cls,
        bay_number: str,
        max_vehicle_size: VehicleSize,
        equipment_types: List[str] = None,
        location: Optional[Location] = None
    ) -> "WashBay":
        """Factory method to create a new wash bay with validation"""
        return cls(
            bay_number=bay_number,
            max_vehicle_size=max_vehicle_size,
            equipment_types=equipment_types or [],
            location=location
        )

    def can_accommodate_vehicle(self, vehicle_size: VehicleSize) -> bool:
        """
        Check if bay can accommodate vehicle size.

        Implements RG-FAC-002: Hierarchical size compatibility.
        A bay can accommodate its max size and all smaller sizes.
        """
        max_level = self.VEHICLE_SIZE_HIERARCHY[self.max_vehicle_size]
        vehicle_level = self.VEHICLE_SIZE_HIERARCHY[vehicle_size]
        return vehicle_level <= max_level

    def is_available_for_booking(self) -> bool:
        """Check if bay is available for new bookings"""
        return self.status == ResourceStatus.ACTIVE

    def activate(self) -> None:
        """Activate the wash bay - RG-FAC-001"""
        self.status = ResourceStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the wash bay for maintenance - RG-FAC-001"""
        self.status = ResourceStatus.MAINTENANCE
        self.updated_at = datetime.utcnow()

    def update_equipment(self, equipment_types: List[str]) -> None:
        """Update available equipment types"""
        self.equipment_types = equipment_types
        self.updated_at = datetime.utcnow()


@dataclass
class MobileTeam:
    """
    Mobile team resource entity.

    Implements:
    - RG-FAC-003: Team configuration with base location, radius, capacity
    - RG-FAC-004: Service radius distance calculations
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    team_name: str = ""
    base_location: Optional[Location] = None
    service_radius_km: Decimal = Decimal('50')  # Default 50km - RG-FAC-003
    daily_capacity: int = 8  # Default 8 vehicles/day - RG-FAC-003
    equipment_types: List[str] = field(default_factory=list)
    status: ResourceStatus = ResourceStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate mobile team constraints - RG-FAC-003"""
        if not self.team_name or not self.team_name.strip():
            raise ValidationError("Team name cannot be empty")

        if self.service_radius_km <= 0:
            raise ValidationError("Service radius must be positive")

        if self.daily_capacity <= 0:
            raise ValidationError("Daily capacity must be positive")

        if self.base_location is None:
            raise ValidationError("Base location is required for mobile team")

    @classmethod
    def create(
        cls,
        team_name: str,
        base_location: Location,
        service_radius_km: Decimal = Decimal('50'),
        daily_capacity: int = 8,
        equipment_types: List[str] = None
    ) -> "MobileTeam":
        """Factory method to create a new mobile team with validation"""
        return cls(
            team_name=team_name,
            base_location=base_location,
            service_radius_km=service_radius_km,
            daily_capacity=daily_capacity,
            equipment_types=equipment_types or []
        )

    def can_service_location(self, customer_location: Location) -> bool:
        """
        Check if team can service the customer location.

        Implements RG-FAC-004: Distance-based service availability.
        Service is available if customer is within service radius.
        """
        if self.status != ResourceStatus.ACTIVE:
            return False

        if not self.base_location:
            return False

        distance = self.base_location.distance_to(customer_location)
        return distance <= self.service_radius_km

    def is_available_for_booking(self) -> bool:
        """Check if team is available for new bookings"""
        return self.status == ResourceStatus.ACTIVE

    def activate(self) -> None:
        """Activate the mobile team"""
        self.status = ResourceStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate the mobile team"""
        self.status = ResourceStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def update_service_radius(self, radius_km: Decimal) -> None:
        """Update service radius - RG-FAC-004"""
        if radius_km <= 0:
            raise ValidationError("Service radius must be positive")
        self.service_radius_km = radius_km
        self.updated_at = datetime.utcnow()

    def update_capacity(self, daily_capacity: int) -> None:
        """Update daily capacity - RG-FAC-003"""
        if daily_capacity <= 0:
            raise ValidationError("Daily capacity must be positive")
        self.daily_capacity = daily_capacity
        self.updated_at = datetime.utcnow()
