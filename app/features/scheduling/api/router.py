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
    use_case: GetAvailableSlotsUseCase = Depends(get_available_slots_use_case),
):
    """
    Get all available time slots for the specified criteria.

    Returns available slots within the date range that meet the
    vehicle size and service type requirements.
    """
    try:
        use_case_request = UseCaseGetSlotsRequest(
            start_date=request.start_date,
            end_date=request.end_date,
            service_type=request.service_type,
            vehicle_size=request.vehicle_size,
            duration_minutes=request.duration_minutes
        )

        result = await use_case.execute(use_case_request)

        return GetSlotsResponse(
            slots=result["slots"],
            total_count=result["total_count"],
            search_criteria={
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "service_type": request.service_type.value,
                "duration_minutes": request.duration_minutes,
                "vehicle_size": request.vehicle_size.value
            }
        )

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


@router.get("/resources", response_model=ResourceListResponse)
async def list_resources(
    use_case: ListResourcesUseCase = Depends(get_list_resources_use_case),
):
    """
    List all available scheduling resources (wash bays and mobile teams).

    Returns information about available wash bays and mobile teams
    including their capabilities and current utilization.
    """
    try:
        request = ListResourcesRequest()
        result = await use_case.execute(request)

        return ResourceListResponse(
            wash_bays=result["wash_bays"],
            mobile_teams=result["mobile_teams"],
            total_wash_bays=result["total_wash_bays"],
            total_mobile_teams=result["total_mobile_teams"]
        )

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


@router.post("/book-slot", response_model=BookingSlotResponse)
async def book_time_slot(
    request: BookingSlotRequest,
    current_user: CurrentUser,
    use_case: BookSlotUseCase = Depends(get_book_slot_use_case),
):
    """
    Book a specific time slot for a customer.

    This endpoint reserves a time slot and creates the scheduling
    entry in the system. Should be called after availability check.
    """
    try:
        result = await use_case.execute(
            booking_id=request.booking_id,
            resource_id=request.resource_id,
            start_time=request.start_time,
            duration_minutes=request.duration_minutes
        )

        return BookingSlotResponse(
            success=result["success"],
            slot_id=result["slot_id"],
            confirmed_time=result["confirmed_time"],
            resource_id=result["resource_id"],
            message=result.get("message", "Time slot successfully booked")
        )

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


@router.delete("/book-slot/{slot_id}")
async def cancel_time_slot(
    slot_id: str,
    current_user: CurrentUser,
    use_case: CancelSlotUseCase = Depends(get_cancel_slot_use_case),
):
    """
    Cancel a booked time slot.

    This endpoint releases a previously booked time slot and
    makes the resource available again.
    """
    try:
        result = await use_case.execute(slot_id=slot_id)
        return {"message": result.get("message", f"Time slot {slot_id} cancelled successfully")}

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