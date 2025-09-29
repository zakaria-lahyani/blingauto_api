"""
Booking API router
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import (
    get_current_user, get_current_active_user, require_manager_or_admin, require_staff
)
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.bookings.application.services.booking_service import BookingApplicationService
from src.features.bookings.infrastructure.database.repositories import BookingRepository, BookingEventRepository
from src.features.services.infrastructure.database.repositories import ServiceRepository
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository
from src.features.bookings.domain.enums import BookingStatus, BookingType, QualityRating
from .schemas import (
    CreateBookingRequest, UpdateBookingRequest, RescheduleBookingRequest,
    CancelBookingRequest, QualityRatingRequest, AddServiceRequest,
    BookingResponse, BookingListResponse, CancellationInfoResponse,
    BookingAnalyticsResponse, BookingFilters, SuccessResponse, ErrorResponse,
    VehicleInfoSchema, BookingServiceSchema, CreateBookingWithCapacityRequest
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])



def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingApplicationService:
    """Dependency to get booking service"""
    booking_repo = BookingRepository(db)
    event_repo = BookingEventRepository(db)
    service_repo = ServiceRepository(db)
    return BookingApplicationService(booking_repo, event_repo, service_repo)


def get_enhanced_booking_service(db: AsyncSession = Depends(get_db)) -> BookingApplicationService:
    """Simplified booking service (enhanced features temporarily disabled)"""
    booking_repo = BookingRepository(db)
    event_repo = BookingEventRepository(db)
    service_repo = ServiceRepository(db)
    return BookingApplicationService(booking_repo, event_repo, service_repo)


def get_vehicle_repository(db: AsyncSession = Depends(get_db)) -> VehicleRepository:
    """Dependency to get vehicle repository"""
    return VehicleRepository(db)


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: CreateBookingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    enhanced_service: BookingApplicationService = Depends(get_enhanced_booking_service),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repository)
):
    """Create a new booking with booking type validation"""
    try:
        # Convert string booking_type to enum
        booking_type_enum = BookingType.IN_HOME if request.booking_type == "in_home" else BookingType.MOBILE
        
        booking, warnings = await enhanced_service.create_booking_with_validation(
            customer_id=current_user.id,
            vehicle_id=request.vehicle_id,
            scheduled_at=request.scheduled_at,
            service_ids=request.service_ids,
            notes=request.notes,
            booking_type=booking_type_enum,
            vehicle_size=request.vehicle_size,
            customer_location=request.customer_location,
            auto_assign_resource=True
        )
        
        return await _booking_to_response(booking, vehicle_repo)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}"
        )


@router.get("/", response_model=BookingListResponse)
async def list_bookings(
    filters: BookingFilters = Depends(),
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """List bookings with filtering and pagination"""
    try:
        # Non-admin users can only see their own bookings
        customer_id = filters.customer_id
        if current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER]:
            customer_id = current_user.id
        
        # Build date range if individual dates provided
        date_range = None
        if filters.start_date and filters.end_date:
            date_range = (filters.start_date, filters.end_date)
        
        bookings, total = await booking_service.list_bookings(
            customer_id=customer_id,
            vehicle_id=filters.vehicle_id,
            status=filters.status,
            scheduled_date=filters.scheduled_date,
            date_range=date_range,
            search=filters.search,
            sort_by=filters.sort_by,
            sort_desc=filters.sort_desc,
            page=filters.page,
            page_size=filters.size
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        booking_responses = [await _booking_to_response(booking, vehicle_repo) for booking in bookings]
        
        return BookingListResponse(
            bookings=booking_responses,
            total=total,
            page=filters.page,
            size=filters.size,
            has_next=(filters.page * filters.size) < total,
            has_prev=filters.page > 1
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings"
        )


@router.get("/my", response_model=List[BookingResponse])
async def get_my_bookings(
    status_filter: Optional[List[BookingStatus]] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Get current user's recent bookings"""
    try:
        bookings = await booking_service.get_customer_bookings(
            customer_id=current_user.id,
            status_filter=status_filter,
            limit=limit
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return [await _booking_to_response(booking, vehicle_repo) for booking in bookings]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings"
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Get a specific booking"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if (current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER] and 
            booking.customer_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(booking, vehicle_repo)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking"
        )


@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: UUID,
    request: UpdateBookingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Update a booking (only notes for now)"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if not booking.can_be_modified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking cannot be modified in current status"
            )
        
        # Update notes
        booking.notes = request.notes
        booking.updated_at = datetime.utcnow()
        
        updated_booking = await booking_service.booking_repo.update(booking)
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(updated_booking, vehicle_repo)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update booking"
        )


@router.patch("/{booking_id}/confirm", response_model=BookingResponse)
async def confirm_booking(
    booking_id: UUID,
    current_user: AuthUser = Depends(require_manager_or_admin),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Confirm a pending booking (admin/manager only)"""
    try:
        booking = await booking_service.confirm_booking(booking_id)
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(booking, vehicle_repo)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm booking"
        )


@router.patch("/{booking_id}/start", response_model=BookingResponse)
async def start_service(
    booking_id: UUID,
    current_user: AuthUser = Depends(require_manager_or_admin),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Start the service (staff only)"""
    try:
        booking = await booking_service.start_service(booking_id)
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(booking, vehicle_repo)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start service"
        )


@router.patch("/{booking_id}/complete", response_model=BookingResponse)
async def complete_service(
    booking_id: UUID,
    actual_end_time: Optional[datetime] = None,
    current_user: AuthUser = Depends(require_manager_or_admin),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Complete the service (staff only)"""
    try:
        booking = await booking_service.complete_service(booking_id, actual_end_time)
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(booking, vehicle_repo)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete service"
        )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    request: CancelBookingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Cancel a booking"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if (current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER] and 
            booking.customer_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        cancelled_booking = await booking_service.cancel_booking(
            booking_id=booking_id,
            reason=request.reason
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(cancelled_booking, vehicle_repo)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking"
        )


@router.post("/{booking_id}/reschedule", response_model=BookingResponse)
async def reschedule_booking(
    booking_id: UUID,
    request: RescheduleBookingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Reschedule a booking"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if (current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER] and 
            booking.customer_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        rescheduled_booking = await booking_service.reschedule_booking(
            booking_id=booking_id,
            new_scheduled_at=request.new_scheduled_at
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(rescheduled_booking, vehicle_repo)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reschedule booking"
        )


@router.post("/{booking_id}/rate", response_model=BookingResponse)
async def rate_service_quality(
    booking_id: UUID,
    request: QualityRatingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Rate service quality"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the customer can rate the service"
            )
        
        rating = QualityRating(request.rating)
        rated_booking = await booking_service.rate_service_quality(
            booking_id=booking_id,
            rating=rating,
            feedback=request.feedback
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(rated_booking, vehicle_repo)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rate service"
        )


@router.post("/{booking_id}/services", response_model=BookingResponse)
async def add_service_to_booking(
    booking_id: UUID,
    request: AddServiceRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Add a service to an existing booking"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        updated_booking = await booking_service.add_service_to_booking(
            booking_id=booking_id,
            service_id=request.service_id
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(updated_booking, vehicle_repo)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add service"
        )


@router.delete("/{booking_id}/services/{service_id}", response_model=BookingResponse)
async def remove_service_from_booking(
    booking_id: UUID,
    service_id: UUID,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Remove a service from an existing booking"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        updated_booking = await booking_service.remove_service_from_booking(
            booking_id=booking_id,
            service_id=service_id
        )
        
        vehicle_repo = VehicleRepository(booking_service.booking_repo.db_session)
        return await _booking_to_response(updated_booking, vehicle_repo)
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove service"
        )


@router.get("/{booking_id}/cancellation-info", response_model=CancellationInfoResponse)
async def get_cancellation_info(
    booking_id: UUID,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Get cancellation policy and fee information"""
    try:
        booking = await booking_service.get_booking(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check access permissions
        if (current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER] and 
            booking.customer_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        info = await booking_service.calculate_cancellation_info(booking_id)
        
        # Determine if booking can be cancelled
        can_cancel = booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
        
        # Create descriptive message
        if not can_cancel:
            message = f"Cannot cancel booking with status: {booking.status.value}"
        elif info["notice_hours"] > 24:
            message = "Free cancellation available"
        elif info["notice_hours"] > 6:
            message = f"25% cancellation fee applies (${info['fee']})"
        elif info["notice_hours"] > 2:
            message = f"50% cancellation fee applies (${info['fee']})"
        else:
            message = f"100% cancellation fee applies (${info['fee']})"
        
        return CancellationInfoResponse(
            policy=info["policy"],
            fee=info["fee"],
            notice_hours=info["notice_hours"],
            total_price=info["total_price"],
            can_cancel=can_cancel,
            message=message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cancellation info"
        )


@router.get("/analytics/summary", response_model=BookingAnalyticsResponse)
async def get_booking_analytics(
    customer_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingApplicationService = Depends(get_booking_service)
):
    """Get booking analytics and metrics"""
    try:
        # Non-admin users can only see their own analytics
        if current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER]:
            customer_id = current_user.id
        
        date_range = None
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        analytics = await booking_service.get_booking_analytics(
            customer_id=customer_id,
            date_range=date_range
        )
        
        return BookingAnalyticsResponse(**analytics)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics"
        )


async def _booking_to_response(booking, vehicle_repo: VehicleRepository) -> BookingResponse:
    """Convert booking entity to response schema"""
    now = datetime.utcnow()
    
    # Fetch vehicle information
    vehicle = await vehicle_repo.get_by_id(booking.vehicle_id)
    vehicle_info = None
    if vehicle:
        vehicle_info = VehicleInfoSchema(
            id=vehicle.id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            license_plate=vehicle.license_plate,
            is_default=vehicle.is_default,
            display_name=f"{vehicle.year} {vehicle.make} {vehicle.model}"
        )
    
    return BookingResponse(
        id=booking.id,
        customer_id=booking.customer_id,
        vehicle_id=booking.vehicle_id,
        vehicle=vehicle_info,
        scheduled_at=booking.scheduled_at,
        booking_type=booking.booking_type.value,
        vehicle_size=booking.vehicle_size,
        customer_location=booking.customer_location,
        status=booking.status,
        notes=booking.notes,
        total_price=booking.total_price,
        total_duration=booking.total_duration,
        cancellation_fee=booking.cancellation_fee,
        quality_rating=booking.quality_rating.value if booking.quality_rating else None,
        quality_feedback=booking.quality_feedback,
        actual_start_time=booking.actual_start_time,
        actual_end_time=booking.actual_end_time,
        services=[
            BookingServiceSchema(
                id=service.id,
                service_id=service.service_id,
                service_name=service.service_name,
                price=service.price,
                duration=service.duration
            )
            for service in booking.services
        ],
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        can_be_modified=booking.can_be_modified,
        can_be_cancelled=booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED],
        can_be_rescheduled=booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED],
        can_be_rated=booking.can_be_rated,
        is_overdue=booking.scheduled_at < now and booking.status == BookingStatus.CONFIRMED,
        expected_end_time=booking.get_expected_end_time()
    )


# ============= ENHANCED SCHEDULING ENDPOINTS =============

@router.post("/create-with-validation", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_booking_with_validation(
    request: CreateBookingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    enhanced_service: BookingApplicationService = Depends(get_enhanced_booking_service),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repository)
):
    """Create a booking with full scheduling validation and conflict detection"""
    try:
        booking, warnings = await enhanced_service.create_booking_with_validation(
            customer_id=current_user.id,
            vehicle_id=request.vehicle_id,
            scheduled_at=request.scheduled_at,
            service_ids=request.service_ids,
            notes=request.notes,
            auto_assign_resource=True
        )
        
        booking_response = await _booking_to_response(booking, vehicle_repo)
        
        return {
            "booking": booking_response,
            "warnings": warnings,
            "has_warnings": len(warnings) > 0,
            "message": "Booking created successfully" + (f" with {len(warnings)} warnings" if warnings else "")
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking with validation"
        )


@router.post("/create-with-capacity", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_booking_with_capacity(
    request: CreateBookingWithCapacityRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    enhanced_service: BookingApplicationService = Depends(get_enhanced_booking_service),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repository)
):
    """Create a booking with capacity-based scheduling and validation (DEPRECATED - use main endpoint)"""
    
    try:
        # Convert string booking_type to enum
        booking_type_enum = BookingType.IN_HOME if request.wash_type == "stationary" else BookingType.MOBILE
        
        booking, warnings = await enhanced_service.create_booking_with_validation(
            customer_id=current_user.id,
            vehicle_id=request.vehicle_id,
            scheduled_at=request.scheduled_at,
            service_ids=request.service_ids,
            notes=request.notes,
            auto_assign_resource=True,
            booking_type=booking_type_enum,
            vehicle_size=request.vehicle_size,
            customer_location=request.customer_location
        )
        
        booking_response = await _booking_to_response(booking, vehicle_repo)
        
        return {
            "booking": booking_response,
            "warnings": warnings,
            "has_warnings": len(warnings) > 0,
            "booking_type": booking_type_enum.value,
            "vehicle_size": request.vehicle_size,
            "customer_location": request.customer_location,
            "message": f"Booking created successfully for {booking_type_enum.value} service" + (f" with {len(warnings)} warnings" if warnings else "")
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking with capacity management"
        )


@router.get("/available-times/{date}", response_model=dict)
async def get_available_times_for_date(
    date: str,  # Format: YYYY-MM-DD
    service_ids: List[UUID] = Query(...),
    current_user: AuthUser = Depends(get_current_active_user),
    enhanced_service: BookingApplicationService = Depends(get_enhanced_booking_service)
):
    """Get all available times for a specific date"""
    try:
        # Parse date
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        available_times = await enhanced_service.get_available_times_for_date(
            date=parsed_date,
            service_ids=service_ids,
            customer_id=current_user.id
        )
        
        return {
            "date": date,
            "available_times": [time.isoformat() for time in available_times],
            "total_slots": len(available_times),
            "service_ids": service_ids
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get available times"
        )


@router.post("/suggest-alternatives", response_model=dict)
async def suggest_alternative_times(
    request: dict,  # {"preferred_time": "2024-01-15T14:30:00", "service_ids": [...], "days_to_search": 7}
    current_user: AuthUser = Depends(get_current_active_user),
    enhanced_service: BookingApplicationService = Depends(get_enhanced_booking_service)
):
    """Get suggested alternative times when preferred time is not available"""
    try:
        preferred_time = datetime.fromisoformat(request["preferred_time"])
        service_ids = request["service_ids"]
        days_to_search = request.get("days_to_search", 7)
        
        alternatives = await enhanced_service.suggest_alternative_times(
            customer_id=current_user.id,
            preferred_time=preferred_time,
            service_ids=service_ids,
            days_to_search=days_to_search
        )
        
        return {
            "preferred_time": request["preferred_time"],
            "alternatives": [time.isoformat() for time in alternatives],
            "total_alternatives": len(alternatives),
            "search_period_days": days_to_search
        }
        
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {e}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest alternative times"
        )


@router.put("/{booking_id}/reschedule-with-validation", response_model=dict)
async def reschedule_booking_with_validation(
    booking_id: UUID,
    request: RescheduleBookingRequest,
    current_user: AuthUser = Depends(get_current_active_user),
    enhanced_service: BookingApplicationService = Depends(get_enhanced_booking_service),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repository)
):
    """Reschedule a booking with full scheduling validation"""
    try:
        booking, warnings = await enhanced_service.reschedule_booking_with_validation(
            booking_id=booking_id,
            new_scheduled_at=request.new_scheduled_at,
            customer_id=current_user.id
        )
        
        booking_response = await _booking_to_response(booking, vehicle_repo)
        
        return {
            "booking": booking_response,
            "warnings": warnings,
            "has_warnings": len(warnings) > 0,
            "message": "Booking rescheduled successfully" + (f" with {len(warnings)} warnings" if warnings else ""),
            "old_time": request.new_scheduled_at.isoformat(),  # This should be the old time in real implementation
            "new_time": booking.scheduled_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reschedule booking with validation"
        )