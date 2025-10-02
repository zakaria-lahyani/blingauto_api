from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.core.errors import NotFoundError, ValidationError, BusinessRuleViolationError
from app.shared.auth import get_current_user, require_any_role, CurrentUser

from app.features.bookings.api.schemas import (
    CreateBookingSchema,
    UpdateBookingSchema,
    CancelBookingSchema,
    BookingResponseSchema,
    BookingListResponseSchema,
    CreateBookingResponseSchema,
    CancelBookingResponseSchema,
    UpdateBookingResponseSchema,
    # New schemas
    ConfirmBookingSchema,
    ConfirmBookingResponseSchema,
    StartBookingSchema,
    StartBookingResponseSchema,
    CompleteBookingSchema,
    CompleteBookingResponseSchema,
    RescheduleBookingSchema,
    RescheduleBookingResponseSchema,
    AddServicesSchema,
    AddServicesResponseSchema,
    RemoveServiceResponseSchema,
    MarkNoShowSchema,
    MarkNoShowResponseSchema,
    RateBookingSchema,
    RateBookingResponseSchema,
)
from app.features.bookings.api.dependencies import (
    get_create_booking_use_case,
    get_cancel_booking_use_case,
    get_get_booking_use_case,
    get_list_bookings_use_case,
    get_update_booking_use_case,
    # New dependencies
    get_confirm_booking_use_case,
    get_start_booking_use_case,
    get_complete_booking_use_case,
    get_reschedule_booking_use_case,
    get_add_service_to_booking_use_case,
    get_remove_service_from_booking_use_case,
    get_mark_no_show_use_case,
    get_rate_booking_use_case,
)
from app.features.bookings.use_cases import (
    CreateBookingUseCase,
    CreateBookingRequest,
    CancelBookingUseCase,
    CancelBookingRequest,
    GetBookingUseCase,
    GetBookingRequest,
    ListBookingsUseCase,
    ListBookingsRequest,
    UpdateBookingUseCase,
    UpdateBookingRequest,
    # New use cases
    ConfirmBookingUseCase,
    ConfirmBookingRequest,
    StartBookingUseCase,
    StartBookingRequest,
    CompleteBookingUseCase,
    CompleteBookingRequest,
    RescheduleBookingUseCase,
    RescheduleBookingRequest,
    AddServiceToBookingUseCase,
    AddServiceToBookingRequest,
    RemoveServiceFromBookingUseCase,
    RemoveServiceFromBookingRequest,
    MarkNoShowUseCase,
    MarkNoShowRequest,
    RateBookingUseCase,
    RateBookingRequest,
)


router = APIRouter()


@router.post(
    "",
    response_model=CreateBookingResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="Create a new booking with specified services and schedule.",
)
async def create_booking(
    booking_data: CreateBookingSchema,
    current_user: CurrentUser,
    create_use_case: Annotated[CreateBookingUseCase, Depends(get_create_booking_use_case)],
):
    """Create a new booking."""
    try:
        # Validate customer can create booking for themselves or admin
        if booking_data.customer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create bookings for yourself"
            )
        
        request = CreateBookingRequest(
            customer_id=booking_data.customer_id,
            vehicle_id=booking_data.vehicle_id,
            service_ids=booking_data.service_ids,
            scheduled_at=booking_data.scheduled_at,
            booking_type=booking_data.booking_type,
            notes=booking_data.notes,
            phone_number=booking_data.phone_number,
        )
        
        response = await create_use_case.execute(request)
        return CreateBookingResponseSchema(**response.__dict__)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{booking_id}",
    response_model=BookingResponseSchema,
    summary="Get booking details",
    description="Retrieve detailed information about a specific booking.",
)
async def get_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    current_user: CurrentUser,
    get_use_case: Annotated[GetBookingUseCase, Depends(get_get_booking_use_case)],
):
    """Get booking by ID."""
    try:
        request = GetBookingRequest(
            booking_id=booking_id,
            requested_by=current_user.id,
            is_admin=current_user.is_admin,
        )
        
        response = await get_use_case.execute(request)
        return BookingResponseSchema(**response.__dict__)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "",
    response_model=BookingListResponseSchema,
    summary="List bookings",
    description="List bookings with optional filtering and pagination.",
)
async def list_bookings(
    current_user: CurrentUser,
    list_use_case: Annotated[ListBookingsUseCase, Depends(get_list_bookings_use_case)],
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by booking status"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List bookings with filtering and pagination."""
    try:
        # If not admin, can only see own bookings
        if not current_user.is_admin:
            if customer_id and customer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own bookings"
                )
            customer_id = current_user.id
        
        request = ListBookingsRequest(
            customer_id=customer_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )
        
        response = await list_use_case.execute(request)
        return BookingListResponseSchema(**response.__dict__)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{booking_id}",
    response_model=UpdateBookingResponseSchema,
    summary="Update booking",
    description="Update an existing booking's details.",
)
async def update_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    booking_data: UpdateBookingSchema,
    current_user: CurrentUser,
    update_use_case: Annotated[UpdateBookingUseCase, Depends(get_update_booking_use_case)],
):
    """Update an existing booking."""
    try:
        request = UpdateBookingRequest(
            booking_id=booking_id,
            updated_by=current_user.id,
            is_admin=current_user.is_admin,
            scheduled_at=booking_data.scheduled_at,
            service_ids=booking_data.service_ids,
            notes=booking_data.notes,
            phone_number=booking_data.phone_number,
        )
        
        response = await update_use_case.execute(request)
        return UpdateBookingResponseSchema(**response.__dict__)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/cancel",
    response_model=CancelBookingResponseSchema,
    summary="Cancel booking",
    description="Cancel an existing booking with optional reason.",
)
async def cancel_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    cancel_data: CancelBookingSchema,
    current_user: CurrentUser,
    cancel_use_case: Annotated[CancelBookingUseCase, Depends(get_cancel_booking_use_case)],
):
    """Cancel an existing booking."""
    try:
        request = CancelBookingRequest(
            booking_id=booking_id,
            cancelled_by=current_user.id,
            reason=cancel_data.reason,
        )
        
        response = await cancel_use_case.execute(request)
        return CancelBookingResponseSchema(**response.__dict__)
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Admin-only endpoints
@router.get(
    "/admin/stats",
    dependencies=[Depends(require_any_role("admin"))],
    summary="Get booking statistics",
    description="Get booking statistics for administrators.",
)
async def get_booking_stats(
    current_user: CurrentUser,
    start_date: Optional[datetime] = Query(None, description="Stats from date"),
    end_date: Optional[datetime] = Query(None, description="Stats to date"),
):
    """Get booking statistics for admins."""
    # TODO: Implement booking statistics logic
    return {
        "total_bookings": 0,
        "pending_bookings": 0,
        "confirmed_bookings": 0,
        "cancelled_bookings": 0,
        "total_revenue": 0.0,
    }


@router.post(
    "/{booking_id}/confirm",
    response_model=ConfirmBookingResponseSchema,
    dependencies=[Depends(require_any_role("admin", "manager", "washer"))],
    status_code=status.HTTP_200_OK,
    summary="Confirm booking",
    description="Confirm a pending booking. Only staff members can confirm bookings.",
)
async def confirm_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    booking_data: ConfirmBookingSchema,
    current_user: CurrentUser,
    use_case: Annotated[ConfirmBookingUseCase, Depends(get_confirm_booking_use_case)],
):
    """Confirm a booking (staff only - admin/manager/washer)."""
    try:
        request = ConfirmBookingRequest(
            booking_id=booking_id,
            confirmed_by=current_user.id,
            notes=booking_data.notes,
        )
        response = await use_case.execute(request)
        return ConfirmBookingResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/start",
    response_model=StartBookingResponseSchema,
    dependencies=[Depends(require_any_role("admin", "manager", "washer"))],
    status_code=status.HTTP_200_OK,
    summary="Start booking",
    description="Start a confirmed booking. Marks the booking as in progress.",
)
async def start_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    current_user: CurrentUser,
    use_case: Annotated[StartBookingUseCase, Depends(get_start_booking_use_case)],
):
    """Start a booking service (staff only)."""
    try:
        request = StartBookingRequest(
            booking_id=booking_id,
            started_by=current_user.id,
        )
        response = await use_case.execute(request)
        return StartBookingResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/complete",
    response_model=CompleteBookingResponseSchema,
    dependencies=[Depends(require_any_role("admin", "manager", "washer"))],
    status_code=status.HTTP_200_OK,
    summary="Complete booking",
    description="Mark an in-progress booking as completed. Calculates overtime fees if applicable.",
)
async def complete_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    booking_data: CompleteBookingSchema,
    current_user: CurrentUser,
    use_case: Annotated[CompleteBookingUseCase, Depends(get_complete_booking_use_case)],
):
    """Mark a booking as completed (staff only)."""
    try:
        request = CompleteBookingRequest(
            booking_id=booking_id,
            completed_by=current_user.id,
            actual_end_time=booking_data.actual_end_time,
        )
        response = await use_case.execute(request)
        return CompleteBookingResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/reschedule",
    response_model=RescheduleBookingResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Reschedule booking",
    description="Reschedule a booking to a new time. Requires minimum 2 hours notice.",
)
async def reschedule_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    booking_data: RescheduleBookingSchema,
    current_user: CurrentUser,
    use_case: Annotated[RescheduleBookingUseCase, Depends(get_reschedule_booking_use_case)],
):
    """Reschedule a booking to a new time."""
    try:
        request = RescheduleBookingRequest(
            booking_id=booking_id,
            new_scheduled_at=booking_data.new_scheduled_at,
            rescheduled_by=current_user.id,
            reason=booking_data.reason,
        )
        response = await use_case.execute(request)
        return RescheduleBookingResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/services",
    response_model=AddServicesResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Add services to booking",
    description="Add additional services to a pending booking. Maximum 10 services total.",
)
async def add_services_to_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    services_data: AddServicesSchema,
    current_user: CurrentUser,
    use_case: Annotated[AddServiceToBookingUseCase, Depends(get_add_service_to_booking_use_case)],
):
    """Add services to a pending booking."""
    try:
        request = AddServiceToBookingRequest(
            booking_id=booking_id,
            service_ids=services_data.service_ids,
            added_by=current_user.id,
        )
        response = await use_case.execute(request)
        return AddServicesResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete(
    "/{booking_id}/services/{service_id}",
    response_model=RemoveServiceResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Remove service from booking",
    description="Remove a service from a pending booking. Minimum 1 service must remain.",
)
async def remove_service_from_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    service_id: Annotated[str, Path(..., description="Service ID to remove")],
    current_user: CurrentUser,
    use_case: Annotated[RemoveServiceFromBookingUseCase, Depends(get_remove_service_from_booking_use_case)],
):
    """Remove a service from a pending booking."""
    try:
        request = RemoveServiceFromBookingRequest(
            booking_id=booking_id,
            service_ids=[service_id],
            removed_by=current_user.id,
        )
        response = await use_case.execute(request)
        return RemoveServiceResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/no-show",
    response_model=MarkNoShowResponseSchema,
    dependencies=[Depends(require_any_role("admin", "manager", "washer"))],
    status_code=status.HTTP_200_OK,
    summary="Mark booking as no-show",
    description="Mark a confirmed booking as no-show after grace period. Charges 100% fee.",
)
async def mark_booking_no_show(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    no_show_data: MarkNoShowSchema,
    current_user: CurrentUser,
    use_case: Annotated[MarkNoShowUseCase, Depends(get_mark_no_show_use_case)],
):
    """Mark a booking as no-show (staff only)."""
    try:
        request = MarkNoShowRequest(
            booking_id=booking_id,
            marked_by=current_user.id,
            reason=no_show_data.reason,
        )
        response = await use_case.execute(request)
        return MarkNoShowResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/{booking_id}/rate",
    response_model=RateBookingResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Rate booking",
    description="Rate a completed booking (1-5 stars). Can only be done once per booking.",
)
async def rate_booking(
    booking_id: Annotated[str, Path(..., description="Booking ID")],
    rating_data: RateBookingSchema,
    current_user: CurrentUser,
    use_case: Annotated[RateBookingUseCase, Depends(get_rate_booking_use_case)],
):
    """Rate a completed booking (customer only)."""
    try:
        request = RateBookingRequest(
            booking_id=booking_id,
            customer_id=current_user.id,
            rating=rating_data.rating,
            feedback=rating_data.feedback,
        )
        response = await use_case.execute(request)
        return RateBookingResponseSchema(**response.__dict__)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
# Alias for backward compatibility
booking_router = router
