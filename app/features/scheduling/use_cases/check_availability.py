"""
Check Availability Use Case - RG-SCH-001, RG-SCH-002
Implements availability checking logic for bookings.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..domain.entities import (
    VehicleSize, ResourceType, TimeSlot, Location, WashBay, MobileTeam
)
from ..domain.policies import (
    ResourceAllocationPolicy, AvailabilityPolicy, CapacityPolicy
)
from ..ports.repositories import (
    IWashBayRepository, IMobileTeamRepository, ITimeSlotRepository,
    ISchedulingConstraintsRepository
)
from ..ports.services import IDistanceCalculationService
from app.core.errors import ValidationError, BusinessRuleViolationError


class CheckAvailabilityUseCase:
    """Use case for checking availability for booking requests."""
    
    def __init__(
        self,
        wash_bay_repo: IWashBayRepository,
        mobile_team_repo: IMobileTeamRepository,
        time_slot_repo: ITimeSlotRepository,
        constraints_repo: ISchedulingConstraintsRepository,
        distance_service: Optional[IDistanceCalculationService] = None
    ):
        self.wash_bay_repo = wash_bay_repo
        self.mobile_team_repo = mobile_team_repo
        self.time_slot_repo = time_slot_repo
        self.constraints_repo = constraints_repo
        self.distance_service = distance_service
    
    async def execute(
        self,
        requested_time: datetime,
        duration_minutes: int,
        vehicle_size: VehicleSize,
        service_type: ResourceType,
        customer_location: Optional[Location] = None,
        required_equipment: List[str] = None
    ) -> Dict[str, Any]:
        """Check availability for a booking request."""
        
        # Validate inputs
        if duration_minutes <= 0:
            raise ValidationError("Duration must be positive")
        
        if service_type == ResourceType.MOBILE_TEAM and not customer_location:
            raise ValidationError("Customer location required for mobile service")
        
        # Get scheduling constraints
        constraints = await self.constraints_repo.get_current_constraints()
        
        # Validate requested time against constraints
        if not constraints.is_valid_booking_time(requested_time):
            return {
                "available": False,
                "reason": "Requested time violates scheduling constraints",
                "alternatives": await self._suggest_alternatives(
                    requested_time, duration_minutes, vehicle_size,
                    service_type, customer_location, required_equipment
                )
            }
        
        # Get suitable resources
        suitable_resources = await self._get_suitable_resources(
            service_type, vehicle_size, customer_location, required_equipment
        )
        
        if not suitable_resources:
            return {
                "available": False,
                "reason": "No suitable resources available",
                "alternatives": []
            }
        
        # Check availability for each suitable resource
        for resource in suitable_resources:
            is_available = await self._check_resource_availability(
                resource, requested_time, duration_minutes, constraints
            )
            
            if is_available:
                return {
                    "available": True,
                    "resource_id": resource.id,
                    "resource_type": service_type.value,
                    "confirmed_time": requested_time,
                    "duration_minutes": duration_minutes,
                    "estimated_travel_time": await self._calculate_travel_time(
                        resource, customer_location
                    )
                }
        
        # No resources available at requested time
        return {
            "available": False,
            "reason": "No resources available at requested time",
            "alternatives": await self._suggest_alternatives(
                requested_time, duration_minutes, vehicle_size,
                service_type, customer_location, required_equipment
            )
        }
    
    async def _get_suitable_resources(
        self,
        service_type: ResourceType,
        vehicle_size: VehicleSize,
        customer_location: Optional[Location],
        required_equipment: List[str] = None
    ) -> List[any]:
        """Get resources suitable for the request."""
        
        if service_type == ResourceType.WASH_BAY:
            wash_bays = await self.wash_bay_repo.get_all_active()
            return ResourceAllocationPolicy.find_suitable_wash_bays(
                wash_bays, vehicle_size, required_equipment
            )
        
        elif service_type == ResourceType.MOBILE_TEAM:
            mobile_teams = await self.mobile_team_repo.get_all_active()
            suitable_teams = ResourceAllocationPolicy.find_suitable_mobile_teams(
                mobile_teams, customer_location, required_equipment
            )
            return ResourceAllocationPolicy.rank_resources_by_preference(
                suitable_teams, customer_location
            )
        
        return []
    
    async def _check_resource_availability(
        self,
        resource: any,
        requested_time: datetime,
        duration_minutes: int,
        constraints
    ) -> bool:
        """Check if a specific resource is available at the requested time."""
        
        # Check daily capacity
        if not CapacityPolicy.check_daily_capacity(
            resource, requested_time, []
        ):
            return False
        
        # Get existing bookings for the resource
        search_start = requested_time - timedelta(hours=1)
        search_end = requested_time + timedelta(hours=2)
        
        existing_bookings = await self.time_slot_repo.get_bookings_for_resource(
            resource.id, search_start, search_end
        )
        
        # Create potential time slot
        potential_slot = TimeSlot(
            start_time=requested_time,
            end_time=requested_time + timedelta(minutes=duration_minutes),
            resource_id=resource.id,
            resource_type=ResourceType.WASH_BAY if isinstance(resource, WashBay) else ResourceType.MOBILE_TEAM,
            buffer_minutes=constraints.buffer_minutes
        )
        
        # Check availability
        return AvailabilityPolicy.check_slot_availability(
            potential_slot, existing_bookings, constraints
        )
    
    async def _calculate_travel_time(
        self,
        resource: any,
        customer_location: Optional[Location]
    ) -> Optional[int]:
        """Calculate travel time for mobile services."""
        
        if not isinstance(resource, MobileTeam) or not customer_location:
            return None
        
        if self.distance_service:
            return await self.distance_service.calculate_travel_time(
                resource.base_location, customer_location
            )
        
        # Fallback calculation
        distance = resource.base_location.distance_to(customer_location)
        # Assume 30 km/h average speed
        travel_time_hours = distance / Decimal('30')
        return int(travel_time_hours * 60)  # Convert to minutes
    
    async def _suggest_alternatives(
        self,
        requested_time: datetime,
        duration_minutes: int,
        vehicle_size: VehicleSize,
        service_type: ResourceType,
        customer_location: Optional[Location],
        required_equipment: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Suggest alternative times and resources."""
        
        alternatives = []
        constraints = await self.constraints_repo.get_current_constraints()
        suitable_resources = await self._get_suitable_resources(
            service_type, vehicle_size, customer_location, required_equipment
        )
        
        for resource in suitable_resources[:3]:  # Limit to top 3 resources
            # Get available slots around the requested time
            search_start = requested_time - timedelta(days=1)
            search_end = requested_time + timedelta(days=3)
            
            existing_bookings = await self.time_slot_repo.get_bookings_for_resource(
                resource.id, search_start, search_end
            )
            
            available_slots = AvailabilityPolicy.get_available_slots(
                resource_id=resource.id,
                resource_type=service_type,
                start_date=search_start,
                end_date=search_end,
                duration_minutes=duration_minutes,
                constraints=constraints,
                existing_bookings=existing_bookings
            )
            
            # Get the closest alternatives
            for slot in available_slots[:3]:
                alternatives.append({
                    "resource_id": resource.id,
                    "resource_type": service_type.value,
                    "suggested_time": slot.start_time,
                    "duration_minutes": duration_minutes,
                    "time_difference_hours": abs(
                        (slot.start_time - requested_time).total_seconds() / 3600
                    )
                })
        
        # Sort by time difference
        alternatives.sort(key=lambda x: x["time_difference_hours"])
        
        return alternatives[:5]  # Return top 5 alternatives


class GetAvailableSlotsUseCase:
    """Use case for getting all available slots in a time range."""
    
    def __init__(
        self,
        wash_bay_repo: IWashBayRepository,
        mobile_team_repo: IMobileTeamRepository,
        time_slot_repo: ITimeSlotRepository,
        constraints_repo: ISchedulingConstraintsRepository
    ):
        self.wash_bay_repo = wash_bay_repo
        self.mobile_team_repo = mobile_team_repo
        self.time_slot_repo = time_slot_repo
        self.constraints_repo = constraints_repo
    
    async def execute(
        self,
        start_date: datetime,
        end_date: datetime,
        service_type: ResourceType,
        duration_minutes: int = 60,
        vehicle_size: VehicleSize = VehicleSize.STANDARD,
        customer_location: Optional[Location] = None
    ) -> List[Dict[str, Any]]:
        """Get all available slots for the specified criteria."""
        
        constraints = await self.constraints_repo.get_current_constraints()
        available_slots = []
        
        # Get suitable resources
        if service_type == ResourceType.WASH_BAY:
            resources = await self.wash_bay_repo.get_all_active()
            suitable_resources = ResourceAllocationPolicy.find_suitable_wash_bays(
                resources, vehicle_size
            )
        else:
            resources = await self.mobile_team_repo.get_all_active()
            suitable_resources = ResourceAllocationPolicy.find_suitable_mobile_teams(
                resources, customer_location
            )
        
        # Get available slots for each resource
        for resource in suitable_resources:
            existing_bookings = await self.time_slot_repo.get_bookings_for_resource(
                resource.id, start_date, end_date
            )
            
            resource_slots = AvailabilityPolicy.get_available_slots(
                resource_id=resource.id,
                resource_type=service_type,
                start_date=start_date,
                end_date=end_date,
                duration_minutes=duration_minutes,
                constraints=constraints,
                existing_bookings=existing_bookings
            )
            
            for slot in resource_slots:
                available_slots.append({
                    "resource_id": resource.id,
                    "resource_type": service_type.value,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "duration_minutes": slot.duration_minutes,
                    "capacity_utilization": CapacityPolicy.get_capacity_utilization(
                        resource, slot.start_time, existing_bookings
                    )
                })
        
        # Sort by start time
        available_slots.sort(key=lambda x: x["start_time"])
        
        return available_slots