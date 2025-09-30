"""
Enhanced Booking Router
Handles booking confirmation with automatic schedule updates and smart features.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import get_current_active_user
from src.features.auth.domain.entities import AuthUser
from src.features.bookings.application.services.booking_service import BookingService
from src.features.bookings.infrastructure.database.repositories import BookingRepository
from src.features.scheduling.application.services.scheduling_service import SchedulingService
from src.features.scheduling.application.services.smart_booking_service import SmartBookingService
from src.features.scheduling.infrastructure.database.repositories import (
    BusinessHoursRepository, ResourceRepository, TimeSlotRepository, 
    SchedulingConflictRepository
)
from src.features.scheduling.infrastructure.database.wash_facility_repositories import CapacityAllocationRepository
from src.features.services.infrastructure.database.repositories import ServiceRepository
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository
from src.features.bookings.domain.entities import Booking
from src.features.bookings.domain.enums import BookingStatus, BookingType

router = APIRouter(prefix="/bookings", tags=["Enhanced Bookings"])


def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Dependency to get booking service"""
    booking_repo = BookingRepository(db)
    # Add other required repositories
    return BookingService(booking_repo=booking_repo)


def get_smart_booking_service(db: AsyncSession = Depends(get_db)) -> SmartBookingService:
    """Dependency to get smart booking service"""
    business_hours_repo = BusinessHoursRepository(db)
    resource_repo = ResourceRepository(db)
    time_slot_repo = TimeSlotRepository(db)
    conflict_repo = SchedulingConflictRepository(db)
    service_repo = ServiceRepository(db)
    capacity_repo = CapacityAllocationRepository(db)
    vehicle_repo = VehicleRepository(db)
    booking_repo = BookingRepository(db)
    
    scheduling_service = SchedulingService(
        business_hours_repo=business_hours_repo,
        resource_repo=resource_repo,
        time_slot_repo=time_slot_repo,
        conflict_repo=conflict_repo,
        service_repo=service_repo
    )
    
    return SmartBookingService(
        scheduling_service=scheduling_service,
        capacity_repo=capacity_repo,
        vehicle_repo=vehicle_repo,
        booking_repo=booking_repo,
        service_repo=service_repo
    )


# ================= ENHANCED BOOKING CREATION =================

@router.post("/")
async def create_booking_with_schedule_update(
    booking_data: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingService = Depends(get_booking_service),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service),
    db: AsyncSession = Depends(get_db)
):
    """Create booking with automatic schedule updates and conflict checking"""
    try:
        # Extract booking parameters
        vehicle_id = UUID(booking_data["vehicle_id"])
        service_ids = [UUID(sid) for sid in booking_data["service_ids"]]
        scheduled_at = datetime.fromisoformat(booking_data["scheduled_at"])
        booking_type = BookingType(booking_data.get("booking_type", "stationary"))
        notes = booking_data.get("notes", "")
        customer_location = booking_data.get("customer_location")
        
        # Step 1: Pre-booking validation and conflict checking
        print(f"[BOOKING] Pre-validation for customer {current_user.id}")
        
        # Calculate total service duration
        total_duration = await smart_booking.calculate_total_service_duration(service_ids)
        service_type = await smart_booking.determine_service_type(service_ids)
        
        # Check availability with conflict detection
        availability_check = await smart_booking.check_availability_advanced(
            booking_datetime=scheduled_at,
            service_duration_minutes=total_duration,
            service_type=service_type,
            vehicle_size="standard",  # Could be determined from vehicle
            customer_id=current_user.id
        )
        
        if not availability_check["available"]:
            # Handle conflicts
            conflicts = availability_check.get("conflicts", [])
            alternatives = availability_check.get("alternative_slots", [])
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Requested time slot is not available",
                    "conflicts": conflicts,
                    "alternative_slots": alternatives[:5],  # Provide top 5 alternatives
                    "suggestion": "Please select an alternative time slot"
                }
            )
        
        # Step 2: Calculate pricing (with dynamic pricing if applicable)
        pricing_info = await smart_booking.calculate_booking_price(
            service_ids=service_ids,
            scheduled_at=scheduled_at,
            customer_id=current_user.id,
            vehicle_type="standard"  # Could be determined from vehicle
        )
        
        total_price = pricing_info["total_price"]
        pricing_factors = pricing_info.get("pricing_factors", [])
        
        # Step 3: Create the booking
        print(f"[BOOKING] Creating booking for {scheduled_at}")
        
        # Create booking entity
        booking = Booking(
            customer_id=current_user.id,
            vehicle_id=vehicle_id,
            scheduled_at=scheduled_at,
            services=[],  # Will be populated by service
            booking_type=booking_type,
            notes=notes,
            customer_location=customer_location,
            status=BookingStatus.CONFIRMED,  # Auto-confirm if availability check passed
            total_price=total_price,
            total_duration=total_duration
        )
        
        # Save booking
        created_booking = await booking_service.create_booking(
            booking=booking,
            service_ids=service_ids
        )
        
        print(f"[BOOKING] Created booking {created_booking.id}")
        
        # Step 4: Update schedule and capacity allocations
        print(f"[SCHEDULE] Updating schedule for booking {created_booking.id}")
        
        schedule_update_result = await smart_booking.update_schedule_for_booking(
            booking_id=created_booking.id,
            scheduled_at=scheduled_at,
            service_duration_minutes=total_duration,
            service_type=service_type
        )
        
        if not schedule_update_result["success"]:
            # Rollback booking if schedule update fails
            await booking_service.cancel_booking(created_booking.id, current_user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update schedule. Booking has been cancelled."
            )
        
        # Step 5: Update capacity allocations
        print(f"[CAPACITY] Updating capacity allocations")
        
        await smart_booking.update_capacity_allocation(
            date=scheduled_at.date(),
            booking_id=created_booking.id,
            service_type=service_type,
            allocated_bay_id=schedule_update_result.get("assigned_bay_id")
        )
        
        # Step 6: Generate upselling suggestions for response
        upselling_suggestions = await smart_booking.get_upselling_suggestions_for_booking(
            customer_id=current_user.id,
            vehicle_id=vehicle_id,
            selected_service_ids=service_ids
        )
        
        # Prepare response
        response = {
            "booking": {
                "id": created_booking.id,
                "customer_id": created_booking.customer_id,
                "vehicle_id": created_booking.vehicle_id,
                "scheduled_at": created_booking.scheduled_at.isoformat(),
                "status": created_booking.status.value,
                "booking_type": created_booking.booking_type.value,
                "total_price": float(created_booking.total_price),
                "total_duration": created_booking.total_duration,
                "notes": created_booking.notes,
                "created_at": created_booking.created_at.isoformat()
            },
            "schedule_info": {
                "assigned_bay_id": schedule_update_result.get("assigned_bay_id"),
                "assigned_bay_name": schedule_update_result.get("assigned_bay_name"),
                "time_slot_id": schedule_update_result.get("time_slot_id"),
                "buffer_time_minutes": schedule_update_result.get("buffer_time_minutes", 15)
            },
            "pricing_details": {
                "base_price": pricing_info.get("base_price"),
                "total_price": float(total_price),
                "pricing_factors": pricing_factors,
                "savings_applied": pricing_info.get("savings_applied", 0)
            },
            "upselling_opportunities": upselling_suggestions[:3],  # Top 3 suggestions
            "confirmation_details": {
                "confirmation_number": f"CW{created_booking.id.hex[:8].upper()}",
                "estimated_completion": (scheduled_at + timedelta(minutes=total_duration)).isoformat(),
                "arrival_instructions": "Please arrive 10 minutes before your scheduled time",
                "contact_phone": "+1-555-WASH-NOW"
            }
        }
        
        print(f"[BOOKING] Successfully created and scheduled booking {created_booking.id}")
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid booking data: {str(e)}"
        )
    except Exception as e:
        print(f"[ERROR] Booking creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}"
        )


# ================= BOOKING CONFIRMATION =================

@router.post("/{booking_id}/confirm")
async def confirm_booking(
    booking_id: UUID,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingService = Depends(get_booking_service),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Confirm a pending booking and update schedule"""
    try:
        # Get existing booking
        booking = await booking_service.get_booking_by_id(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check ownership
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Not your booking."
            )
        
        # Check if already confirmed
        if booking.status == BookingStatus.CONFIRMED:
            return {
                "success": True,
                "message": "Booking is already confirmed",
                "booking_id": booking_id
            }
        
        # Check if booking can be confirmed (not cancelled, completed, etc.)
        if booking.status not in [BookingStatus.PENDING, BookingStatus.TENTATIVE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking cannot be confirmed. Current status: {booking.status.value}"
            )
        
        print(f"[CONFIRM] Confirming booking {booking_id}")
        
        # Re-check availability at confirmation time
        service_type = await smart_booking.determine_service_type_from_booking(booking)
        availability_check = await smart_booking.check_availability_advanced(
            booking_datetime=booking.scheduled_at,
            service_duration_minutes=booking.total_duration,
            service_type=service_type,
            vehicle_size="standard",
            customer_id=current_user.id,
            exclude_booking_id=booking_id  # Exclude this booking from conflict check
        )
        
        if not availability_check["available"]:
            # Availability changed since booking creation
            alternatives = availability_check.get("alternative_slots", [])
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Time slot is no longer available",
                    "alternative_slots": alternatives[:5],
                    "action_required": "Please reschedule your booking"
                }
            )
        
        # Confirm the booking
        booking.status = BookingStatus.CONFIRMED
        confirmed_booking = await booking_service.update_booking(booking)
        
        # Update schedule and capacity if not already done
        if booking.status == BookingStatus.PENDING:
            print(f"[SCHEDULE] Updating schedule for confirmed booking {booking_id}")
            
            schedule_update_result = await smart_booking.update_schedule_for_booking(
                booking_id=booking_id,
                scheduled_at=booking.scheduled_at,
                service_duration_minutes=booking.total_duration,
                service_type=service_type
            )
            
            await smart_booking.update_capacity_allocation(
                date=booking.scheduled_at.date(),
                booking_id=booking_id,
                service_type=service_type,
                allocated_bay_id=schedule_update_result.get("assigned_bay_id")
            )
        
        # Send confirmation notifications (simulated)
        print(f"[NOTIFICATION] Sending confirmation for booking {booking_id}")
        
        response = {
            "success": True,
            "message": "Booking confirmed successfully",
            "booking_id": booking_id,
            "confirmation_number": f"CW{booking_id.hex[:8].upper()}",
            "scheduled_at": booking.scheduled_at.isoformat(),
            "estimated_completion": (booking.scheduled_at + timedelta(minutes=booking.total_duration)).isoformat(),
            "status": confirmed_booking.status.value,
            "preparation_instructions": [
                "Arrive 10 minutes before your scheduled time",
                "Remove personal items from your vehicle",
                "Ensure vehicle is unlocked for interior services"
            ],
            "contact_info": {
                "phone": "+1-555-WASH-NOW",
                "email": "support@blingauto.com"
            }
        }
        
        print(f"[CONFIRM] Successfully confirmed booking {booking_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Booking confirmation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm booking: {str(e)}"
        )


# ================= BOOKING MODIFICATION WITH SCHEDULE UPDATES =================

@router.put("/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: UUID,
    reschedule_data: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingService = Depends(get_booking_service),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Reschedule a booking and update schedule accordingly"""
    try:
        # Get existing booking
        booking = await booking_service.get_booking_by_id(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check ownership
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Not your booking."
            )
        
        # Parse new scheduled time
        new_scheduled_at = datetime.fromisoformat(reschedule_data["new_scheduled_at"])
        
        # Check if new time is different
        if new_scheduled_at == booking.scheduled_at:
            return {
                "success": True,
                "message": "No change in schedule",
                "booking_id": booking_id
            }
        
        print(f"[RESCHEDULE] Rescheduling booking {booking_id} from {booking.scheduled_at} to {new_scheduled_at}")
        
        # Step 1: Check availability for new time
        service_type = await smart_booking.determine_service_type_from_booking(booking)
        availability_check = await smart_booking.check_availability_advanced(
            booking_datetime=new_scheduled_at,
            service_duration_minutes=booking.total_duration,
            service_type=service_type,
            vehicle_size="standard",
            customer_id=current_user.id
        )
        
        if not availability_check["available"]:
            conflicts = availability_check.get("conflicts", [])
            alternatives = availability_check.get("alternative_slots", [])
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "New time slot is not available",
                    "conflicts": conflicts,
                    "alternative_slots": alternatives[:5],
                    "suggestion": "Please select a different time"
                }
            )
        
        # Step 2: Release old schedule slot
        print(f"[SCHEDULE] Releasing old schedule slot")
        
        await smart_booking.release_schedule_slot(
            booking_id=booking_id,
            scheduled_at=booking.scheduled_at,
            service_duration_minutes=booking.total_duration
        )
        
        # Step 3: Update booking with new time
        old_scheduled_at = booking.scheduled_at
        booking.scheduled_at = new_scheduled_at
        
        # Recalculate pricing if there's dynamic pricing
        pricing_info = await smart_booking.calculate_booking_price(
            service_ids=[service.service_id for service in booking.services],
            scheduled_at=new_scheduled_at,
            customer_id=current_user.id,
            vehicle_type="standard"
        )
        
        # Update price if significantly different
        price_difference = pricing_info["total_price"] - booking.total_price
        if abs(price_difference) > 0.01:  # More than 1 cent difference
            booking.total_price = pricing_info["total_price"]
        
        updated_booking = await booking_service.update_booking(booking)
        
        # Step 4: Reserve new schedule slot
        print(f"[SCHEDULE] Reserving new schedule slot")
        
        schedule_update_result = await smart_booking.update_schedule_for_booking(
            booking_id=booking_id,
            scheduled_at=new_scheduled_at,
            service_duration_minutes=booking.total_duration,
            service_type=service_type
        )
        
        # Step 5: Update capacity allocations
        print(f"[CAPACITY] Updating capacity allocations")
        
        # Release old capacity
        await smart_booking.release_capacity_allocation(
            date=old_scheduled_at.date(),
            booking_id=booking_id
        )
        
        # Allocate new capacity
        await smart_booking.update_capacity_allocation(
            date=new_scheduled_at.date(),
            booking_id=booking_id,
            service_type=service_type,
            allocated_bay_id=schedule_update_result.get("assigned_bay_id")
        )
        
        # Prepare response
        response = {
            "success": True,
            "message": "Booking rescheduled successfully",
            "booking_id": booking_id,
            "old_scheduled_at": old_scheduled_at.isoformat(),
            "new_scheduled_at": new_scheduled_at.isoformat(),
            "price_change": float(price_difference),
            "schedule_info": {
                "assigned_bay_id": schedule_update_result.get("assigned_bay_id"),
                "assigned_bay_name": schedule_update_result.get("assigned_bay_name"),
                "estimated_completion": (new_scheduled_at + timedelta(minutes=booking.total_duration)).isoformat()
            },
            "confirmation_number": f"CW{booking_id.hex[:8].upper()}",
            "update_reason": reschedule_data.get("reason", "Customer requested reschedule")
        }
        
        print(f"[RESCHEDULE] Successfully rescheduled booking {booking_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Booking reschedule failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule booking: {str(e)}"
        )


# ================= BOOKING CANCELLATION WITH SCHEDULE CLEANUP =================

@router.delete("/{booking_id}")
async def cancel_booking_with_schedule_cleanup(
    booking_id: UUID,
    cancellation_data: Optional[Dict[str, Any]] = None,
    current_user: AuthUser = Depends(get_current_active_user),
    booking_service: BookingService = Depends(get_booking_service),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Cancel booking and clean up schedule and capacity allocations"""
    try:
        # Get existing booking
        booking = await booking_service.get_booking_by_id(booking_id)
        
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )
        
        # Check ownership
        if booking.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Not your booking."
            )
        
        # Check if already cancelled
        if booking.status == BookingStatus.CANCELLED:
            return {
                "success": True,
                "message": "Booking is already cancelled",
                "booking_id": booking_id
            }
        
        print(f"[CANCEL] Cancelling booking {booking_id}")
        
        # Calculate cancellation fee based on timing
        hours_until_booking = (booking.scheduled_at - datetime.now()).total_seconds() / 3600
        cancellation_fee = 0.0
        
        if hours_until_booking < 2:  # Less than 2 hours notice
            cancellation_fee = float(booking.total_price) * 0.25  # 25% fee
        elif hours_until_booking < 24:  # Less than 24 hours notice
            cancellation_fee = float(booking.total_price) * 0.10  # 10% fee
        
        # Cancel the booking
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_fee = cancellation_fee
        cancelled_booking = await booking_service.update_booking(booking)
        
        # Step 1: Release schedule slot
        print(f"[SCHEDULE] Releasing schedule slot for cancelled booking")
        
        await smart_booking.release_schedule_slot(
            booking_id=booking_id,
            scheduled_at=booking.scheduled_at,
            service_duration_minutes=booking.total_duration
        )
        
        # Step 2: Release capacity allocation
        print(f"[CAPACITY] Releasing capacity allocation")
        
        await smart_booking.release_capacity_allocation(
            date=booking.scheduled_at.date(),
            booking_id=booking_id
        )
        
        # Step 3: Check for waitlist customers who can take this slot
        print(f"[WAITLIST] Checking waitlist for released slot")
        
        waitlist_notification = await smart_booking.notify_waitlist_for_available_slot(
            released_datetime=booking.scheduled_at,
            service_duration_minutes=booking.total_duration,
            service_type=await smart_booking.determine_service_type_from_booking(booking)
        )
        
        # Prepare response
        response = {
            "success": True,
            "message": "Booking cancelled successfully",
            "booking_id": booking_id,
            "cancellation_fee": cancellation_fee,
            "refund_amount": float(booking.total_price) - cancellation_fee,
            "cancellation_details": {
                "cancelled_at": datetime.now().isoformat(),
                "original_scheduled_at": booking.scheduled_at.isoformat(),
                "hours_notice": round(hours_until_booking, 1),
                "reason": cancellation_data.get("reason", "Customer requested cancellation") if cancellation_data else "Customer requested cancellation"
            },
            "refund_info": {
                "refund_method": "Original payment method",
                "estimated_processing_time": "3-5 business days",
                "refund_reference": f"REF{booking_id.hex[:8].upper()}"
            },
            "waitlist_notification": waitlist_notification.get("customers_notified", 0) if waitlist_notification else 0
        }
        
        print(f"[CANCEL] Successfully cancelled booking {booking_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Booking cancellation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel booking: {str(e)}"
        )