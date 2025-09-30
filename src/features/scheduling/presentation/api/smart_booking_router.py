"""
Smart Booking Engine API Router
Handles intelligent booking suggestions, availability checking, and optimization.
"""

from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import get_current_active_user
from src.features.auth.domain.entities import AuthUser
from src.features.scheduling.application.services.scheduling_service import SchedulingService
from src.features.scheduling.application.services.smart_booking_service import SmartBookingService
from src.features.scheduling.infrastructure.database.repositories import (
    BusinessHoursRepository, ResourceRepository, TimeSlotRepository, 
    SchedulingConflictRepository
)
from src.features.scheduling.infrastructure.database.wash_facility_repositories import CapacityAllocationRepository
from src.features.services.infrastructure.database.repositories import ServiceRepository
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository
from src.features.bookings.infrastructure.database.repositories import BookingRepository

router = APIRouter(prefix="/scheduling", tags=["Smart Booking"])


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


# ================= SMART AVAILABILITY ENDPOINTS =================

@router.get("/available-slots")
async def get_available_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    service_duration: int = Query(..., ge=15, le=480, description="Service duration in minutes"),
    service_type: str = Query("exterior_wash", description="Type of service"),
    vehicle_size: str = Query("standard", description="Vehicle size: compact, standard, large, oversized"),
    preferred_time: Optional[str] = Query(None, description="Preferred time: morning, afternoon, evening"),
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Get available time slots based on business hours and wash bay availability"""
    try:
        # Parse date
        booking_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get available slots using smart booking engine
        available_slots = await smart_booking.get_available_slots(
            date=booking_date,
            service_duration_minutes=service_duration,
            service_type=service_type,
            vehicle_size=vehicle_size,
            customer_id=current_user.id,
            preferred_time=preferred_time
        )
        
        # Convert to response format
        response_slots = []
        for slot in available_slots:
            response_slots.append({
                "start_time": slot["start_time"].isoformat(),
                "end_time": slot["end_time"].isoformat(),
                "bay_id": slot["bay_id"],
                "bay_name": slot["bay_name"],
                "bay_number": slot["bay_number"],
                "confidence_score": slot["confidence_score"],
                "estimated_price": slot["estimated_price"],
                "equipment_available": slot["equipment_available"]
            })
        
        return response_slots
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available slots: {str(e)}"
        )


@router.get("/smart-suggestions")
async def get_smart_suggestions(
    service_type: str = Query(..., description="Type of service"),
    preferred_time: str = Query("morning", description="Preferred time: morning, afternoon, evening"),
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days to look ahead"),
    max_suggestions: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Get smart booking suggestions based on historical data and preferences"""
    try:
        suggestions = await smart_booking.get_smart_suggestions(
            customer_id=current_user.id,
            service_type=service_type,
            preferred_time=preferred_time,
            days_ahead=days_ahead,
            max_suggestions=max_suggestions
        )
        
        # Convert to response format
        response_suggestions = []
        for suggestion in suggestions:
            response_suggestions.append({
                "date": suggestion["date"].strftime('%Y-%m-%d'),
                "time": suggestion["time"].strftime('%H:%M'),
                "bay_name": suggestion["bay_name"],
                "bay_id": suggestion["bay_id"],
                "confidence_score": suggestion["confidence_score"],
                "reasoning": suggestion["reasoning"],
                "estimated_price": suggestion["estimated_price"],
                "discount_available": suggestion.get("discount_available", False),
                "peak_time": suggestion.get("peak_time", False)
            })
        
        return response_suggestions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get smart suggestions: {str(e)}"
        )


@router.post("/check-availability")
async def check_availability_advanced(
    request_data: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Advanced availability checking with conflict detection"""
    try:
        # Extract request parameters
        booking_datetime = datetime.fromisoformat(request_data["scheduled_at"])
        service_duration = request_data["service_duration"]
        service_type = request_data.get("service_type", "exterior_wash")
        vehicle_size = request_data.get("vehicle_size", "standard")
        
        # Check availability
        availability_result = await smart_booking.check_availability_advanced(
            booking_datetime=booking_datetime,
            service_duration_minutes=service_duration,
            service_type=service_type,
            vehicle_size=vehicle_size,
            customer_id=current_user.id
        )
        
        response = {
            "available": availability_result["available"],
            "conflicts": availability_result.get("conflicts", []),
            "alternative_slots": availability_result.get("alternative_slots", []),
            "bay_assignments": availability_result.get("bay_assignments", []),
            "estimated_price": availability_result.get("estimated_price"),
            "recommendations": availability_result.get("recommendations", [])
        }
        
        return response
        
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check availability: {str(e)}"
        )


# ================= BOOKING OPTIMIZATION ENDPOINTS =================

@router.post("/optimize-booking")
async def optimize_booking(
    request_data: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Optimize a booking request for best time, bay, and pricing"""
    try:
        # Extract request parameters
        preferred_date = datetime.strptime(request_data["preferred_date"], '%Y-%m-%d').date()
        service_ids = request_data["service_ids"]
        vehicle_id = request_data["vehicle_id"]
        flexibility_hours = request_data.get("flexibility_hours", 2)
        
        # Optimize booking
        optimization_result = await smart_booking.optimize_booking(
            customer_id=current_user.id,
            vehicle_id=UUID(vehicle_id),
            service_ids=[UUID(sid) for sid in service_ids],
            preferred_date=preferred_date,
            flexibility_hours=flexibility_hours
        )
        
        response = {
            "optimized_slots": [
                {
                    "datetime": slot["datetime"].isoformat(),
                    "bay_id": slot["bay_id"],
                    "bay_name": slot["bay_name"],
                    "total_price": slot["total_price"],
                    "savings": slot["savings"],
                    "optimization_score": slot["optimization_score"],
                    "reasoning": slot["reasoning"]
                }
                for slot in optimization_result["optimized_slots"]
            ],
            "best_recommendation": optimization_result.get("best_recommendation"),
            "price_comparison": optimization_result.get("price_comparison"),
            "time_flexibility_benefits": optimization_result.get("time_flexibility_benefits")
        }
        
        return response
        
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize booking: {str(e)}"
        )


# ================= CAPACITY MANAGEMENT ENDPOINTS =================

@router.get("/capacity-status")
async def get_capacity_status(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Get real-time capacity status for wash bays"""
    try:
        # Use today if no date provided
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = datetime.now().date()
        
        capacity_status = await smart_booking.get_capacity_status(target_date)
        
        response = {
            "date": target_date.strftime('%Y-%m-%d'),
            "overall_utilization": capacity_status["overall_utilization"],
            "peak_hours": capacity_status["peak_hours"],
            "available_slots_count": capacity_status["available_slots_count"],
            "bay_status": [
                {
                    "bay_id": bay["bay_id"],
                    "bay_name": bay["bay_name"],
                    "utilization_rate": bay["utilization_rate"],
                    "available_slots": bay["available_slots"],
                    "next_available": bay["next_available"].isoformat() if bay["next_available"] else None,
                    "maintenance_window": bay.get("maintenance_window")
                }
                for bay in capacity_status["bay_status"]
            ],
            "recommendations": capacity_status.get("recommendations", [])
        }
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capacity status: {str(e)}"
        )


@router.get("/peak-hours-analysis")
async def get_peak_hours_analysis(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Analyze peak hours and booking patterns"""
    try:
        analysis = await smart_booking.analyze_peak_hours(days_back=days_back)
        
        response = {
            "analysis_period": f"Last {days_back} days",
            "peak_hours": analysis["peak_hours"],
            "slow_hours": analysis["slow_hours"],
            "daily_patterns": analysis["daily_patterns"],
            "weekly_patterns": analysis["weekly_patterns"],
            "utilization_trends": analysis["utilization_trends"],
            "recommendations": analysis["recommendations"]
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze peak hours: {str(e)}"
        )


# ================= CONFLICT RESOLUTION ENDPOINTS =================

@router.get("/conflicts")
async def get_scheduling_conflicts(
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Get scheduling conflicts with resolution status"""
    try:
        conflicts = await smart_booking.get_scheduling_conflicts(
            resolved=resolved,
            days_back=days_back
        )
        
        response_conflicts = []
        for conflict in conflicts:
            response_conflicts.append({
                "id": conflict["id"],
                "conflict_type": conflict["conflict_type"],
                "message": conflict["message"],
                "requested_time": conflict["requested_time"].isoformat(),
                "customer_id": conflict["customer_id"],
                "resource_id": conflict.get("resource_id"),
                "conflicting_booking_id": conflict.get("conflicting_booking_id"),
                "resolved": conflict["resolved"],
                "created_at": conflict["created_at"].isoformat(),
                "resolution_suggestions": conflict.get("resolution_suggestions", [])
            })
        
        return response_conflicts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduling conflicts: {str(e)}"
        )


@router.post("/conflicts/resolve")
async def resolve_scheduling_conflict(
    request_data: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_active_user),
    smart_booking: SmartBookingService = Depends(get_smart_booking_service)
):
    """Resolve scheduling conflict with smart suggestions"""
    try:
        # Extract conflict parameters
        requested_time = datetime.fromisoformat(request_data["requested_time"])
        service_duration = request_data["service_duration"]
        customer_preferences = request_data.get("customer_preferences", {})
        
        # Get resolution suggestions
        resolution = await smart_booking.resolve_conflict(
            requested_time=requested_time,
            service_duration_minutes=service_duration,
            customer_preferences=customer_preferences,
            customer_id=current_user.id
        )
        
        response = {
            "alternative_slots": [
                {
                    "start_time": alt["start_time"].isoformat(),
                    "end_time": alt["end_time"].isoformat(),
                    "bay_name": alt["bay_name"],
                    "bay_id": alt["bay_id"],
                    "preference_score": alt["preference_score"],
                    "time_difference_minutes": alt["time_difference_minutes"],
                    "pricing_impact": alt.get("pricing_impact", 0)
                }
                for alt in resolution["alternative_slots"]
            ],
            "best_alternative": resolution.get("best_alternative"),
            "conflict_reason": resolution.get("conflict_reason"),
            "resolution_strategy": resolution.get("resolution_strategy")
        }
        
        return response
        
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflict: {str(e)}"
        )