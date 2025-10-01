"""
Scheduling API router.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from .schemas import (
    AvailabilityCheckRequest, AvailabilityCheckResponse,
    GetSlotsRequest, GetSlotsResponse,
    ResourceListResponse, BookingSlotRequest, BookingSlotResponse,
    LocationSchema
)
from ..domain.entities import ResourceType, VehicleSize, Location
from ..use_cases.check_availability import CheckAvailabilityUseCase, GetAvailableSlotsUseCase
from ..use_cases.manage_slots import BookSlotUseCase, CancelSlotUseCase, GetAvailableSlotsRequest as UseCaseGetSlotsRequest
from ..use_cases.manage_resources import ListResourcesUseCase, ListResourcesRequest
from app.core.errors import ValidationError, BusinessRuleViolationError
from app.shared.auth import get_current_user, CurrentUser

router = APIRouter()


# Dependency injection placeholders - would be configured in main app
def get_check_availability_use_case() -> CheckAvailabilityUseCase:
    raise NotImplementedError("Dependency injection not configured")

def get_list_resources_use_case() -> ListResourcesUseCase:
    raise NotImplementedError("Dependency injection not configured")

def get_book_slot_use_case() -> BookSlotUseCase:
    raise NotImplementedError("Dependency injection not configured")

def get_cancel_slot_use_case() -> CancelSlotUseCase:
    raise NotImplementedError("Dependency injection not configured")

def get_available_slots_use_case() -> GetAvailableSlotsUseCase:
    raise NotImplementedError("Dependency injection not configured")


@router.post("/check-availability", response_model=AvailabilityCheckResponse)
async def check_availability(
    request: AvailabilityCheckRequest,
    current_user: CurrentUser,
    use_case: CheckAvailabilityUseCase = Depends(get_check_availability_use_case),
):
    """
    Check availability for a booking request.
    
    This endpoint implements scheduling rules defined in:
    - RG-SCH-001: Business hours and constraints
    - RG-SCH-002: Advance booking requirements
    - RG-FAC-001: Wash bay constraints  
    - RG-FAC-002: Vehicle size compatibility
    - RG-FAC-003: Mobile team capacity
    - RG-FAC-004: Service radius limitations
    """
    try:
        # Convert request location if provided
        customer_location = None
        if request.customer_location:
            customer_location = Location(
                latitude=request.customer_location.latitude,
                longitude=request.customer_location.longitude
            )
        
        # Execute use case
        result = await use_case.execute(
            requested_time=request.requested_time,
            duration_minutes=request.duration_minutes,
            vehicle_size=request.vehicle_size,
            service_type=request.service_type,
            customer_location=customer_location,
            required_equipment=request.required_equipment
        )
        
        return AvailabilityCheckResponse(**result)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/available-slots", response_model=GetSlotsResponse)
async def get_available_slots(
    request: GetSlotsRequest,
    current_user: CurrentUser,
):
    """
    Get all available time slots for the specified criteria.
    
    Returns available slots within the date range that meet the
    vehicle size and service type requirements.
    """
    try:
        # Mock implementation for now
        mock_slots = []
        
        # Generate some mock slots
        current_time = request.start_date
        while current_time < request.end_date:
            # Skip past times and weekends for simplicity
            if current_time > datetime.utcnow() and current_time.weekday() < 5:
                mock_slots.append({
                    "resource_id": f"resource-{current_time.hour % 3 + 1}",
                    "resource_type": request.service_type.value,
                    "start_time": current_time,
                    "end_time": current_time + timedelta(minutes=request.duration_minutes),
                    "duration_minutes": request.duration_minutes,
                    "capacity_utilization": 25.0
                })
            
            current_time += timedelta(hours=1)
        
        return GetSlotsResponse(
            slots=mock_slots[:20],  # Limit to 20 slots
            total_count=len(mock_slots),
            search_criteria={
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "service_type": request.service_type.value,
                "duration_minutes": request.duration_minutes,
                "vehicle_size": request.vehicle_size.value
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/resources", response_model=ResourceListResponse)
async def list_resources():
    """
    List all available scheduling resources (wash bays and mobile teams).
    
    Returns information about available wash bays and mobile teams
    including their capabilities and current utilization.
    """
    try:
        # Mock implementation
        mock_wash_bays = [
            {
                "id": "bay-001",
                "bay_number": "Bay 1",
                "max_vehicle_size": VehicleSize.LARGE.value,
                "equipment_types": ["pressure_washer", "foam_cannon", "dryer"],
                "status": "active",
                "current_utilization": 65.0
            },
            {
                "id": "bay-002", 
                "bay_number": "Bay 2",
                "max_vehicle_size": VehicleSize.OVERSIZED.value,
                "equipment_types": ["pressure_washer", "foam_cannon", "dryer", "wax_applicator"],
                "status": "active",
                "current_utilization": 80.0
            }
        ]
        
        mock_mobile_teams = [
            {
                "id": "team-001",
                "team_name": "Mobile Team Alpha",
                "base_location": {"latitude": 40.7128, "longitude": -74.0060},
                "service_radius_km": 50,
                "daily_capacity": 8,
                "equipment_types": ["portable_washer", "vacuum", "detailing_kit"],
                "status": "active",
                "current_utilization": 62.5
            }
        ]
        
        return ResourceListResponse(
            wash_bays=mock_wash_bays,
            mobile_teams=mock_mobile_teams,
            total_wash_bays=len(mock_wash_bays),
            total_mobile_teams=len(mock_mobile_teams)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/book-slot", response_model=BookingSlotResponse)
async def book_time_slot(
    request: BookingSlotRequest,
    # TODO: Add proper authentication when available
    # current_user = Depends(get_current_user),
):
    """
    Book a specific time slot for a customer.
    
    This endpoint reserves a time slot and creates the scheduling
    entry in the system. Should be called after availability check.
    """
    try:
        # Mock implementation for now
        # In real implementation, this would:
        # 1. Verify the slot is still available
        # 2. Create the time slot reservation
        # 3. Update resource capacity
        # 4. Send notifications
        
        return BookingSlotResponse(
            success=True,
            slot_id=f"slot-{request.booking_id}",
            confirmed_time=request.start_time,
            resource_id=request.resource_id,
            message="Time slot successfully booked"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/book-slot/{slot_id}")
async def cancel_time_slot(
    slot_id: str,
    # TODO: Add proper authentication when available
    # current_user = Depends(get_current_user),
):
    """
    Cancel a booked time slot.
    
    This endpoint releases a previously booked time slot and
    makes the resource available again.
    """
    try:
        # Mock implementation for now
        return {"message": f"Time slot {slot_id} cancelled successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )