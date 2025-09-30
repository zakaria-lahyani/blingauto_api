"""
Advanced Features API Router
Handles vehicle history, dynamic pricing, analytics, and business optimization.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.simple_database import get_db
from src.shared.auth import get_current_active_user, require_manager_or_admin
from src.features.auth.domain.entities import AuthUser
from src.features.auth.domain.enums import AuthRole

router = APIRouter(tags=["Advanced Features"])


# ================= VEHICLE HISTORY & RECOMMENDATIONS =================

@router.get("/vehicles/{vehicle_id}/history")
async def get_vehicle_history(
    vehicle_id: UUID,
    include_recommendations: bool = Query(True, description="Include service recommendations"),
    current_user: AuthUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive vehicle service history with recommendations"""
    try:
        # Simulate vehicle history data (in real implementation, query from database)
        vehicle_history = {
            "vehicle_id": vehicle_id,
            "total_services": 12,
            "total_spent": 850.50,
            "last_service_date": "2024-01-15",
            "average_service_interval_days": 28,
            "bookings": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "date": "2024-01-15",
                    "services": ["Exterior Wash", "Interior Clean"],
                    "total_price": 45.00,
                    "rating": 5,
                    "notes": "Excellent service"
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002", 
                    "date": "2023-12-18",
                    "services": ["Full Detail", "Wax Protection"],
                    "total_price": 125.00,
                    "rating": 4,
                    "notes": "Good detailing work"
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440003",
                    "date": "2023-11-20",
                    "services": ["Exterior Wash"],
                    "total_price": 25.00,
                    "rating": 5,
                    "notes": "Quick and efficient"
                }
            ],
            "service_patterns": {
                "most_frequent_services": ["Exterior Wash", "Interior Clean"],
                "seasonal_preferences": {
                    "winter": ["Interior Protection", "Salt Removal"],
                    "summer": ["UV Protection", "Air Conditioning Clean"]
                },
                "average_spending_per_visit": 71.25
            }
        }
        
        if include_recommendations:
            # Get vehicle info for smart recommendations
            days_since_last_service = (datetime.now().date() - 
                                     datetime.strptime(vehicle_history["last_service_date"], '%Y-%m-%d').date()).days
            
            recommendations = []
            
            # Time-based recommendations
            if days_since_last_service >= 30:
                recommendations.append({
                    "service_name": "Exterior Wash & Vacuum",
                    "reason": "It's been over 30 days since your last service",
                    "priority": "high",
                    "estimated_price": 35.00,
                    "discount_available": True,
                    "discount_percentage": 10
                })
            
            # Season-based recommendations
            current_month = datetime.now().month
            if current_month in [12, 1, 2]:  # Winter months
                recommendations.append({
                    "service_name": "Winter Protection Package",
                    "reason": "Winter conditions require special protection",
                    "priority": "medium", 
                    "estimated_price": 85.00,
                    "discount_available": False
                })
            elif current_month in [6, 7, 8]:  # Summer months
                recommendations.append({
                    "service_name": "UV Protection & AC Clean",
                    "reason": "Summer heat and UV exposure protection",
                    "priority": "medium",
                    "estimated_price": 65.00,
                    "discount_available": True,
                    "discount_percentage": 15
                })
            
            # Pattern-based recommendations
            recommendations.append({
                "service_name": "Premium Detail Package",
                "reason": "Based on your history, you enjoy comprehensive cleaning",
                "priority": "low",
                "estimated_price": 150.00,
                "discount_available": True,
                "discount_percentage": 20,
                "savings_message": "20% off for loyal customers"
            })
            
            vehicle_history["recommendations"] = recommendations
        
        return vehicle_history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vehicle history: {str(e)}"
        )


@router.get("/customers/analytics")
async def get_customer_analytics(
    current_user: AuthUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get customer analytics and insights"""
    try:
        # Simulate customer analytics (in real implementation, aggregate from database)
        analytics = {
            "customer_id": current_user.id,
            "membership_since": "2023-06-15",
            "total_bookings": 15,
            "total_spent": 1250.75,
            "average_booking_value": 83.38,
            "last_service_date": "2024-01-15",
            "favorite_services": [
                {"name": "Exterior Wash", "count": 8},
                {"name": "Interior Clean", "count": 6},
                {"name": "Full Detail", "count": 3}
            ],
            "preferred_time_slots": {
                "morning": 40,
                "afternoon": 35, 
                "evening": 25
            },
            "seasonal_activity": {
                "spring": 4,
                "summer": 5,
                "fall": 3,
                "winter": 3
            },
            "loyalty_status": {
                "tier": "Gold",
                "points_earned": 1251,
                "points_available": 425,
                "next_tier": "Platinum",
                "points_to_next_tier": 749
            },
            "savings_opportunities": [
                {
                    "type": "package_deal",
                    "title": "Monthly Maintenance Package",
                    "description": "Save 25% with monthly exterior + interior package",
                    "potential_savings": 15.00
                },
                {
                    "type": "loyalty_bonus",
                    "title": "Gold Member Bonus",
                    "description": "Extra 10% off next premium service",
                    "potential_savings": 12.50
                }
            ]
        }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer analytics: {str(e)}"
        )


# ================= DYNAMIC PRICING ENGINE =================

@router.get("/pricing/dynamic")
async def get_dynamic_pricing(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    time: str = Query(..., description="Time in HH:MM format"),
    service_type: str = Query("exterior_wash", description="Type of service"),
    weather_condition: Optional[str] = Query(None, description="Weather condition: sunny, rain, snow"),
    current_user: AuthUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dynamic pricing based on demand, weather, and time factors"""
    try:
        # Parse datetime
        booking_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        
        # Base pricing (simulate lookup from service catalog)
        base_prices = {
            "exterior_wash": 25.00,
            "interior_clean": 35.00,
            "full_detail": 125.00,
            "express_wash": 15.00
        }
        
        base_price = base_prices.get(service_type, 25.00)
        
        # Initialize pricing factors
        demand_multiplier = 1.0
        weather_multiplier = 1.0
        time_multiplier = 1.0
        pricing_factors = []
        
        # Time-based pricing
        hour = booking_datetime.hour
        day_of_week = booking_datetime.weekday()
        
        # Peak hours (morning rush, lunch, evening)
        if hour in [8, 9, 10] or hour in [12, 13] or hour in [17, 18, 19]:
            time_multiplier = 1.15
            pricing_factors.append("Peak hours (+15%)")
        
        # Weekend premium
        if day_of_week >= 5:  # Saturday, Sunday
            demand_multiplier = 1.2
            pricing_factors.append("Weekend premium (+20%)")
        
        # Weather-based pricing
        if weather_condition == "rain":
            weather_multiplier = 1.3
            pricing_factors.append("Rainy day premium (+30% - higher indoor demand)")
        elif weather_condition == "snow":
            weather_multiplier = 1.25
            pricing_factors.append("Snow conditions (+25% - salt/de-icing cleanup)")
        elif weather_condition == "sunny":
            # Sunny days might have slight discount for outdoor services
            if service_type == "exterior_wash":
                weather_multiplier = 0.95
                pricing_factors.append("Sunny day discount (-5% for exterior services)")
        
        # Demand-based adjustments (simulate real-time demand)
        current_demand = _simulate_current_demand(booking_datetime, service_type)
        
        if current_demand > 0.8:  # High demand
            demand_multiplier *= 1.25
            pricing_factors.append("High demand (+25%)")
        elif current_demand > 0.6:  # Medium demand
            demand_multiplier *= 1.1
            pricing_factors.append("Medium demand (+10%)")
        elif current_demand < 0.3:  # Low demand
            demand_multiplier *= 0.9
            pricing_factors.append("Low demand discount (-10%)")
        
        # Calculate final price
        total_multiplier = demand_multiplier * weather_multiplier * time_multiplier
        adjusted_price = round(base_price * total_multiplier, 2)
        
        response = {
            "service_type": service_type,
            "base_price": base_price,
            "adjusted_price": adjusted_price,
            "demand_multiplier": round(total_multiplier, 2),
            "pricing_factors": pricing_factors,
            "savings_vs_peak": round(max(0, (base_price * 1.5) - adjusted_price), 2),
            "demand_level": _get_demand_level_text(current_demand),
            "recommendation": _get_pricing_recommendation(total_multiplier, pricing_factors)
        }
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date or time format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate dynamic pricing: {str(e)}"
        )


def _simulate_current_demand(booking_datetime: datetime, service_type: str) -> float:
    """Simulate current demand based on time and service type"""
    hour = booking_datetime.hour
    day_of_week = booking_datetime.weekday()
    
    # Base demand patterns
    base_demand = 0.5
    
    # Time of day influence
    if hour in [8, 9, 10]:  # Morning rush
        base_demand += 0.3
    elif hour in [12, 13]:  # Lunch time
        base_demand += 0.2
    elif hour in [17, 18, 19]:  # Evening
        base_demand += 0.25
    elif hour < 8 or hour > 20:  # Off hours
        base_demand -= 0.2
    
    # Day of week influence
    if day_of_week >= 5:  # Weekend
        base_demand += 0.2
    
    # Service type influence
    if service_type in ["full_detail", "premium_wash"]:
        base_demand += 0.1  # Premium services have higher demand
    
    return min(1.0, max(0.1, base_demand))


def _get_demand_level_text(demand: float) -> str:
    """Convert demand level to text"""
    if demand > 0.8:
        return "Very High"
    elif demand > 0.6:
        return "High"
    elif demand > 0.4:
        return "Medium"
    elif demand > 0.2:
        return "Low"
    else:
        return "Very Low"


def _get_pricing_recommendation(multiplier: float, factors: List[str]) -> str:
    """Get pricing recommendation based on multiplier"""
    if multiplier > 1.3:
        return "Consider booking at a different time for better rates"
    elif multiplier > 1.1:
        return "Moderate premium pricing - good value for peak convenience"
    elif multiplier < 0.95:
        return "Great deal! Lower than usual pricing"
    else:
        return "Standard pricing - good time to book"


# ================= MOBILE TEAM ROUTE OPTIMIZATION =================

@router.get("/mobile-teams/{team_id}/optimize-route")
async def optimize_mobile_team_route(
    team_id: UUID,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: AuthUser = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Optimize route for mobile team's daily schedule"""
    try:
        # Parse date
        route_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Simulate mobile team data and bookings
        team_info = {
            "id": team_id,
            "name": "Mobile Team Alpha",
            "base_location": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "address": "123 Main St, New York, NY"
            },
            "service_radius_km": 25,
            "max_vehicles_per_day": 8
        }
        
        # Simulate daily bookings
        bookings = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "scheduled_time": "09:00",
                "estimated_duration": 45,
                "location": {
                    "latitude": 40.7589,
                    "longitude": -73.9851,
                    "address": "Times Square, NY"
                },
                "customer_name": "John Doe",
                "service_type": "Exterior Wash"
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "scheduled_time": "10:30",
                "estimated_duration": 60,
                "location": {
                    "latitude": 40.7505,
                    "longitude": -73.9934,
                    "address": "Empire State Building, NY"
                },
                "customer_name": "Jane Smith",
                "service_type": "Full Detail"
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "scheduled_time": "12:00",
                "estimated_duration": 30,
                "location": {
                    "latitude": 40.7484,
                    "longitude": -73.9857,
                    "address": "Flatiron Building, NY"
                },
                "customer_name": "Bob Wilson",
                "service_type": "Express Wash"
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440004",
                "scheduled_time": "14:00",
                "estimated_duration": 50,
                "location": {
                    "latitude": 40.7614,
                    "longitude": -73.9776,
                    "address": "Central Park South, NY"
                },
                "customer_name": "Alice Johnson",
                "service_type": "Interior + Exterior"
            }
        ]
        
        # Simulate route optimization calculation
        optimized_route = {
            "team_id": team_id,
            "date": date,
            "total_distance_km": 15.2,
            "total_time_minutes": 385,
            "total_service_time_minutes": 185,
            "total_travel_time_minutes": 45,
            "fuel_cost_estimate": 12.50,
            "optimization_score": 8.7,
            "stops": [
                {
                    "order": 1,
                    "booking_id": bookings[0]["id"],
                    "address": bookings[0]["location"]["address"],
                    "estimated_arrival": "08:45",
                    "service_start": "09:00",
                    "service_end": "09:45",
                    "travel_time_to_next": 8,
                    "distance_to_next_km": 2.1
                },
                {
                    "order": 2,
                    "booking_id": bookings[1]["id"],
                    "address": bookings[1]["location"]["address"],
                    "estimated_arrival": "09:53",
                    "service_start": "10:00",
                    "service_end": "11:00",
                    "travel_time_to_next": 12,
                    "distance_to_next_km": 3.2
                },
                {
                    "order": 3,
                    "booking_id": bookings[2]["id"],
                    "address": bookings[2]["location"]["address"],
                    "estimated_arrival": "11:12",
                    "service_start": "11:30",
                    "service_end": "12:00",
                    "travel_time_to_next": 15,
                    "distance_to_next_km": 4.1
                },
                {
                    "order": 4,
                    "booking_id": bookings[3]["id"],
                    "address": bookings[3]["location"]["address"],
                    "estimated_arrival": "12:15",
                    "service_start": "12:30",
                    "service_end": "13:20",
                    "travel_time_to_next": 10,
                    "distance_to_next_km": 5.8,
                    "return_to_base": True
                }
            ],
            "efficiency_metrics": {
                "stops_per_hour": 1.04,
                "travel_vs_service_ratio": 0.24,
                "customer_satisfaction_score": 9.2,
                "fuel_efficiency": "Good"
            },
            "recommendations": [
                "Route is well optimized with minimal travel time",
                "Consider 15-minute buffer between appointments",
                "Traffic conditions optimal for morning schedule"
            ]
        }
        
        return optimized_route
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize route: {str(e)}"
        )


# ================= CAPACITY ANALYTICS =================

@router.get("/analytics/capacity/daily")
async def get_daily_capacity_analytics(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    current_user: AuthUser = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get daily capacity analytics and utilization metrics"""
    try:
        # Parse date
        analysis_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Simulate daily capacity analytics
        analytics = {
            "date": date,
            "total_capacity": 48,  # 6 bays × 8 hours = 48 slots
            "booked_slots": 35,
            "available_slots": 13,
            "utilization_rate": 0.729,  # 35/48
            "revenue_generated": 2450.50,
            "average_service_value": 70.01,
            "peak_hours": [
                {"hour": "09:00-10:00", "utilization": 0.95, "revenue": 315.50},
                {"hour": "10:00-11:00", "utilization": 0.90, "revenue": 298.75},
                {"hour": "12:00-13:00", "utilization": 0.85, "revenue": 275.25}
            ],
            "slow_hours": [
                {"hour": "07:00-08:00", "utilization": 0.25, "revenue": 85.00},
                {"hour": "15:00-16:00", "utilization": 0.35, "revenue": 125.50},
                {"hour": "19:00-20:00", "utilization": 0.20, "revenue": 67.25}
            ],
            "bay_analytics": [
                {
                    "bay_id": "550e8400-e29b-41d4-a716-446655440001",
                    "bay_name": "Bay 1 - Premium",
                    "utilization_rate": 0.85,
                    "revenue": 525.75,
                    "services_completed": 7,
                    "average_service_duration": 52,
                    "downtime_minutes": 25
                },
                {
                    "bay_id": "550e8400-e29b-41d4-a716-446655440002",
                    "bay_name": "Bay 2 - Standard",
                    "utilization_rate": 0.75,
                    "revenue": 385.25,
                    "services_completed": 6,
                    "average_service_duration": 45,
                    "downtime_minutes": 35
                },
                {
                    "bay_id": "550e8400-e29b-41d4-a716-446655440003",
                    "bay_name": "Bay 3 - Express",
                    "utilization_rate": 0.90,
                    "revenue": 425.50,
                    "services_completed": 8,
                    "average_service_duration": 35,
                    "downtime_minutes": 15
                }
            ],
            "service_type_breakdown": [
                {"type": "Exterior Wash", "count": 12, "revenue": 380.00, "avg_duration": 25},
                {"type": "Full Detail", "count": 8, "revenue": 1250.00, "avg_duration": 90},
                {"type": "Interior Clean", "count": 10, "revenue": 450.00, "avg_duration": 40},
                {"type": "Express Wash", "count": 5, "revenue": 95.00, "avg_duration": 15}
            ],
            "recommendations": [
                "Consider offering discounts during 15:00-16:00 slow period",
                "Bay 3 (Express) showing excellent utilization - consider expanding express services",
                "Peak morning hours at capacity - potential for premium pricing",
                "Average service duration suggests good efficiency"
            ]
        }
        
        return analytics
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily capacity analytics: {str(e)}"
        )


@router.get("/analytics/capacity/weekly")
async def get_weekly_capacity_trends(
    current_user: AuthUser = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get weekly capacity trends and performance metrics"""
    try:
        # Simulate weekly analytics
        analytics = {
            "week_start": (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d'),
            "week_end": datetime.now().strftime('%Y-%m-%d'),
            "average_utilization": 0.73,
            "total_revenue": 16450.75,
            "total_services": 245,
            "best_day": {
                "date": "2024-01-20",
                "utilization": 0.89,
                "revenue": 2850.25,
                "day_name": "Saturday"
            },
            "worst_day": {
                "date": "2024-01-16",
                "utilization": 0.52,
                "revenue": 1425.50,
                "day_name": "Tuesday"
            },
            "daily_trends": [
                {"day": "Monday", "utilization": 0.68, "revenue": 2125.50},
                {"day": "Tuesday", "utilization": 0.52, "revenue": 1425.50},
                {"day": "Wednesday", "utilization": 0.65, "revenue": 1985.75},
                {"day": "Thursday", "utilization": 0.71, "revenue": 2245.25},
                {"day": "Friday", "utilization": 0.82, "revenue": 2685.00},
                {"day": "Saturday", "utilization": 0.89, "revenue": 2850.25},
                {"day": "Sunday", "utilization": 0.85, "revenue": 2633.50}
            ],
            "service_trends": {
                "growing": ["Express Wash", "Interior Protection"],
                "declining": ["Basic Wash"],
                "stable": ["Full Detail", "Exterior Wash"]
            },
            "recommendations": [
                "Tuesday shows consistently low utilization - consider promotional campaigns",
                "Weekend performance excellent - maintain current pricing strategy",
                "Express services trending up - consider dedicated express bay",
                "Overall trend positive with 12% growth vs previous week"
            ],
            "comparison_previous_week": {
                "utilization_change": 0.08,
                "revenue_change": 0.12,
                "services_change": 0.15
            }
        }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get weekly capacity trends: {str(e)}"
        )


# ================= UPSELLING ENGINE =================

@router.post("/upselling/suggestions")
async def get_upselling_suggestions(
    request_data: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized upselling suggestions based on vehicle and history"""
    try:
        # Extract request data
        vehicle_id = request_data.get("vehicle_id")
        selected_services = request_data.get("selected_services", [])
        vehicle_type = request_data.get("vehicle_type", "Standard")
        customer_history = request_data.get("customer_history", {})
        
        # Simulate upselling logic
        upsell_options = []
        
        # Service-based upselling
        if "exterior_wash" in [s.lower() for s in selected_services]:
            upsell_options.append({
                "service_name": "Wax Protection Add-on",
                "service_id": "550e8400-e29b-41d4-a716-446655440001",
                "additional_cost": 25.00,
                "reason": "Protect your paint with premium wax coating",
                "confidence_score": 0.85,
                "estimated_additional_time": 15,
                "popularity": "87% of customers add wax protection"
            })
        
        if "interior_clean" in [s.lower() for s in selected_services]:
            upsell_options.append({
                "service_name": "Fabric Protection Treatment",
                "service_id": "550e8400-e29b-41d4-a716-446655440002",
                "additional_cost": 35.00,
                "reason": "Keep your seats looking new with stain protection",
                "confidence_score": 0.72,
                "estimated_additional_time": 20,
                "popularity": "62% of customers choose fabric protection"
            })
        
        # Vehicle-type based upselling
        if "BMW" in vehicle_type or "Mercedes" in vehicle_type or "Audi" in vehicle_type:
            upsell_options.append({
                "service_name": "Premium Luxury Detail",
                "service_id": "550e8400-e29b-41d4-a716-446655440003",
                "additional_cost": 75.00,
                "reason": "Specialized care for luxury vehicles with premium products",
                "confidence_score": 0.90,
                "estimated_additional_time": 45,
                "luxury_benefit": "Hand-applied ceramic coating and leather conditioning"
            })
        
        # History-based upselling
        total_bookings = customer_history.get("total_bookings", 0)
        if total_bookings >= 5:
            upsell_options.append({
                "service_name": "Loyalty Member Special - Full Detail",
                "service_id": "550e8400-e29b-41d4-a716-446655440004",
                "additional_cost": 85.00,
                "original_price": 125.00,
                "savings": 40.00,
                "reason": "Exclusive loyalty discount for valued customers",
                "confidence_score": 0.95,
                "estimated_additional_time": 90,
                "loyalty_perk": "32% discount applied automatically"
            })
        
        # Seasonal upselling
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:  # Winter
            upsell_options.append({
                "service_name": "Winter Salt Protection Package",
                "service_id": "550e8400-e29b-41d4-a716-446655440005",
                "additional_cost": 45.00,
                "reason": "Protect against road salt and winter damage",
                "confidence_score": 0.78,
                "estimated_additional_time": 25,
                "seasonal_benefit": "Undercarriage treatment included"
            })
        
        # Calculate bundle savings
        bundle_suggestions = []
        if len(upsell_options) >= 2:
            bundle_suggestions.append({
                "bundle_name": "Complete Care Package",
                "services": [opt["service_name"] for opt in upsell_options[:2]],
                "individual_total": sum(opt["additional_cost"] for opt in upsell_options[:2]),
                "bundle_price": sum(opt["additional_cost"] for opt in upsell_options[:2]) * 0.85,
                "savings": sum(opt["additional_cost"] for opt in upsell_options[:2]) * 0.15,
                "confidence_score": 0.88
            })
        
        response = {
            "upsell_options": upsell_options,
            "bundle_suggestions": bundle_suggestions,
            "personalization_factors": {
                "vehicle_type": vehicle_type,
                "customer_tier": "Gold" if total_bookings >= 5 else "Standard",
                "seasonal_relevance": "Winter protection recommended",
                "service_compatibility": "High compatibility with selected services"
            },
            "total_potential_value": sum(opt["additional_cost"] for opt in upsell_options),
            "recommendation_strength": "High" if len(upsell_options) >= 3 else "Medium"
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
            detail=f"Failed to get upselling suggestions: {str(e)}"
        )


@router.get("/services/packages/recommendations")
async def get_package_recommendations(
    vehicle_type: str = Query(..., description="Vehicle make and model"),
    current_user: AuthUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get service package recommendations based on vehicle type"""
    try:
        # Simulate package recommendations
        packages = [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Complete Care Monthly",
                "description": "Everything your vehicle needs for optimal care",
                "services": ["Exterior Wash", "Interior Clean", "Wax Protection", "Tire Shine"],
                "individual_prices": [25.00, 35.00, 25.00, 15.00],
                "total_value": 100.00,
                "package_price": 75.00,
                "savings": 25.00,
                "savings_percentage": 25,
                "recommended_frequency": "Monthly",
                "best_for": ["Regular maintenance", "Busy professionals", "Fleet vehicles"]
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "name": "Premium Detail Experience",
                "description": "Luxury treatment for discerning vehicle owners",
                "services": ["Full Detail", "Ceramic Coating", "Leather Conditioning", "Engine Bay Clean"],
                "individual_prices": [125.00, 150.00, 45.00, 35.00],
                "total_value": 355.00,
                "package_price": 285.00,
                "savings": 70.00,
                "savings_percentage": 20,
                "recommended_frequency": "Quarterly",
                "best_for": ["Luxury vehicles", "Car enthusiasts", "Special occasions"]
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440003",
                "name": "Express Convenience Pack",
                "description": "Quick and efficient for busy schedules",
                "services": ["Express Wash", "Quick Vacuum", "Dashboard Clean"],
                "individual_prices": [15.00, 10.00, 8.00],
                "total_value": 33.00,
                "package_price": 25.00,
                "savings": 8.00,
                "savings_percentage": 24,
                "recommended_frequency": "Bi-weekly",
                "best_for": ["Busy schedules", "Regular commuters", "Quick maintenance"]
            }
        ]
        
        # Customize recommendations based on vehicle type
        if any(luxury in vehicle_type.upper() for luxury in ["BMW", "MERCEDES", "AUDI", "LEXUS"]):
            # Promote premium package for luxury vehicles
            packages[1]["recommended"] = True
            packages[1]["special_offer"] = "10% additional discount for luxury vehicle owners"
        
        return packages
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get package recommendations: {str(e)}"
        )


# Helper functions for dynamic pricing
def _simulate_current_demand(booking_datetime: datetime, service_type: str) -> float:
    """Simulate current demand based on time and service type"""
    import random
    # Simple simulation - in real implementation would check actual bookings
    hour = booking_datetime.hour
    if hour in [8, 9, 10, 17, 18, 19]:  # Peak hours
        return 0.7 + random.random() * 0.3  # 0.7-1.0
    elif hour in [12, 13]:  # Lunch time
        return 0.6 + random.random() * 0.3  # 0.6-0.9
    else:
        return 0.3 + random.random() * 0.4  # 0.3-0.7


def _get_demand_level_text(demand: float) -> str:
    """Convert demand float to text description"""
    if demand > 0.8:
        return "High"
    elif demand > 0.6:
        return "Medium"
    elif demand > 0.4:
        return "Moderate"
    else:
        return "Low"


def _get_pricing_recommendation(multiplier: float, factors: List[str]) -> str:
    """Generate pricing recommendation based on multiplier and factors"""
    if multiplier > 1.3:
        return "Book during off-peak hours for better rates"
    elif multiplier > 1.1:
        return "Consider booking during weekdays for savings"
    elif multiplier < 0.9:
        return "Great time to book - discounted rates available!"
    else:
        return "Standard pricing in effect"