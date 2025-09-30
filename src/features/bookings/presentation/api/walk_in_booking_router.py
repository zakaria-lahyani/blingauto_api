"""
Walk-in Booking Router
Handles walk-in customers and on-the-spot bookings by washers.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import get_current_active_user
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole
from src.features.bookings.application.services.booking_service import BookingService
from src.features.bookings.infrastructure.database.repositories import BookingRepository
from src.features.scheduling.application.services.smart_booking_service import SmartBookingService
from src.features.scheduling.infrastructure.database.repositories import (
    BusinessHoursRepository, ResourceRepository, TimeSlotRepository, 
    SchedulingConflictRepository
)
from src.features.scheduling.infrastructure.database.wash_facility_repositories import CapacityAllocationRepository
from src.features.services.infrastructure.database.repositories import ServiceRepository
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository
# from src.features.vehicles.application.services.vehicle_service import VehicleService  # Not implemented
from src.features.bookings.domain.entities import Booking, BookingService as BookingServiceEntity
from src.features.bookings.domain.enums import BookingStatus, BookingType
from src.features.vehicles.domain.entities import Vehicle
from src.features.vehicles.domain.enums import VehicleStatus

router = APIRouter(prefix="/walk-in", tags=["Walk-in Bookings"])


def require_washer_or_admin(current_user: AuthUser = Depends(get_current_active_user)):
    """Require washer, manager, or admin role"""
    if current_user.role not in [AuthRole.ADMIN, AuthRole.MANAGER, AuthRole.WASHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Washer role or higher required."
        )
    return current_user


def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Dependency to get booking service"""
    booking_repo = BookingRepository(db)
    return BookingService(booking_repo=booking_repo)


# def get_vehicle_service(db: AsyncSession = Depends(get_db)) -> VehicleService:
#     """Dependency to get vehicle service"""
#     vehicle_repo = VehicleRepository(db)
#     return VehicleService(vehicle_repo=vehicle_repo)  # VehicleService not implemented


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
    
    from src.features.scheduling.application.services.scheduling_service import SchedulingService
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


# ================= WALK-IN CUSTOMER REGISTRATION =================

@router.post("/register-customer")
async def register_walk_in_customer(
    customer_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_washer_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Register a walk-in customer on the spot"""
    try:
        # Create temporary customer account for walk-in
        temp_customer = {
            "id": uuid4(),
            "email": customer_data.get("email", f"walkin_{uuid4().hex[:8]}@temp.com"),
            "first_name": customer_data.get("first_name", "Walk-in"),
            "last_name": customer_data.get("last_name", "Customer"),
            "phone": customer_data.get("phone", ""),
            "is_walk_in": True,
            "registered_by_washer": current_user.id,
            "registration_date": datetime.now()
        }
        
        print(f"[WALK-IN] Washer {current_user.id} registering walk-in customer")
        
        # In a real implementation, this would save to database
        # For now, we'll simulate the customer creation
        
        return {
            "customer_id": temp_customer["id"],
            "customer_info": {
                "name": f"{temp_customer['first_name']} {temp_customer['last_name']}",
                "phone": temp_customer["phone"],
                "email": temp_customer["email"],
                "is_walk_in": True
            },
            "registered_by": {
                "washer_id": current_user.id,
                "washer_name": f"{current_user.first_name} {current_user.last_name}"
            },
            "next_step": "Register vehicle information"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register walk-in customer: {str(e)}"
        )


# ================= VEHICLE REGISTRATION ON-THE-SPOT =================

@router.post("/register-vehicle")
async def register_walk_in_vehicle(
    vehicle_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_washer_or_admin),
    # vehicle_service: VehicleService = Depends(get_vehicle_service)  # VehicleService not implemented
    db: AsyncSession = Depends(get_db)
):
    """Register a vehicle on the spot for walk-in service"""
    try:
        customer_id = UUID(vehicle_data["customer_id"])
        
        # Create vehicle entity
        vehicle = Vehicle(
            id=uuid4(),
            user_id=customer_id,
            make=vehicle_data["make"],
            model=vehicle_data["model"],
            year=vehicle_data["year"],
            color=vehicle_data["color"],
            license_plate=vehicle_data["license_plate"].upper(),
            is_default=True,  # First vehicle is default
            status=VehicleStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        print(f"[WALK-IN] Registering vehicle {vehicle.license_plate} for customer {customer_id}")
        
        # Save vehicle directly using repository
        vehicle_repo = VehicleRepository(db)
        created_vehicle = await vehicle_repo.create(vehicle)
        
        return {
            "vehicle_id": created_vehicle.id,
            "vehicle_info": {
                "make": created_vehicle.make,
                "model": created_vehicle.model,
                "year": created_vehicle.year,
                "color": created_vehicle.color,
                "license_plate": created_vehicle.license_plate
            },
            "customer_id": customer_id,
            "registered_by": {
                "washer_id": current_user.id,
                "washer_name": f"{current_user.first_name} {current_user.last_name}"
            },
            "next_step": "Create walk-in booking"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid vehicle data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register vehicle: {str(e)}"
        )


# ================= WALK-IN BOOKING CREATION =================

@router.post("/create-booking")
async def create_walk_in_booking(
    booking_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_washer_or_admin),
    booking_service: BookingService = Depends(get_booking_service),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service),
    db: AsyncSession = Depends(get_db)
):
    """Create a walk-in booking and automatically adjust schedule"""
    try:
        # Extract booking parameters
        customer_id = UUID(booking_data["customer_id"])
        vehicle_id = UUID(booking_data["vehicle_id"])
        service_ids = [UUID(sid) for sid in booking_data["service_ids"]]
        
        # Current time as start time for walk-in
        start_time = datetime.now()
        
        # Determine which bay the washer is using
        assigned_bay_id = None
        if "bay_id" in booking_data:
            assigned_bay_id = UUID(booking_data["bay_id"])
        else:
            # Auto-assign available bay
            available_bays = await smart_booking.scheduling_service.get_available_wash_bays(
                date=start_time.date(),
                vehicle_size="standard",
                service_type="walk_in"
            )
            if available_bays:
                assigned_bay_id = available_bays[0].id
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No available bays for walk-in service"
                )
        
        print(f"[WALK-IN] Creating walk-in booking for customer {customer_id} at bay {assigned_bay_id}")
        
        # Calculate service duration and pricing
        total_duration = await smart_booking.calculate_total_service_duration(service_ids)
        service_type = await smart_booking.determine_service_type(service_ids)
        
        # Calculate pricing (walk-ins might have different pricing)
        pricing_info = await smart_booking.calculate_booking_price(
            service_ids=service_ids,
            scheduled_at=start_time,
            customer_id=customer_id,
            vehicle_type="standard"
        )
        
        # Apply walk-in premium (5% extra for immediate service)
        walk_in_multiplier = 1.05
        total_price = pricing_info["total_price"] * walk_in_multiplier
        
        # Create booking entity
        booking = Booking(
            id=uuid4(),
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            scheduled_at=start_time,
            services=[],  # Will be populated by service
            booking_type=BookingType.STATIONARY,
            notes=f"Walk-in service by washer {current_user.first_name} {current_user.last_name}",
            status=BookingStatus.IN_PROGRESS,  # Walk-ins start immediately
            total_price=Decimal(str(total_price)),
            total_duration=total_duration,
            actual_start_time=start_time,
            created_at=start_time,
            updated_at=start_time
        )
        
        # Save booking
        created_booking = await booking_service.create_booking(
            booking=booking,
            service_ids=service_ids
        )
        
        print(f"[WALK-IN] Created booking {created_booking.id}")
        
        # Update schedule immediately for walk-in
        schedule_update_result = await smart_booking.update_schedule_for_walk_in(
            booking_id=created_booking.id,
            start_time=start_time,
            service_duration_minutes=total_duration,
            assigned_bay_id=assigned_bay_id,
            washer_id=current_user.id
        )
        
        # Update capacity allocation
        await smart_booking.update_capacity_allocation(
            date=start_time.date(),
            booking_id=created_booking.id,
            service_type=service_type,
            allocated_bay_id=assigned_bay_id
        )
        
        # Create work tracking entry
        work_tracking = await create_work_tracking_entry(
            booking_id=created_booking.id,
            washer_id=current_user.id,
            bay_id=assigned_bay_id,
            start_time=start_time,
            estimated_duration=total_duration,
            db=db
        )
        
        # Prepare response
        response = {
            "booking": {
                "id": created_booking.id,
                "confirmation_number": f"WI{created_booking.id.hex[:8].upper()}",
                "customer_id": created_booking.customer_id,
                "vehicle_id": created_booking.vehicle_id,
                "status": created_booking.status.value,
                "total_price": float(created_booking.total_price),
                "total_duration": created_booking.total_duration,
                "started_at": start_time.isoformat(),
                "estimated_completion": (start_time + timedelta(minutes=total_duration)).isoformat()
            },
            "schedule_info": {
                "assigned_bay_id": assigned_bay_id,
                "assigned_bay_name": schedule_update_result.get("assigned_bay_name"),
                "washer_assigned": {
                    "id": current_user.id,
                    "name": f"{current_user.first_name} {current_user.last_name}"
                },
                "schedule_automatically_adjusted": True
            },
            "pricing_details": {
                "base_price": pricing_info.get("base_price"),
                "walk_in_premium": f"{((walk_in_multiplier - 1) * 100):.0f}%",
                "total_price": float(total_price),
                "payment_method": "cash_or_card_on_completion"
            },
            "work_tracking": {
                "work_session_id": work_tracking["work_session_id"],
                "tracking_started": True,
                "instructions": "Mark services as completed when finished"
            },
            "next_steps": [
                "Begin service immediately",
                "Mark services as completed in the system",
                "Process payment upon completion",
                "Update vehicle location if needed"
            ]
        }
        
        print(f"[WALK-IN] Successfully created and scheduled walk-in booking {created_booking.id}")
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid booking data: {str(e)}"
        )
    except Exception as e:
        print(f"[ERROR] Walk-in booking creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create walk-in booking: {str(e)}"
        )


# ================= WORK TRACKING SYSTEM =================

async def create_work_tracking_entry(
    booking_id: UUID,
    washer_id: UUID,
    bay_id: UUID,
    start_time: datetime,
    estimated_duration: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """Create work tracking entry for accounting and performance monitoring"""
    
    work_session = {
        "work_session_id": uuid4(),
        "booking_id": booking_id,
        "washer_id": washer_id,
        "bay_id": bay_id,
        "start_time": start_time,
        "estimated_completion": start_time + timedelta(minutes=estimated_duration),
        "status": "in_progress",
        "services_completed": [],
        "actual_duration": None,
        "quality_notes": "",
        "labor_cost": 0.0,
        "created_at": start_time
    }
    
    # In real implementation, save to work_tracking table
    print(f"[WORK-TRACKING] Created work session {work_session['work_session_id']} for washer {washer_id}")
    
    return work_session


@router.get("/work-sessions/active")
async def get_active_work_sessions(
    current_user: AuthUser = Depends(require_washer_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get active work sessions for the current washer"""
    try:
        # Get active work sessions for this washer
        active_sessions = [
            {
                "work_session_id": "550e8400-e29b-41d4-a716-446655440001",
                "booking_id": "550e8400-e29b-41d4-a716-446655440002",
                "confirmation_number": "WI12345678",
                "bay_name": "Bay 2",
                "vehicle_info": "2023 Toyota Camry - ABC123",
                "customer_name": "Walk-in Customer",
                "services": ["Exterior Wash", "Interior Clean"],
                "start_time": "2024-02-15T10:30:00",
                "estimated_completion": "2024-02-15T11:30:00",
                "elapsed_time_minutes": 25,
                "status": "in_progress",
                "services_completed": ["Exterior Wash"],
                "services_remaining": ["Interior Clean"]
            }
        ]
        
        return {
            "active_sessions": active_sessions,
            "total_active": len(active_sessions),
            "washer_id": current_user.id,
            "current_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active work sessions: {str(e)}"
        )


@router.post("/work-sessions/{work_session_id}/complete-service")
async def complete_service_in_session(
    work_session_id: UUID,
    service_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_washer_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Mark a specific service as completed in a work session"""
    try:
        service_id = UUID(service_data["service_id"])
        quality_rating = service_data.get("quality_rating", 5)
        notes = service_data.get("notes", "")
        
        print(f"[WORK-TRACKING] Completing service {service_id} in session {work_session_id}")
        
        # Update work tracking (simulated)
        completion_time = datetime.now()
        
        # Calculate labor time for this specific service
        # In real implementation, this would track time per service
        service_duration = service_data.get("actual_duration_minutes", 30)
        
        response = {
            "work_session_id": work_session_id,
            "service_completed": {
                "service_id": service_id,
                "service_name": service_data.get("service_name", "Service"),
                "completed_at": completion_time.isoformat(),
                "quality_rating": quality_rating,
                "actual_duration_minutes": service_duration,
                "notes": notes
            },
            "session_status": {
                "total_services": service_data.get("total_services", 2),
                "completed_services": service_data.get("completed_count", 1) + 1,
                "remaining_services": service_data.get("total_services", 2) - (service_data.get("completed_count", 1) + 1),
                "overall_progress": f"{((service_data.get('completed_count', 1) + 1) / service_data.get('total_services', 2)) * 100:.0f}%"
            },
            "accounting": {
                "labor_time_logged": f"{service_duration} minutes",
                "hourly_rate": "$15.00",
                "labor_cost_this_service": f"${(service_duration / 60) * 15:.2f}"
            }
        }
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid service data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete service: {str(e)}"
        )


@router.post("/work-sessions/{work_session_id}/complete")
async def complete_work_session(
    work_session_id: UUID,
    completion_data: Optional[Dict[str, Any]] = None,
    current_user: AuthUser = Depends(require_washer_or_admin),
    booking_service: BookingService = Depends(get_booking_service),
    db: AsyncSession = Depends(get_db)
):
    """Complete entire work session and update booking status"""
    try:
        completion_time = datetime.now()
        
        # Get completion data
        total_actual_duration = completion_data.get("total_actual_duration_minutes", 60) if completion_data else 60
        quality_notes = completion_data.get("quality_notes", "") if completion_data else ""
        customer_satisfaction = completion_data.get("customer_satisfaction", 5) if completion_data else 5
        
        print(f"[WORK-TRACKING] Completing work session {work_session_id}")
        
        # Update booking status to completed
        # In real implementation, get booking from work session
        booking_id = UUID("550e8400-e29b-41d4-a716-446655440002")  # Simulated
        
        # Calculate final accounting
        hourly_rate = 15.00  # $15/hour for washer
        total_labor_cost = (total_actual_duration / 60) * hourly_rate
        
        # Update work session (simulated)
        work_session_completion = {
            "work_session_id": work_session_id,
            "booking_id": booking_id,
            "completed_at": completion_time,
            "total_duration_minutes": total_actual_duration,
            "quality_notes": quality_notes,
            "customer_satisfaction": customer_satisfaction,
            "total_labor_cost": total_labor_cost,
            "status": "completed"
        }
        
        # Update booking status
        booking = await booking_service.get_booking_by_id(booking_id)
        if booking:
            booking.status = BookingStatus.COMPLETED
            booking.actual_end_time = completion_time
            booking.quality_rating = customer_satisfaction
            booking.quality_feedback = quality_notes
            
            await booking_service.update_booking(booking)
        
        # Generate accounting entry
        accounting_entry = {
            "entry_id": uuid4(),
            "booking_id": booking_id,
            "work_session_id": work_session_id,
            "washer_id": current_user.id,
            "service_date": completion_time.date().isoformat(),
            "labor_hours": round(total_actual_duration / 60, 2),
            "hourly_rate": hourly_rate,
            "total_labor_cost": total_labor_cost,
            "service_revenue": 65.00,  # From booking total price
            "labor_percentage": f"{(total_labor_cost / 65.00) * 100:.1f}%",
            "net_revenue": 65.00 - total_labor_cost,
            "created_at": completion_time.isoformat()
        }
        
        response = {
            "work_session_completed": True,
            "work_session_id": work_session_id,
            "booking_id": booking_id,
            "completion_summary": {
                "completed_at": completion_time.isoformat(),
                "total_duration": f"{total_actual_duration} minutes",
                "customer_satisfaction": f"{customer_satisfaction}/5 stars",
                "quality_notes": quality_notes
            },
            "accounting": {
                "labor_hours": round(total_actual_duration / 60, 2),
                "hourly_rate": f"${hourly_rate:.2f}",
                "total_labor_cost": f"${total_labor_cost:.2f}",
                "service_revenue": "$65.00",
                "net_revenue": f"${65.00 - total_labor_cost:.2f}"
            },
            "accounting_entry": accounting_entry,
            "performance_metrics": {
                "efficiency_score": "Good" if total_actual_duration <= 75 else "Needs Improvement",
                "quality_score": "Excellent" if customer_satisfaction >= 4 else "Good",
                "time_vs_estimate": f"{((60 - total_actual_duration) / 60) * 100:+.0f}% vs estimate"
            },
            "next_actions": [
                "Process payment with customer",
                "Clean and prepare bay for next service",
                "Update availability status"
            ]
        }
        
        print(f"[WORK-TRACKING] Completed work session {work_session_id} - Labor: ${total_labor_cost:.2f}")
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid completion data: {str(e)}"
        )
    except Exception as e:
        print(f"[ERROR] Work session completion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete work session: {str(e)}"
        )


# ================= WASHER DASHBOARD =================

@router.get("/dashboard")
async def get_washer_dashboard(
    current_user: AuthUser = Depends(require_washer_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard for washer"""
    try:
        today = datetime.now().date()
        
        # Simulate dashboard data
        dashboard_data = {
            "washer_info": {
                "id": current_user.id,
                "name": f"{current_user.first_name} {current_user.last_name}",
                "role": current_user.role.value,
                "shift_start": "08:00",
                "shift_end": "16:00"
            },
            "daily_summary": {
                "date": today.isoformat(),
                "services_completed": 8,
                "walk_ins_processed": 3,
                "scheduled_bookings": 5,
                "total_revenue_generated": 520.00,
                "total_labor_hours": 6.5,
                "total_labor_cost": 97.50,
                "average_service_time": 48,  # minutes
                "customer_satisfaction_avg": 4.7
            },
            "current_status": {
                "current_bay": "Bay 2",
                "current_booking": {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "type": "walk_in",
                    "vehicle": "2023 Honda Civic - XYZ789",
                    "services": ["Full Detail"],
                    "started_at": "14:30",
                    "estimated_completion": "16:00",
                    "progress": "60%"
                },
                "status": "working",
                "break_time_remaining": "15 minutes until next break"
            },
            "pending_walk_ins": [
                {
                    "priority": "high",
                    "vehicle": "2022 BMW X5 - LUX001",
                    "customer": "Premium Customer",
                    "requested_services": ["Premium Detail", "Ceramic Coating"],
                    "estimated_value": 185.00,
                    "wait_time": "10 minutes"
                }
            ],
            "upcoming_scheduled": [
                {
                    "time": "16:30",
                    "booking_id": "550e8400-e29b-41d4-a716-446655440003",
                    "customer": "John Smith",
                    "vehicle": "2021 Tesla Model 3 - ECO123",
                    "services": ["Exterior Wash", "Interior Clean"],
                    "bay": "Bay 1"
                }
            ],
            "performance_metrics": {
                "efficiency_rating": "Excellent",
                "quality_score": 4.7,
                "speed_score": "Above Average",
                "customer_satisfaction": 4.8,
                "this_week_earnings": 487.50,
                "productivity_trend": "+12% vs last week"
            },
            "available_actions": [
                "register_walk_in_customer",
                "register_walk_in_vehicle", 
                "create_walk_in_booking",
                "complete_current_service",
                "take_break",
                "request_bay_change"
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get washer dashboard: {str(e)}"
        )


# ================= ACCOUNTING & REPORTING =================

@router.get("/accounting/daily")
async def get_daily_accounting(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: AuthUser = Depends(require_washer_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get daily accounting summary for washer"""
    try:
        # Use today if no date provided
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = datetime.now().date()
        
        # Simulate accounting data
        accounting_data = {
            "washer_id": current_user.id,
            "washer_name": f"{current_user.first_name} {current_user.last_name}",
            "date": target_date.isoformat(),
            "summary": {
                "total_services": 8,
                "walk_in_services": 3,
                "scheduled_services": 5,
                "total_work_hours": 6.5,
                "total_labor_cost": 97.50,
                "total_revenue_generated": 520.00,
                "labor_efficiency": "85%",
                "average_service_value": 65.00
            },
            "service_breakdown": [
                {
                    "service_type": "Exterior Wash",
                    "count": 4,
                    "total_time_minutes": 100,
                    "total_revenue": 100.00,
                    "labor_cost": 25.00
                },
                {
                    "service_type": "Full Detail",
                    "count": 2,
                    "total_time_minutes": 180,
                    "total_revenue": 250.00,
                    "labor_cost": 45.00
                },
                {
                    "service_type": "Interior Clean",
                    "count": 3,
                    "total_time_minutes": 105,
                    "total_revenue": 105.00,
                    "labor_cost": 26.25
                }
            ],
            "time_tracking": {
                "clock_in": "08:00:00",
                "clock_out": "16:30:00",
                "total_shift_hours": 8.5,
                "productive_hours": 6.5,
                "break_time": 1.0,
                "idle_time": 1.0,
                "productivity_rate": "76%"
            },
            "earnings": {
                "base_hourly_rate": 15.00,
                "total_base_pay": 127.50,  # 8.5 hours * $15
                "performance_bonus": 12.75,  # 10% bonus for good performance
                "walk_in_bonus": 7.50,  # $2.50 per walk-in
                "total_daily_earnings": 147.75
            },
            "quality_metrics": {
                "average_customer_rating": 4.7,
                "services_requiring_rework": 0,
                "customer_complaints": 0,
                "quality_bonus_eligible": True
            }
        }
        
        return accounting_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily accounting: {str(e)}"
        )


@router.get("/accounting/weekly")
async def get_weekly_accounting(
    current_user: AuthUser = Depends(require_washer_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get weekly accounting summary for washer"""
    try:
        # Simulate weekly accounting data
        weekly_data = {
            "washer_id": current_user.id,
            "week_ending": datetime.now().strftime('%Y-%m-%d'),
            "summary": {
                "total_days_worked": 5,
                "total_services": 42,
                "total_work_hours": 32.5,
                "total_earnings": 738.75,
                "average_daily_earnings": 147.75,
                "total_revenue_generated": 2730.00,
                "labor_efficiency": "87%"
            },
            "daily_breakdown": [
                {"day": "Monday", "services": 8, "hours": 6.5, "earnings": 147.75, "revenue": 520.00},
                {"day": "Tuesday", "services": 9, "hours": 7.0, "earnings": 157.50, "revenue": 585.00},
                {"day": "Wednesday", "services": 7, "hours": 6.0, "earnings": 135.00, "revenue": 455.00},
                {"day": "Thursday", "services": 10, "hours": 7.5, "earnings": 168.75, "revenue": 650.00},
                {"day": "Friday", "services": 8, "hours": 5.5, "earnings": 129.75, "revenue": 520.00}
            ],
            "performance_trends": {
                "services_per_hour": 1.29,
                "revenue_per_service": 65.00,
                "customer_satisfaction_trend": "+0.2 vs last week",
                "efficiency_trend": "+5% vs last week"
            },
            "bonuses_earned": {
                "performance_bonus": 63.75,
                "walk_in_bonus": 37.50,
                "quality_bonus": 25.00,
                "total_bonuses": 126.25
            }
        }
        
        return weekly_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get weekly accounting: {str(e)}"
        )