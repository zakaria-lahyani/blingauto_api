"""
Wash facility specific domain entities for capacity management
"""
from datetime import datetime, time
from typing import List, Optional, Dict, Set
from uuid import UUID, uuid4
from enum import Enum

from .enums import ResourceStatus


class WashType(Enum):
    """Types of wash services"""
    STATIONARY = "stationary"  # Customer comes to wash bay
    MOBILE = "mobile"  # Wash team goes to customer location


class LocationType(Enum):
    """Types of service locations"""
    WASH_BAY = "wash_bay"  # Fixed location at facility
    CUSTOMER_LOCATION = "customer_location"  # Mobile service
    PICKUP_DROPOFF = "pickup_dropoff"  # We pick up and return vehicle


class WashBay:
    """Physical wash bay at the facility"""
    
    def __init__(
        self,
        name: str,
        bay_number: int,
        is_active: bool = True,
        equipment_types: Optional[Set[str]] = None,
        max_vehicle_size: str = "standard",  # compact, standard, large, oversized
        has_covered_area: bool = True,
        has_power_supply: bool = True,
        notes: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.name = name
        self.bay_number = bay_number
        self.is_active = is_active
        self.equipment_types = equipment_types or set()
        self.max_vehicle_size = max_vehicle_size
        self.has_covered_area = has_covered_area
        self.has_power_supply = has_power_supply
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
    
    def can_accommodate_vehicle(self, vehicle_size: str) -> bool:
        """Check if bay can accommodate vehicle size"""
        size_hierarchy = ["compact", "standard", "large", "oversized"]
        max_index = size_hierarchy.index(self.max_vehicle_size)
        vehicle_index = size_hierarchy.index(vehicle_size)
        return vehicle_index <= max_index
    
    def has_equipment(self, required_equipment: Set[str]) -> bool:
        """Check if bay has required equipment"""
        return required_equipment.issubset(self.equipment_types)
    
    def activate(self):
        """Activate the wash bay"""
        self.is_active = True
    
    def deactivate(self, reason: Optional[str] = None):
        """Deactivate the wash bay"""
        self.is_active = False
        if reason:
            self.notes = f"Deactivated: {reason}"


class MobileWashTeam:
    """Mobile wash team that can service customers at their location"""
    
    def __init__(
        self,
        name: str,
        team_size: int,
        equipment_types: Optional[Set[str]] = None,
        service_radius_km: float = 50.0,
        max_vehicles_per_day: int = 8,
        hourly_rate: Optional[float] = None,
        is_active: bool = True,
        base_location: Optional[Dict[str, float]] = None,  # {"lat": 40.7128, "lng": -74.0060}
        notes: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.name = name
        self.team_size = team_size
        self.equipment_types = equipment_types or set()
        self.service_radius_km = service_radius_km
        self.max_vehicles_per_day = max_vehicles_per_day
        self.hourly_rate = hourly_rate
        self.is_active = is_active
        self.base_location = base_location or {}
        self.notes = notes
        self.created_at = created_at or datetime.utcnow()
    
    def can_service_location(self, customer_location: Dict[str, float]) -> bool:
        """Check if team can service customer location based on radius"""
        if not self.base_location or not customer_location:
            return True  # Assume serviceable if no location data
        
        # Simple distance calculation (in real app, use proper geo calculation)
        lat_diff = abs(self.base_location.get("lat", 0) - customer_location.get("lat", 0))
        lng_diff = abs(self.base_location.get("lng", 0) - customer_location.get("lng", 0))
        
        # Rough distance approximation (not accurate, for demo purposes)
        distance_km = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # 1 degree ≈ 111 km
        
        return distance_km <= self.service_radius_km
    
    def has_equipment(self, required_equipment: Set[str]) -> bool:
        """Check if team has required equipment"""
        return required_equipment.issubset(self.equipment_types)
    
    def activate(self):
        """Activate the mobile team"""
        self.is_active = True
    
    def deactivate(self, reason: Optional[str] = None):
        """Deactivate the mobile team"""
        self.is_active = False
        if reason:
            self.notes = f"Deactivated: {reason}"


class WashFacilityConfiguration:
    """Overall wash facility configuration"""
    
    def __init__(
        self,
        facility_name: str,
        total_wash_bays: int,
        total_mobile_teams: int,
        wash_bays: Optional[List[WashBay]] = None,
        mobile_teams: Optional[List[MobileWashTeam]] = None,
        operating_hours: Optional[Dict] = None,
        default_service_duration_minutes: int = 60,
        buffer_between_services_minutes: int = 15,
        max_advance_booking_days: int = 30,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.facility_name = facility_name
        self.total_wash_bays = total_wash_bays
        self.total_mobile_teams = total_mobile_teams
        self.wash_bays = wash_bays or []
        self.mobile_teams = mobile_teams or []
        self.operating_hours = operating_hours or {}
        self.default_service_duration_minutes = default_service_duration_minutes
        self.buffer_between_services_minutes = buffer_between_services_minutes
        self.max_advance_booking_days = max_advance_booking_days
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def get_available_wash_bays(self) -> List[WashBay]:
        """Get all active wash bays"""
        return [bay for bay in self.wash_bays if bay.is_active]
    
    def get_available_mobile_teams(self) -> List[MobileWashTeam]:
        """Get all active mobile teams"""
        return [team for team in self.mobile_teams if team.is_active]
    
    def get_total_capacity(self, wash_type: WashType) -> int:
        """Get total capacity for a wash type"""
        if wash_type == WashType.STATIONARY:
            return len(self.get_available_wash_bays())
        elif wash_type == WashType.MOBILE:
            return len(self.get_available_mobile_teams())
        return 0
    
    def add_wash_bay(self, wash_bay: WashBay) -> None:
        """Add a wash bay to the facility"""
        self.wash_bays.append(wash_bay)
        self.total_wash_bays = len(self.wash_bays)
        self.updated_at = datetime.utcnow()
    
    def add_mobile_team(self, mobile_team: MobileWashTeam) -> None:
        """Add a mobile team to the facility"""
        self.mobile_teams.append(mobile_team)
        self.total_mobile_teams = len(self.mobile_teams)
        self.updated_at = datetime.utcnow()
    
    def remove_wash_bay(self, bay_id: UUID) -> bool:
        """Remove a wash bay from the facility"""
        original_count = len(self.wash_bays)
        self.wash_bays = [bay for bay in self.wash_bays if bay.id != bay_id]
        if len(self.wash_bays) < original_count:
            self.total_wash_bays = len(self.wash_bays)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def remove_mobile_team(self, team_id: UUID) -> bool:
        """Remove a mobile team from the facility"""
        original_count = len(self.mobile_teams)
        self.mobile_teams = [team for team in self.mobile_teams if team.id != team_id]
        if len(self.mobile_teams) < original_count:
            self.total_mobile_teams = len(self.mobile_teams)
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def find_best_resource_for_booking(
        self,
        wash_type: WashType,
        required_equipment: Optional[Set[str]] = None,
        vehicle_size: str = "standard",
        customer_location: Optional[Dict[str, float]] = None
    ) -> Optional[object]:
        """Find the best resource (bay or mobile team) for a booking"""
        
        if wash_type == WashType.STATIONARY:
            # Find best wash bay
            suitable_bays = []
            for bay in self.get_available_wash_bays():
                if bay.can_accommodate_vehicle(vehicle_size):
                    if not required_equipment or bay.has_equipment(required_equipment):
                        suitable_bays.append(bay)
            
            # Return first suitable bay (could be enhanced with more logic)
            return suitable_bays[0] if suitable_bays else None
        
        elif wash_type == WashType.MOBILE:
            # Find best mobile team
            suitable_teams = []
            for team in self.get_available_mobile_teams():
                if customer_location and not team.can_service_location(customer_location):
                    continue
                if not required_equipment or team.has_equipment(required_equipment):
                    suitable_teams.append(team)
            
            # Return team with smallest service radius (closest to base)
            return min(suitable_teams, key=lambda t: t.service_radius_km) if suitable_teams else None
        
        return None


class CapacityAllocation:
    """Tracks capacity allocation for a specific time period"""
    
    def __init__(
        self,
        date: datetime,
        wash_type: WashType,
        resource_id: UUID,
        resource_name: str,
        allocated_slots: int = 0,
        max_capacity: int = 1,
        bookings: Optional[List[UUID]] = None
    ):
        self.date = date
        self.wash_type = wash_type
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.allocated_slots = allocated_slots
        self.max_capacity = max_capacity
        self.bookings = bookings or []
    
    def is_available(self) -> bool:
        """Check if resource has available capacity"""
        return self.allocated_slots < self.max_capacity
    
    def get_available_slots(self) -> int:
        """Get number of available slots"""
        return max(0, self.max_capacity - self.allocated_slots)
    
    def allocate_slot(self, booking_id: UUID) -> bool:
        """Allocate a slot for a booking"""
        if self.is_available():
            self.allocated_slots += 1
            self.bookings.append(booking_id)
            return True
        return False
    
    def release_slot(self, booking_id: UUID) -> bool:
        """Release a slot from a booking"""
        if booking_id in self.bookings:
            self.bookings.remove(booking_id)
            self.allocated_slots = max(0, self.allocated_slots - 1)
            return True
        return False