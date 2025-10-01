"""
Scheduling domain policies and business rules.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from .entities import (
    WashBay, MobileTeam, TimeSlot, VehicleSize, ResourceType, 
    SchedulingConstraints, Location
)


class ResourceAllocationPolicy:
    """Policy for resource allocation decisions."""
    
    @staticmethod
    def find_suitable_wash_bays(
        wash_bays: List[WashBay],
        vehicle_size: VehicleSize,
        required_equipment: List[str] = None
    ) -> List[WashBay]:
        """Find wash bays that can accommodate the request."""
        suitable_bays = []
        required_equipment = required_equipment or []
        
        for bay in wash_bays:
            if not bay.is_available_for_booking():
                continue
            
            if not bay.can_accommodate_vehicle(vehicle_size):
                continue
            
            # Check if bay has required equipment
            if required_equipment:
                bay_equipment = set(bay.equipment_types)
                required_set = set(required_equipment)
                if not required_set.issubset(bay_equipment):
                    continue
            
            suitable_bays.append(bay)
        
        return suitable_bays
    
    @staticmethod
    def find_suitable_mobile_teams(
        mobile_teams: List[MobileTeam],
        customer_location: Location,
        required_equipment: List[str] = None
    ) -> List[MobileTeam]:
        """Find mobile teams that can service the location."""
        suitable_teams = []
        required_equipment = required_equipment or []
        
        for team in mobile_teams:
            if not team.is_available_for_booking():
                continue
            
            if not team.can_service_location(customer_location):
                continue
            
            # Check if team has required equipment
            if required_equipment:
                team_equipment = set(team.equipment_types)
                required_set = set(required_equipment)
                if not required_set.issubset(team_equipment):
                    continue
            
            suitable_teams.append(team)
        
        return suitable_teams
    
    @staticmethod
    def rank_resources_by_preference(
        resources: List[any],
        customer_location: Optional[Location] = None
    ) -> List[any]:
        """Rank resources by preference criteria."""
        if not customer_location:
            return resources
        
        # For mobile teams, prefer closer ones
        def distance_key(resource):
            if hasattr(resource, 'base_location'):
                return resource.base_location.distance_to(customer_location)
            return Decimal('0')
        
        return sorted(resources, key=distance_key)


class AvailabilityPolicy:
    """Policy for checking availability."""
    
    @staticmethod
    def get_available_slots(
        resource_id: str,
        resource_type: ResourceType,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int,
        constraints: SchedulingConstraints,
        existing_bookings: List[TimeSlot] = None
    ) -> List[TimeSlot]:
        """Get available time slots for a resource."""
        available_slots = []
        existing_bookings = existing_bookings or []
        
        current_time = start_date
        while current_time < end_date:
            # Check if time meets scheduling constraints
            if not constraints.is_valid_booking_time(current_time):
                current_time += timedelta(minutes=constraints.slot_duration_minutes)
                continue
            
            # Create potential slot
            slot_end = current_time + timedelta(minutes=duration_minutes)
            potential_slot = TimeSlot(
                start_time=current_time,
                end_time=slot_end,
                resource_id=resource_id,
                resource_type=resource_type,
                buffer_minutes=constraints.buffer_minutes
            )
            
            # Check for conflicts with existing bookings
            has_conflict = any(
                potential_slot.conflicts_with(existing_slot)
                for existing_slot in existing_bookings
            )
            
            if not has_conflict:
                available_slots.append(potential_slot)
            
            current_time += timedelta(minutes=constraints.slot_duration_minutes)
        
        return available_slots
    
    @staticmethod
    def check_slot_availability(
        slot: TimeSlot,
        existing_bookings: List[TimeSlot],
        constraints: SchedulingConstraints
    ) -> bool:
        """Check if a specific slot is available."""
        # Check scheduling constraints
        if not constraints.is_valid_booking_time(slot.start_time):
            return False
        
        # Check for conflicts
        for existing_slot in existing_bookings:
            if slot.conflicts_with(existing_slot):
                return False
        
        return True


class OptimizationPolicy:
    """Policy for optimizing scheduling decisions."""
    
    @staticmethod
    def suggest_alternative_times(
        preferred_time: datetime,
        duration_minutes: int,
        resource_id: str,
        resource_type: ResourceType,
        constraints: SchedulingConstraints,
        existing_bookings: List[TimeSlot] = None,
        num_suggestions: int = 5
    ) -> List[TimeSlot]:
        """Suggest alternative times near the preferred time."""
        suggestions = []
        existing_bookings = existing_bookings or []
        
        # Search window: ±3 days from preferred time
        search_start = preferred_time - timedelta(days=3)
        search_end = preferred_time + timedelta(days=3)
        
        # Get all available slots in the window
        available_slots = AvailabilityPolicy.get_available_slots(
            resource_id=resource_id,
            resource_type=resource_type,
            start_date=search_start,
            end_date=search_end,
            duration_minutes=duration_minutes,
            constraints=constraints,
            existing_bookings=existing_bookings
        )
        
        # Sort by proximity to preferred time
        def time_distance(slot: TimeSlot) -> int:
            return abs((slot.start_time - preferred_time).total_seconds())
        
        sorted_slots = sorted(available_slots, key=time_distance)
        
        return sorted_slots[:num_suggestions]
    
    @staticmethod
    def optimize_mobile_team_route(
        team: MobileTeam,
        bookings: List[Dict[str, Any]],
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Optimize route for mobile team bookings on a given date."""
        # Simple optimization: sort by distance from base location
        # In real implementation, would use proper route optimization algorithm
        
        def distance_from_base(booking):
            location = booking.get('location')
            if location:
                return team.base_location.distance_to(location)
            return Decimal('999999')  # Far distance for bookings without location
        
        return sorted(bookings, key=distance_from_base)


class CapacityPolicy:
    """Policy for managing resource capacity."""
    
    @staticmethod
    def check_daily_capacity(
        resource: any,
        date: datetime,
        existing_bookings: List[TimeSlot]
    ) -> bool:
        """Check if resource has capacity for more bookings on a date."""
        # For wash bays, capacity is essentially unlimited (one at a time)
        if isinstance(resource, WashBay):
            return resource.is_available_for_booking()
        
        # For mobile teams, check daily capacity
        if isinstance(resource, MobileTeam):
            if not resource.is_available_for_booking():
                return False
            
            # Count bookings for the date
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            daily_bookings = [
                booking for booking in existing_bookings
                if (day_start <= booking.start_time < day_end and 
                    booking.resource_id == resource.id)
            ]
            
            return len(daily_bookings) < resource.daily_capacity
        
        return False
    
    @staticmethod
    def get_capacity_utilization(
        resource: any,
        date: datetime,
        existing_bookings: List[TimeSlot]
    ) -> float:
        """Get capacity utilization percentage for a resource on a date."""
        if isinstance(resource, WashBay):
            # For wash bays, check hourly utilization
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Count booked hours
            booked_minutes = sum(
                booking.duration_minutes for booking in existing_bookings
                if (day_start <= booking.start_time < day_end and 
                    booking.resource_id == resource.id)
            )
            
            # Assume 12 hours of operation per day (720 minutes)
            total_available_minutes = 720
            return (booked_minutes / total_available_minutes) * 100
        
        if isinstance(resource, MobileTeam):
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            daily_bookings = [
                booking for booking in existing_bookings
                if (day_start <= booking.start_time < day_end and 
                    booking.resource_id == resource.id)
            ]
            
            return (len(daily_bookings) / resource.daily_capacity) * 100
        
        return 0.0