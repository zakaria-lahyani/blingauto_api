"""
Slot Management Use Cases for Scheduling Feature.
Implements time slot creation, reservation, and management.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from ..domain.entities import TimeSlot, ResourceType, VehicleSize, Location
from ..domain.policies import AvailabilityPolicy, CapacityPolicy
from ..ports.repositories import (
    ITimeSlotRepository, IWashBayRepository, IMobileTeamRepository,
    ISchedulingConstraintsRepository
)


@dataclass
class BookSlotRequest:
    resource_id: str
    resource_type: ResourceType
    start_time: datetime
    duration_minutes: int
    booking_id: str
    customer_id: str


@dataclass
class BookSlotResponse:
    success: bool
    slot_id: Optional[str] = None
    confirmed_time: Optional[datetime] = None
    resource_id: Optional[str] = None
    message: str = ""


@dataclass
class CancelSlotRequest:
    slot_id: str
    cancelled_by: str
    reason: str = "cancelled_by_customer"


@dataclass
class CancelSlotResponse:
    success: bool
    message: str
    cancelled_slot_id: str


@dataclass
class GetAvailableSlotsRequest:
    start_date: datetime
    end_date: datetime
    service_type: ResourceType
    duration_minutes: int = 60
    vehicle_size: VehicleSize = VehicleSize.STANDARD
    customer_location: Optional[Location] = None


@dataclass
class SlotInfo:
    resource_id: str
    resource_type: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    capacity_utilization: float


@dataclass
class GetAvailableSlotsResponse:
    slots: List[SlotInfo]
    total_count: int
    search_criteria: Dict[str, Any]


class BookSlotUseCase:
    """Use case for booking a specific time slot."""
    
    def __init__(
        self,
        time_slot_repository: ITimeSlotRepository,
        wash_bay_repository: IWashBayRepository,
        mobile_team_repository: IMobileTeamRepository,
        constraints_repository: ISchedulingConstraintsRepository
    ):
        self._time_slot_repository = time_slot_repository
        self._wash_bay_repository = wash_bay_repository
        self._mobile_team_repository = mobile_team_repository
        self._constraints_repository = constraints_repository
    
    def execute(self, request: BookSlotRequest) -> BookSlotResponse:
        """Execute book slot use case."""
        
        # Validate inputs
        if request.duration_minutes <= 0:
            raise ValidationError("Duration must be positive")
        
        # Get scheduling constraints
        constraints = self._constraints_repository.get_current_constraints()
        
        # Validate requested time against constraints
        if not constraints.is_valid_booking_time(request.start_time):
            return BookSlotResponse(
                success=False,
                message="Requested time violates scheduling constraints"
            )
        
        # Get resource to validate it exists and is available
        resource = None
        if request.resource_type == ResourceType.WASH_BAY:
            resource = self._wash_bay_repository.get_by_id(request.resource_id)
            if not resource:
                raise NotFoundError(f"Wash bay {request.resource_id} not found")
            
            if not resource.is_available_for_booking():
                return BookSlotResponse(
                    success=False,
                    message="Wash bay is not available for booking"
                )
        
        elif request.resource_type == ResourceType.MOBILE_TEAM:
            resource = self._mobile_team_repository.get_by_id(request.resource_id)
            if not resource:
                raise NotFoundError(f"Mobile team {request.resource_id} not found")
            
            if not resource.is_available_for_booking():
                return BookSlotResponse(
                    success=False,
                    message="Mobile team is not available for booking"
                )
        
        # Check for conflicts with existing bookings
        search_start = request.start_time - timedelta(hours=1)
        search_end = request.start_time + timedelta(hours=2)
        
        existing_bookings = self._time_slot_repository.get_bookings_for_resource(
            request.resource_id, search_start, search_end
        )
        
        # Create potential time slot
        end_time = request.start_time + timedelta(minutes=request.duration_minutes)
        potential_slot = TimeSlot(
            start_time=request.start_time,
            end_time=end_time,
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            buffer_minutes=constraints.buffer_minutes
        )
        
        # Check availability
        if not AvailabilityPolicy.check_slot_availability(
            potential_slot, existing_bookings, constraints
        ):
            return BookSlotResponse(
                success=False,
                message="Time slot conflicts with existing booking"
            )
        
        # Check daily capacity
        if not CapacityPolicy.check_daily_capacity(
            resource, request.start_time, existing_bookings
        ):
            return BookSlotResponse(
                success=False,
                message="Resource has reached daily capacity"
            )
        
        # Reserve the slot
        potential_slot.reserve_for_booking(request.booking_id)
        
        # Save to repository
        saved_slot = self._time_slot_repository.create_booking(potential_slot)
        
        return BookSlotResponse(
            success=True,
            slot_id=saved_slot.id,
            confirmed_time=saved_slot.start_time,
            resource_id=saved_slot.resource_id,
            message="Time slot successfully booked"
        )


class CancelSlotUseCase:
    """Use case for cancelling a booked time slot."""
    
    def __init__(self, time_slot_repository: ITimeSlotRepository):
        self._time_slot_repository = time_slot_repository
    
    def execute(self, request: CancelSlotRequest) -> CancelSlotResponse:
        """Execute cancel slot use case."""
        
        # Get the time slot
        success = self._time_slot_repository.cancel_booking(request.slot_id)
        
        if not success:
            raise NotFoundError(f"Time slot {request.slot_id} not found")
        
        return CancelSlotResponse(
            success=True,
            message="Time slot cancelled successfully",
            cancelled_slot_id=request.slot_id
        )


class GetAvailableSlotsUseCase:
    """Use case for getting all available slots in a time range."""
    
    def __init__(
        self,
        wash_bay_repository: IWashBayRepository,
        mobile_team_repository: IMobileTeamRepository,
        time_slot_repository: ITimeSlotRepository,
        constraints_repository: ISchedulingConstraintsRepository
    ):
        self._wash_bay_repository = wash_bay_repository
        self._mobile_team_repository = mobile_team_repository
        self._time_slot_repository = time_slot_repository
        self._constraints_repository = constraints_repository
    
    def execute(self, request: GetAvailableSlotsRequest) -> GetAvailableSlotsResponse:
        """Execute get available slots use case."""
        
        # Validate date range
        if request.end_date <= request.start_date:
            raise ValidationError("End date must be after start date")
        
        # Limit search range to prevent excessive queries
        if (request.end_date - request.start_date).days > 30:
            raise ValidationError("Search range cannot exceed 30 days")
        
        constraints = self._constraints_repository.get_current_constraints()
        available_slots = []
        
        # Get suitable resources
        if request.service_type == ResourceType.WASH_BAY:
            resources = self._wash_bay_repository.get_all_active()
            # Filter by vehicle size if needed
            suitable_resources = [
                bay for bay in resources 
                if bay.can_accommodate_vehicle(request.vehicle_size)
            ]
        else:
            resources = self._mobile_team_repository.get_all_active()
            # Filter by location if needed
            suitable_resources = resources
            if request.customer_location:
                suitable_resources = [
                    team for team in resources
                    if team.can_service_location(request.customer_location)
                ]
        
        # Get available slots for each resource
        for resource in suitable_resources:
            existing_bookings = self._time_slot_repository.get_bookings_for_resource(
                resource.id, request.start_date, request.end_date
            )
            
            resource_slots = AvailabilityPolicy.get_available_slots(
                resource_id=resource.id,
                resource_type=request.service_type,
                start_date=request.start_date,
                end_date=request.end_date,
                duration_minutes=request.duration_minutes,
                constraints=constraints,
                existing_bookings=existing_bookings
            )
            
            for slot in resource_slots:
                available_slots.append(SlotInfo(
                    resource_id=resource.id,
                    resource_type=request.service_type.value,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    duration_minutes=slot.duration_minutes,
                    capacity_utilization=CapacityPolicy.get_capacity_utilization(
                        resource, slot.start_time, existing_bookings
                    )
                ))
        
        # Sort by start time
        available_slots.sort(key=lambda x: x.start_time)
        
        search_criteria = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "service_type": request.service_type.value,
            "duration_minutes": request.duration_minutes,
            "vehicle_size": request.vehicle_size.value
        }
        
        if request.customer_location:
            search_criteria["customer_location"] = {
                "latitude": float(request.customer_location.latitude),
                "longitude": float(request.customer_location.longitude)
            }
        
        return GetAvailableSlotsResponse(
            slots=available_slots,
            total_count=len(available_slots),
            search_criteria=search_criteria
        )


class RescheduleSlotUseCase:
    """Use case for rescheduling an existing time slot."""
    
    def __init__(
        self,
        time_slot_repository: ITimeSlotRepository,
        constraints_repository: ISchedulingConstraintsRepository
    ):
        self._time_slot_repository = time_slot_repository
        self._constraints_repository = constraints_repository
    
    def execute(
        self,
        slot_id: str,
        new_start_time: datetime,
        new_duration_minutes: Optional[int] = None
    ) -> BookSlotResponse:
        """Execute reschedule slot use case."""
        
        # Get existing slot
        existing_slots = self._time_slot_repository.get_bookings_for_resource(
            "", datetime.min, datetime.max  # This is a simplification
        )
        
        current_slot = None
        for slot in existing_slots:
            if slot.id == slot_id:
                current_slot = slot
                break
        
        if not current_slot:
            raise NotFoundError(f"Time slot {slot_id} not found")
        
        # Use existing duration if not specified
        duration = new_duration_minutes or current_slot.duration_minutes
        
        # Get constraints
        constraints = self._constraints_repository.get_current_constraints()
        
        # Validate new time
        if not constraints.is_valid_booking_time(new_start_time):
            return BookSlotResponse(
                success=False,
                message="New time violates scheduling constraints"
            )
        
        # Check for conflicts (excluding current slot)
        search_start = new_start_time - timedelta(hours=1)
        search_end = new_start_time + timedelta(hours=2)
        
        existing_bookings = self._time_slot_repository.get_bookings_for_resource(
            current_slot.resource_id, search_start, search_end
        )
        
        # Remove current slot from conflict check
        existing_bookings = [b for b in existing_bookings if b.id != slot_id]
        
        # Create new potential slot
        new_end_time = new_start_time + timedelta(minutes=duration)
        potential_slot = TimeSlot(
            start_time=new_start_time,
            end_time=new_end_time,
            resource_id=current_slot.resource_id,
            resource_type=current_slot.resource_type,
            buffer_minutes=constraints.buffer_minutes
        )
        
        # Check availability
        if not AvailabilityPolicy.check_slot_availability(
            potential_slot, existing_bookings, constraints
        ):
            return BookSlotResponse(
                success=False,
                message="New time slot conflicts with existing booking"
            )
        
        # Update the slot
        current_slot.start_time = new_start_time
        current_slot.end_time = new_end_time
        
        updated_slot = self._time_slot_repository.update_booking(current_slot)
        
        return BookSlotResponse(
            success=True,
            slot_id=updated_slot.id,
            confirmed_time=updated_slot.start_time,
            resource_id=updated_slot.resource_id,
            message="Time slot successfully rescheduled"
        )