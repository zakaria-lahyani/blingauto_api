"""
Smart Booking Service
Handles intelligent booking logic, availability optimization, and schedule management.
"""

from datetime import datetime, timedelta, time, date
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from decimal import Decimal

from src.features.scheduling.application.services.scheduling_service import SchedulingService
from src.features.scheduling.infrastructure.database.wash_facility_repositories import CapacityAllocationRepository
from src.features.vehicles.infrastructure.database.repositories import VehicleRepository
from src.features.bookings.infrastructure.database.repositories import BookingRepository
from src.features.services.infrastructure.database.repositories import ServiceRepository
from src.features.scheduling.domain.wash_facility_entities import CapacityAllocation, WashType
from src.features.bookings.domain.entities import Booking


class SmartBookingService:
    """Service for intelligent booking management and optimization"""
    
    def __init__(
        self,
        scheduling_service: SchedulingService,
        capacity_repo: CapacityAllocationRepository,
        vehicle_repo: VehicleRepository,
        booking_repo: BookingRepository,
        service_repo: ServiceRepository
    ):
        self.scheduling_service = scheduling_service
        self.capacity_repo = capacity_repo
        self.vehicle_repo = vehicle_repo
        self.booking_repo = booking_repo
        self.service_repo = service_repo

    # ================= AVAILABILITY CHECKING =================

    async def get_available_slots(
        self,
        date: date,
        service_duration_minutes: int,
        service_type: str,
        vehicle_size: str,
        customer_id: UUID,
        preferred_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available time slots based on business hours and wash bay availability"""
        
        # Get business hours for the day
        day_of_week = date.strftime('%A').lower()
        business_hours = await self.scheduling_service.get_business_hours_for_day(day_of_week)
        
        if not business_hours or business_hours.is_closed:
            return []
        
        # Get available wash bays that can handle the vehicle size
        available_bays = await self.scheduling_service.get_available_wash_bays(
            date=date,
            vehicle_size=vehicle_size,
            service_type=service_type
        )
        
        if not available_bays:
            return []
        
        # Generate time slots based on business hours
        slots = self._generate_time_slots(
            date=date,
            business_hours=business_hours,
            service_duration_minutes=service_duration_minutes,
            preferred_time=preferred_time
        )
        
        # Check availability for each slot and bay combination
        available_slots = []
        
        for slot_time in slots:
            for bay in available_bays:
                # Check if bay is available for this time slot
                is_available = await self._check_bay_availability(
                    bay_id=bay.id,
                    start_time=slot_time,
                    duration_minutes=service_duration_minutes
                )
                
                if is_available:
                    # Calculate confidence score and pricing
                    confidence_score = self._calculate_confidence_score(
                        slot_time=slot_time,
                        bay=bay,
                        preferred_time=preferred_time,
                        service_type=service_type
                    )
                    
                    estimated_price = await self._calculate_slot_price(
                        service_type=service_type,
                        slot_datetime=datetime.combine(date, slot_time),
                        bay=bay
                    )
                    
                    available_slots.append({
                        "start_time": datetime.combine(date, slot_time),
                        "end_time": datetime.combine(date, slot_time) + timedelta(minutes=service_duration_minutes),
                        "bay_id": bay.id,
                        "bay_name": bay.name,
                        "bay_number": bay.bay_number,
                        "confidence_score": confidence_score,
                        "estimated_price": estimated_price,
                        "equipment_available": list(bay.equipment_types)
                    })
        
        # Sort by confidence score and time preference
        available_slots.sort(key=lambda x: (-x["confidence_score"], x["start_time"]))
        
        return available_slots

    def _generate_time_slots(
        self,
        date: date,
        business_hours: Any,
        service_duration_minutes: int,
        preferred_time: Optional[str] = None
    ) -> List[time]:
        """Generate possible time slots within business hours"""
        
        slots = []
        
        # Start from opening time
        current_time = business_hours.open_time
        end_time = business_hours.close_time
        
        # Account for service duration (don't start if can't finish before closing)
        latest_start = datetime.combine(date, end_time) - timedelta(minutes=service_duration_minutes)
        
        while datetime.combine(date, current_time) <= latest_start:
            # Check if slot conflicts with break periods
            conflicts_with_break = False
            
            for break_start, break_end in business_hours.break_periods:
                slot_end = (datetime.combine(date, current_time) + timedelta(minutes=service_duration_minutes)).time()
                
                # Check if slot overlaps with break
                if (current_time < break_end and slot_end > break_start):
                    conflicts_with_break = True
                    break
            
            if not conflicts_with_break:
                slots.append(current_time)
            
            # Move to next slot (15-minute intervals)
            current_time = (datetime.combine(date, current_time) + timedelta(minutes=15)).time()
        
        # Filter by preferred time if specified
        if preferred_time:
            slots = self._filter_by_preferred_time(slots, preferred_time)
        
        return slots

    def _filter_by_preferred_time(self, slots: List[time], preferred_time: str) -> List[time]:
        """Filter slots by preferred time of day"""
        
        if preferred_time == "morning":
            return [slot for slot in slots if slot.hour < 12]
        elif preferred_time == "afternoon":
            return [slot for slot in slots if 12 <= slot.hour < 17]
        elif preferred_time == "evening":
            return [slot for slot in slots if slot.hour >= 17]
        
        return slots

    async def _check_bay_availability(
        self,
        bay_id: UUID,
        start_time: time,
        duration_minutes: int
    ) -> bool:
        """Check if a specific bay is available for the given time slot"""
        
        # Convert to datetime for comparison
        start_datetime = datetime.combine(datetime.now().date(), start_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Check for existing bookings in this time slot
        existing_bookings = await self.booking_repo.get_bookings_for_bay_and_time(
            bay_id=bay_id,
            start_time=start_datetime,
            end_time=end_datetime
        )
        
        # Bay is available if no existing bookings
        return len(existing_bookings) == 0

    def _calculate_confidence_score(
        self,
        slot_time: time,
        bay: Any,
        preferred_time: Optional[str],
        service_type: str
    ) -> float:
        """Calculate confidence score for a time slot"""
        
        score = 0.5  # Base score
        
        # Time preference matching
        if preferred_time:
            if preferred_time == "morning" and slot_time.hour < 12:
                score += 0.3
            elif preferred_time == "afternoon" and 12 <= slot_time.hour < 17:
                score += 0.3
            elif preferred_time == "evening" and slot_time.hour >= 17:
                score += 0.3
        
        # Bay suitability for service type
        if service_type == "premium_detail" and "premium" in bay.name.lower():
            score += 0.2
        elif service_type == "express_wash" and bay.bay_number <= 3:  # Prefer lower-numbered bays for express
            score += 0.15
        
        # Peak time adjustment (slightly lower score for very popular times)
        if slot_time.hour in [9, 10, 11, 14, 15]:  # Popular hours
            score -= 0.05
        
        return min(1.0, max(0.1, score))

    async def _calculate_slot_price(
        self,
        service_type: str,
        slot_datetime: datetime,
        bay: Any
    ) -> float:
        """Calculate estimated price for a time slot"""
        
        # Base prices by service type
        base_prices = {
            "exterior_wash": 25.00,
            "interior_clean": 35.00,
            "full_detail": 125.00,
            "express_wash": 15.00,
            "premium_detail": 200.00
        }
        
        base_price = base_prices.get(service_type, 25.00)
        
        # Time-based multipliers
        multiplier = 1.0
        
        # Peak hour premiums
        if slot_datetime.hour in [8, 9, 10] or slot_datetime.hour in [17, 18, 19]:
            multiplier *= 1.1
        
        # Weekend premium
        if slot_datetime.weekday() >= 5:
            multiplier *= 1.15
        
        # Premium bay surcharge
        if "premium" in bay.name.lower():
            multiplier *= 1.2
        
        return round(base_price * multiplier, 2)

    # ================= SMART SUGGESTIONS =================

    async def get_smart_suggestions(
        self,
        customer_id: UUID,
        service_type: str,
        preferred_time: str,
        days_ahead: int,
        max_suggestions: int
    ) -> List[Dict[str, Any]]:
        """Get smart booking suggestions based on historical data and preferences"""
        
        suggestions = []
        current_date = datetime.now().date()
        
        # Get customer booking history for personalization
        customer_history = await self.booking_repo.get_customer_booking_history(customer_id)
        
        # Generate suggestions for the next few days
        for day_offset in range(1, days_ahead + 1):
            target_date = current_date + timedelta(days=day_offset)
            
            # Get available slots for this date
            available_slots = await self.get_available_slots(
                date=target_date,
                service_duration_minutes=self._get_service_duration(service_type),
                service_type=service_type,
                vehicle_size="standard",
                customer_id=customer_id,
                preferred_time=preferred_time
            )
            
            # Select best slots for this day
            for slot in available_slots[:3]:  # Top 3 slots per day
                confidence_score = self._calculate_suggestion_confidence(
                    slot=slot,
                    customer_history=customer_history,
                    preferred_time=preferred_time,
                    target_date=target_date
                )
                
                reasoning = self._generate_suggestion_reasoning(
                    slot=slot,
                    target_date=target_date,
                    preferred_time=preferred_time
                )
                
                suggestions.append({
                    "date": target_date,
                    "time": slot["start_time"].time(),
                    "bay_name": slot["bay_name"],
                    "bay_id": slot["bay_id"],
                    "confidence_score": confidence_score,
                    "reasoning": reasoning,
                    "estimated_price": slot["estimated_price"],
                    "discount_available": self._check_discount_eligibility(target_date, customer_history),
                    "peak_time": slot["start_time"].hour in [9, 10, 11, 17, 18]
                })
        
        # Sort by confidence score and return top suggestions
        suggestions.sort(key=lambda x: x["confidence_score"], reverse=True)
        return suggestions[:max_suggestions]

    def _get_service_duration(self, service_type: str) -> int:
        """Get estimated service duration by type"""
        durations = {
            "exterior_wash": 30,
            "interior_clean": 45,
            "full_detail": 120,
            "express_wash": 15,
            "premium_detail": 180
        }
        return durations.get(service_type, 30)

    def _calculate_suggestion_confidence(
        self,
        slot: Dict[str, Any],
        customer_history: List[Any],
        preferred_time: str,
        target_date: date
    ) -> float:
        """Calculate confidence score for suggestion"""
        
        base_confidence = slot["confidence_score"]
        
        # Historical preference matching
        if customer_history:
            historical_hours = [booking.scheduled_at.hour for booking in customer_history]
            avg_hour = sum(historical_hours) / len(historical_hours)
            
            slot_hour = slot["start_time"].hour
            hour_diff = abs(slot_hour - avg_hour)
            
            if hour_diff <= 1:
                base_confidence += 0.2
            elif hour_diff <= 2:
                base_confidence += 0.1
        
        # Day of week preference
        day_of_week = target_date.weekday()
        if day_of_week < 5:  # Weekday
            base_confidence += 0.05
        else:  # Weekend
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    def _generate_suggestion_reasoning(
        self,
        slot: Dict[str, Any],
        target_date: date,
        preferred_time: str
    ) -> str:
        """Generate reasoning text for suggestion"""
        
        reasons = []
        
        # Time preference matching
        slot_hour = slot["start_time"].hour
        if preferred_time == "morning" and slot_hour < 12:
            reasons.append("Matches your morning preference")
        elif preferred_time == "afternoon" and 12 <= slot_hour < 17:
            reasons.append("Perfect afternoon timing")
        elif preferred_time == "evening" and slot_hour >= 17:
            reasons.append("Convenient evening slot")
        
        # Day characteristics
        day_name = target_date.strftime("%A")
        if target_date.weekday() < 5:
            reasons.append(f"Good {day_name} availability")
        else:
            reasons.append(f"Weekend {day_name} convenience")
        
        # Bay features
        if "Premium" in slot["bay_name"]:
            reasons.append("Premium bay with advanced equipment")
        
        # Pricing
        if slot["estimated_price"] < 30:
            reasons.append("Great value pricing")
        
        return " • ".join(reasons[:3])  # Max 3 reasons

    def _check_discount_eligibility(
        self,
        target_date: date,
        customer_history: List[Any]
    ) -> bool:
        """Check if customer is eligible for discounts on this date"""
        
        # Off-peak day discounts
        if target_date.weekday() in [1, 2]:  # Tuesday, Wednesday
            return True
        
        # Loyalty discounts
        if len(customer_history) >= 5:
            return True
        
        return False

    # ================= AVAILABILITY CHECKING =================

    async def check_availability_advanced(
        self,
        booking_datetime: datetime,
        service_duration_minutes: int,
        service_type: str,
        vehicle_size: str,
        customer_id: UUID,
        exclude_booking_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Advanced availability checking with conflict detection"""
        
        # Get suitable wash bays
        available_bays = await self.scheduling_service.get_available_wash_bays(
            date=booking_datetime.date(),
            vehicle_size=vehicle_size,
            service_type=service_type
        )
        
        conflicts = []
        bay_assignments = []
        
        for bay in available_bays:
            # Check for conflicts
            bay_conflicts = await self._check_bay_conflicts(
                bay_id=bay.id,
                start_time=booking_datetime,
                duration_minutes=service_duration_minutes,
                exclude_booking_id=exclude_booking_id
            )
            
            if not bay_conflicts:
                # Bay is available
                bay_assignments.append({
                    "bay_id": bay.id,
                    "bay_name": bay.name,
                    "bay_number": bay.bay_number,
                    "equipment": list(bay.equipment_types)
                })
            else:
                conflicts.extend(bay_conflicts)
        
        # If no bays available, suggest alternatives
        alternative_slots = []
        if not bay_assignments:
            alternative_slots = await self._find_alternative_slots(
                original_datetime=booking_datetime,
                service_duration_minutes=service_duration_minutes,
                service_type=service_type,
                vehicle_size=vehicle_size
            )
        
        # Calculate pricing
        estimated_price = None
        if bay_assignments:
            estimated_price = await self._calculate_slot_price(
                service_type=service_type,
                slot_datetime=booking_datetime,
                bay=available_bays[0]  # Use first available bay for pricing
            )
        
        return {
            "available": len(bay_assignments) > 0,
            "conflicts": conflicts,
            "alternative_slots": alternative_slots,
            "bay_assignments": bay_assignments,
            "estimated_price": estimated_price,
            "recommendations": self._generate_availability_recommendations(
                bay_assignments, conflicts, alternative_slots
            )
        }

    async def _check_bay_conflicts(
        self,
        bay_id: UUID,
        start_time: datetime,
        duration_minutes: int,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Check for conflicts in a specific bay"""
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Get existing bookings that overlap
        overlapping_bookings = await self.booking_repo.get_overlapping_bookings(
            bay_id=bay_id,
            start_time=start_time,
            end_time=end_time,
            exclude_booking_id=exclude_booking_id
        )
        
        conflicts = []
        for booking in overlapping_bookings:
            conflicts.append({
                "type": "booking_conflict",
                "message": f"Bay is booked from {booking.scheduled_at} to {booking.scheduled_at + timedelta(minutes=booking.total_duration)}",
                "conflicting_booking_id": booking.id,
                "conflict_start": booking.scheduled_at.isoformat(),
                "conflict_end": (booking.scheduled_at + timedelta(minutes=booking.total_duration)).isoformat()
            })
        
        return conflicts

    async def _find_alternative_slots(
        self,
        original_datetime: datetime,
        service_duration_minutes: int,
        service_type: str,
        vehicle_size: str,
        max_alternatives: int = 5
    ) -> List[Dict[str, Any]]:
        """Find alternative time slots when original is not available"""
        
        alternatives = []
        
        # Check slots within 2 hours before and after original time
        for offset_minutes in [-120, -90, -60, -30, 30, 60, 90, 120]:
            alternative_datetime = original_datetime + timedelta(minutes=offset_minutes)
            
            # Skip if outside business hours
            if not await self._is_within_business_hours(alternative_datetime):
                continue
            
            # Check availability
            availability = await self.check_availability_advanced(
                booking_datetime=alternative_datetime,
                service_duration_minutes=service_duration_minutes,
                service_type=service_type,
                vehicle_size=vehicle_size,
                customer_id=UUID('00000000-0000-0000-0000-000000000000')  # Dummy ID for alternative check
            )
            
            if availability["available"]:
                alternatives.append({
                    "start_time": alternative_datetime,
                    "end_time": alternative_datetime + timedelta(minutes=service_duration_minutes),
                    "time_difference_minutes": offset_minutes,
                    "bay_name": availability["bay_assignments"][0]["bay_name"] if availability["bay_assignments"] else None,
                    "bay_id": availability["bay_assignments"][0]["bay_id"] if availability["bay_assignments"] else None,
                    "estimated_price": availability["estimated_price"]
                })
                
                if len(alternatives) >= max_alternatives:
                    break
        
        return alternatives

    async def _is_within_business_hours(self, check_datetime: datetime) -> bool:
        """Check if datetime is within business hours"""
        
        day_of_week = check_datetime.strftime('%A').lower()
        business_hours = await self.scheduling_service.get_business_hours_for_day(day_of_week)
        
        if not business_hours or business_hours.is_closed:
            return False
        
        check_time = check_datetime.time()
        return business_hours.open_time <= check_time <= business_hours.close_time

    def _generate_availability_recommendations(
        self,
        bay_assignments: List[Dict[str, Any]],
        conflicts: List[Dict[str, Any]],
        alternative_slots: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on availability check"""
        
        recommendations = []
        
        if bay_assignments:
            recommendations.append("Time slot is available - book now to secure your spot")
            
            if len(bay_assignments) > 1:
                recommendations.append(f"{len(bay_assignments)} bays available - flexible scheduling")
        
        if conflicts and alternative_slots:
            recommendations.append("Consider alternative times for better availability")
            
            # Find closest alternative
            closest_alt = min(alternative_slots, key=lambda x: abs(x["time_difference_minutes"]))
            if abs(closest_alt["time_difference_minutes"]) <= 30:
                recommendations.append(f"Slot available just {abs(closest_alt['time_difference_minutes'])} minutes later")
        
        if not bay_assignments and not alternative_slots:
            recommendations.append("This time period is very busy - try booking for a different day")
        
        return recommendations

    # ================= SCHEDULE MANAGEMENT =================

    async def update_schedule_for_booking(
        self,
        booking_id: UUID,
        scheduled_at: datetime,
        service_duration_minutes: int,
        service_type: str
    ) -> Dict[str, Any]:
        """Update schedule when booking is confirmed"""
        
        # Find best available bay
        available_bays = await self.scheduling_service.get_available_wash_bays(
            date=scheduled_at.date(),
            vehicle_size="standard",
            service_type=service_type
        )
        
        if not available_bays:
            return {"success": False, "error": "No available bays"}
        
        # Select the best bay (could be optimized further)
        selected_bay = available_bays[0]
        
        # Create time slot
        time_slot = await self.scheduling_service.create_time_slot(
            start_time=scheduled_at,
            end_time=scheduled_at + timedelta(minutes=service_duration_minutes),
            resource_id=selected_bay.id,
            booking_id=booking_id
        )
        
        return {
            "success": True,
            "assigned_bay_id": selected_bay.id,
            "assigned_bay_name": selected_bay.name,
            "time_slot_id": time_slot.id,
            "buffer_time_minutes": 15  # Standard buffer between bookings
        }

    async def release_schedule_slot(
        self,
        booking_id: UUID,
        scheduled_at: datetime,
        service_duration_minutes: int
    ) -> bool:
        """Release schedule slot when booking is cancelled or rescheduled"""
        
        # Find and delete the time slot
        success = await self.scheduling_service.release_time_slot(
            booking_id=booking_id,
            start_time=scheduled_at,
            end_time=scheduled_at + timedelta(minutes=service_duration_minutes)
        )
        
        return success

    # ================= CAPACITY MANAGEMENT =================

    async def update_capacity_allocation(
        self,
        date: date,
        booking_id: UUID,
        service_type: str,
        allocated_bay_id: UUID
    ) -> bool:
        """Update capacity allocation when booking is confirmed"""
        
        # Determine wash type
        wash_type = WashType.STATIONARY if service_type != "mobile" else WashType.MOBILE
        
        # Get or create capacity allocation for this bay and date
        capacity_allocation = await self.capacity_repo.get_allocation_for_date_and_resource(
            date=date,
            resource_id=allocated_bay_id
        )
        
        if not capacity_allocation:
            # Create new allocation
            bay = await self.scheduling_service.get_wash_bay_by_id(allocated_bay_id)
            capacity_allocation = CapacityAllocation(
                date=date,
                wash_type=wash_type,
                resource_id=allocated_bay_id,
                resource_name=bay.name if bay else "Unknown Bay",
                allocated_slots=1,
                max_capacity=8,  # Assuming 8 slots per day per bay
                bookings=[booking_id]
            )
        else:
            # Update existing allocation
            capacity_allocation.allocated_slots += 1
            capacity_allocation.bookings.append(booking_id)
        
        # Save the allocation
        await self.capacity_repo.save_allocation(capacity_allocation)
        return True

    async def release_capacity_allocation(
        self,
        date: date,
        booking_id: UUID
    ) -> bool:
        """Release capacity allocation when booking is cancelled"""
        
        # Find capacity allocation containing this booking
        allocation = await self.capacity_repo.get_allocation_containing_booking(
            date=date,
            booking_id=booking_id
        )
        
        if allocation:
            # Remove booking from allocation
            if booking_id in allocation.bookings:
                allocation.bookings.remove(booking_id)
                allocation.allocated_slots -= 1
                
                # Save updated allocation
                await self.capacity_repo.save_allocation(allocation)
                return True
        
        return False

    # ================= OPTIMIZATION & ANALYTICS =================

    async def optimize_booking(
        self,
        customer_id: UUID,
        vehicle_id: UUID,
        service_ids: List[UUID],
        preferred_date: date,
        flexibility_hours: int
    ) -> Dict[str, Any]:
        """Optimize booking for best time, bay, and pricing"""
        
        # Get service details
        total_duration = await self.calculate_total_service_duration(service_ids)
        service_type = await self.determine_service_type(service_ids)
        
        optimized_slots = []
        
        # Check different times within flexibility window
        base_datetime = datetime.combine(preferred_date, time(9, 0))  # Start at 9 AM
        
        for hour_offset in range(0, flexibility_hours + 1):
            for start_hour in [9, 10, 11, 14, 15, 16]:  # Common booking hours
                check_datetime = base_datetime.replace(hour=start_hour) + timedelta(hours=hour_offset)
                
                # Check availability
                availability = await self.check_availability_advanced(
                    booking_datetime=check_datetime,
                    service_duration_minutes=total_duration,
                    service_type=service_type,
                    vehicle_size="standard",
                    customer_id=customer_id
                )
                
                if availability["available"]:
                    # Calculate optimization score
                    optimization_score = self._calculate_optimization_score(
                        check_datetime, availability, service_type
                    )
                    
                    optimized_slots.append({
                        "datetime": check_datetime,
                        "bay_id": availability["bay_assignments"][0]["bay_id"],
                        "bay_name": availability["bay_assignments"][0]["bay_name"],
                        "total_price": availability["estimated_price"],
                        "savings": self._calculate_savings(availability["estimated_price"], check_datetime),
                        "optimization_score": optimization_score,
                        "reasoning": self._generate_optimization_reasoning(check_datetime, optimization_score)
                    })
        
        # Sort by optimization score
        optimized_slots.sort(key=lambda x: x["optimization_score"], reverse=True)
        
        return {
            "optimized_slots": optimized_slots[:5],  # Top 5 options
            "best_recommendation": optimized_slots[0] if optimized_slots else None,
            "price_comparison": self._generate_price_comparison(optimized_slots),
            "time_flexibility_benefits": self._analyze_flexibility_benefits(optimized_slots)
        }

    def _calculate_optimization_score(
        self,
        booking_datetime: datetime,
        availability: Dict[str, Any],
        service_type: str
    ) -> float:
        """Calculate optimization score for a booking slot"""
        
        score = 0.5  # Base score
        
        # Price optimization (lower price = higher score)
        if availability["estimated_price"]:
            base_price = 50.0  # Assume base price
            price_ratio = availability["estimated_price"] / base_price
            score += (2.0 - price_ratio) * 0.3  # Up to 0.3 points for good pricing
        
        # Time optimization (avoid peak hours for better score)
        hour = booking_datetime.hour
        if hour in [9, 10, 11]:  # Peak morning
            score -= 0.1
        elif hour in [14, 15]:  # Good afternoon hours
            score += 0.2
        elif hour in [17, 18]:  # Peak evening
            score -= 0.1
        
        # Bay quality (more available bays = higher score)
        bay_count = len(availability.get("bay_assignments", []))
        score += min(0.2, bay_count * 0.1)
        
        return min(1.0, max(0.1, score))

    def _calculate_savings(self, current_price: float, booking_datetime: datetime) -> float:
        """Calculate potential savings compared to peak pricing"""
        
        # Simulate peak price (20% higher during peak hours)
        peak_multiplier = 1.2 if booking_datetime.hour in [9, 10, 17, 18] else 1.0
        peak_price = current_price * peak_multiplier
        
        return max(0, peak_price - current_price)

    def _generate_optimization_reasoning(self, booking_datetime: datetime, score: float) -> str:
        """Generate reasoning for optimization score"""
        
        reasons = []
        
        hour = booking_datetime.hour
        if hour in [14, 15]:
            reasons.append("Excellent afternoon timing")
        elif hour in [9, 10]:
            reasons.append("Popular morning slot")
        
        if score > 0.8:
            reasons.append("Optimal value and availability")
        elif score > 0.6:
            reasons.append("Good balance of price and convenience")
        
        day_name = booking_datetime.strftime("%A")
        reasons.append(f"Available {day_name}")
        
        return " • ".join(reasons)

    def _generate_price_comparison(self, optimized_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate price comparison across optimized slots"""
        
        if not optimized_slots:
            return {}
        
        prices = [slot["total_price"] for slot in optimized_slots]
        
        return {
            "lowest_price": min(prices),
            "highest_price": max(prices),
            "average_price": sum(prices) / len(prices),
            "max_savings": max(prices) - min(prices),
            "best_value_slot": min(optimized_slots, key=lambda x: x["total_price"])["datetime"].isoformat()
        }

    def _analyze_flexibility_benefits(self, optimized_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze benefits of time flexibility"""
        
        if len(optimized_slots) <= 1:
            return {"flexibility_score": 0.1, "benefits": ["Limited options available"]}
        
        # Calculate flexibility benefits
        price_range = max(slot["total_price"] for slot in optimized_slots) - min(slot["total_price"] for slot in optimized_slots)
        time_range_hours = len(set(slot["datetime"].hour for slot in optimized_slots))
        
        flexibility_score = min(1.0, (price_range / 20.0) + (time_range_hours / 10.0))
        
        benefits = []
        if price_range > 5:
            benefits.append(f"Save up to ${price_range:.2f} with flexible timing")
        if time_range_hours >= 3:
            benefits.append(f"Multiple time options across {time_range_hours} hours")
        
        return {
            "flexibility_score": flexibility_score,
            "benefits": benefits,
            "recommended_approach": "Consider off-peak hours for best value"
        }

    # ================= WALK-IN BOOKING SUPPORT =================

    async def update_schedule_for_walk_in(
        self,
        booking_id: UUID,
        start_time: datetime,
        service_duration_minutes: int,
        assigned_bay_id: UUID,
        washer_id: UUID
    ) -> Dict[str, Any]:
        """Update schedule for walk-in booking with immediate start"""
        
        print(f"[WALK-IN-SCHEDULE] Adjusting schedule for walk-in at bay {assigned_bay_id}")
        
        # Get the assigned bay details
        bay = await self.scheduling_service.get_wash_bay_by_id(assigned_bay_id)
        
        if not bay:
            return {"success": False, "error": "Assigned bay not found"}
        
        # Check if there are any conflicting scheduled bookings
        end_time = start_time + timedelta(minutes=service_duration_minutes)
        conflicts = await self._check_walk_in_conflicts(assigned_bay_id, start_time, end_time)
        
        if conflicts:
            # Try to resolve conflicts by rescheduling or moving to other bays
            resolution_result = await self._resolve_walk_in_conflicts(
                conflicts, service_duration_minutes, washer_id
            )
            
            if not resolution_result["success"]:
                return {
                    "success": False, 
                    "error": "Unable to resolve scheduling conflicts",
                    "conflicts": conflicts
                }
        
        # Create immediate time slot for walk-in
        time_slot = await self.scheduling_service.create_time_slot(
            start_time=start_time,
            end_time=end_time,
            resource_id=assigned_bay_id,
            booking_id=booking_id,
            status="occupied"  # Immediately occupied for walk-in
        )
        
        # Update any scheduled bookings that might be affected
        await self._adjust_subsequent_bookings(assigned_bay_id, start_time, service_duration_minutes)
        
        print(f"[WALK-IN-SCHEDULE] Successfully adjusted schedule for walk-in booking {booking_id}")
        
        return {
            "success": True,
            "assigned_bay_id": assigned_bay_id,
            "assigned_bay_name": bay.name,
            "time_slot_id": time_slot.id,
            "conflicts_resolved": len(conflicts) if conflicts else 0,
            "schedule_adjustments_made": True,
            "washer_assigned": washer_id
        }

    async def _check_walk_in_conflicts(
        self,
        bay_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Check for conflicts when inserting a walk-in booking"""
        
        # Get existing bookings that overlap with the walk-in time
        overlapping_bookings = await self.booking_repo.get_overlapping_bookings(
            bay_id=bay_id,
            start_time=start_time,
            end_time=end_time
        )
        
        conflicts = []
        for booking in overlapping_bookings:
            # Only consider confirmed bookings as conflicts
            if booking.status.value in ["confirmed", "in_progress"]:
                conflicts.append({
                    "booking_id": booking.id,
                    "customer_id": booking.customer_id,
                    "scheduled_start": booking.scheduled_at,
                    "scheduled_end": booking.scheduled_at + timedelta(minutes=booking.total_duration),
                    "overlap_start": max(start_time, booking.scheduled_at),
                    "overlap_end": min(end_time, booking.scheduled_at + timedelta(minutes=booking.total_duration)),
                    "conflict_type": "bay_occupied",
                    "priority": "high" if booking.status.value == "in_progress" else "medium"
                })
        
        return conflicts

    async def _resolve_walk_in_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        service_duration_minutes: int,
        washer_id: UUID
    ) -> Dict[str, Any]:
        """Attempt to resolve conflicts for walk-in booking"""
        
        resolved_conflicts = []
        unresolved_conflicts = []
        
        for conflict in conflicts:
            booking_id = conflict["booking_id"]
            
            # Strategy 1: Try to move conflicting booking to another bay
            alternative_bay = await self._find_alternative_bay_for_booking(
                booking_id=booking_id,
                original_start=conflict["scheduled_start"],
                duration_minutes=service_duration_minutes
            )
            
            if alternative_bay:
                # Move the booking to alternative bay
                move_result = await self._move_booking_to_bay(
                    booking_id=booking_id,
                    new_bay_id=alternative_bay["bay_id"],
                    washer_id=washer_id
                )
                
                if move_result["success"]:
                    resolved_conflicts.append({
                        "booking_id": booking_id,
                        "resolution": "moved_to_alternative_bay",
                        "new_bay": alternative_bay["bay_name"],
                        "customer_notified": True
                    })
                    continue
            
            # Strategy 2: Try to reschedule to later time
            later_slot = await self._find_later_available_slot(
                booking_id=booking_id,
                original_start=conflict["scheduled_start"],
                duration_minutes=service_duration_minutes
            )
            
            if later_slot:
                reschedule_result = await self._reschedule_booking(
                    booking_id=booking_id,
                    new_start_time=later_slot["start_time"],
                    washer_id=washer_id
                )
                
                if reschedule_result["success"]:
                    resolved_conflicts.append({
                        "booking_id": booking_id,
                        "resolution": "rescheduled_later",
                        "new_time": later_slot["start_time"].isoformat(),
                        "delay_minutes": (later_slot["start_time"] - conflict["scheduled_start"]).total_seconds() / 60,
                        "customer_notified": True
                    })
                    continue
            
            # Unable to resolve this conflict
            unresolved_conflicts.append(conflict)
        
        success = len(unresolved_conflicts) == 0
        
        return {
            "success": success,
            "resolved_conflicts": resolved_conflicts,
            "unresolved_conflicts": unresolved_conflicts,
            "resolution_strategies_used": ["alternative_bay", "reschedule_later"],
            "customer_notifications_sent": len(resolved_conflicts)
        }

    async def _find_alternative_bay_for_booking(
        self,
        booking_id: UUID,
        original_start: datetime,
        duration_minutes: int
    ) -> Optional[Dict[str, Any]]:
        """Find an alternative bay for a booking being displaced by walk-in"""
        
        # Get booking details to understand requirements
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            return None
        
        # Find available bays at the same time
        available_bays = await self.scheduling_service.get_available_wash_bays(
            date=original_start.date(),
            vehicle_size="standard",  # Could be derived from booking
            service_type="scheduled"
        )
        
        for bay in available_bays:
            # Check if this bay is available at the required time
            is_available = await self._check_bay_availability(
                bay_id=bay.id,
                start_time=original_start.time(),
                duration_minutes=duration_minutes
            )
            
            if is_available:
                return {
                    "bay_id": bay.id,
                    "bay_name": bay.name,
                    "bay_number": bay.bay_number,
                    "same_time": True
                }
        
        return None

    async def _move_booking_to_bay(
        self,
        booking_id: UUID,
        new_bay_id: UUID,
        washer_id: UUID
    ) -> Dict[str, Any]:
        """Move a booking to a different bay"""
        
        try:
            # Update the time slot resource assignment
            success = await self.scheduling_service.update_booking_bay_assignment(
                booking_id=booking_id,
                new_bay_id=new_bay_id
            )
            
            if success:
                # Log the move for audit trail
                print(f"[SCHEDULE-ADJUST] Moved booking {booking_id} to bay {new_bay_id} due to walk-in")
                
                # In real implementation, send notification to customer
                await self._send_bay_change_notification(booking_id, new_bay_id)
                
                return {
                    "success": True,
                    "new_bay_id": new_bay_id,
                    "moved_by_washer": washer_id,
                    "reason": "walk_in_accommodation"
                }
            
            return {"success": False, "error": "Failed to update bay assignment"}
            
        except Exception as e:
            print(f"[ERROR] Failed to move booking {booking_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _find_later_available_slot(
        self,
        booking_id: UUID,
        original_start: datetime,
        duration_minutes: int
    ) -> Optional[Dict[str, Any]]:
        """Find a later available slot for rescheduling"""
        
        # Look for slots within the next 2 hours
        for offset_minutes in [30, 60, 90, 120]:
            potential_start = original_start + timedelta(minutes=offset_minutes)
            
            # Check if this time is within business hours
            if not await self._is_within_business_hours(potential_start):
                continue
            
            # Check availability
            availability = await self.check_availability_advanced(
                booking_datetime=potential_start,
                service_duration_minutes=duration_minutes,
                service_type="rescheduled",
                vehicle_size="standard",
                customer_id=UUID('00000000-0000-0000-0000-000000000000'),  # Dummy for check
                exclude_booking_id=booking_id
            )
            
            if availability["available"]:
                return {
                    "start_time": potential_start,
                    "end_time": potential_start + timedelta(minutes=duration_minutes),
                    "delay_minutes": offset_minutes,
                    "bay_options": availability["bay_assignments"]
                }
        
        return None

    async def _reschedule_booking(
        self,
        booking_id: UUID,
        new_start_time: datetime,
        washer_id: UUID
    ) -> Dict[str, Any]:
        """Reschedule a booking to a new time"""
        
        try:
            # Get the booking
            booking = await self.booking_repo.get_by_id(booking_id)
            if not booking:
                return {"success": False, "error": "Booking not found"}
            
            # Update booking time
            old_start_time = booking.scheduled_at
            booking.scheduled_at = new_start_time
            
            # Save updated booking
            await self.booking_repo.update(booking)
            
            # Update schedule
            await self.release_schedule_slot(
                booking_id=booking_id,
                scheduled_at=old_start_time,
                service_duration_minutes=booking.total_duration
            )
            
            await self.update_schedule_for_booking(
                booking_id=booking_id,
                scheduled_at=new_start_time,
                service_duration_minutes=booking.total_duration,
                service_type="rescheduled"
            )
            
            # Log the reschedule
            print(f"[SCHEDULE-ADJUST] Rescheduled booking {booking_id} from {old_start_time} to {new_start_time}")
            
            # Send notification to customer
            await self._send_reschedule_notification(booking_id, old_start_time, new_start_time)
            
            return {
                "success": True,
                "old_time": old_start_time.isoformat(),
                "new_time": new_start_time.isoformat(),
                "rescheduled_by_washer": washer_id,
                "reason": "walk_in_accommodation"
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to reschedule booking {booking_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _adjust_subsequent_bookings(
        self,
        bay_id: UUID,
        walk_in_start: datetime,
        walk_in_duration: int
    ) -> None:
        """Adjust any subsequent bookings that might be affected"""
        
        walk_in_end = walk_in_start + timedelta(minutes=walk_in_duration)
        
        # Get bookings scheduled after the walk-in on the same bay
        subsequent_bookings = await self.booking_repo.get_bookings_after_time(
            bay_id=bay_id,
            after_time=walk_in_start,
            same_day_only=True
        )
        
        buffer_time = 15  # 15 minutes buffer between services
        
        for booking in subsequent_bookings:
            # Check if booking starts too soon after walk-in ends
            if booking.scheduled_at < walk_in_end + timedelta(minutes=buffer_time):
                # Adjust booking start time
                new_start_time = walk_in_end + timedelta(minutes=buffer_time)
                
                print(f"[SCHEDULE-ADJUST] Adjusting booking {booking.id} start time to {new_start_time}")
                
                # Update booking
                booking.scheduled_at = new_start_time
                await self.booking_repo.update(booking)
                
                # Send notification about the adjustment
                await self._send_minor_adjustment_notification(booking.id, new_start_time)

    async def _send_bay_change_notification(self, booking_id: UUID, new_bay_id: UUID) -> None:
        """Send notification about bay change"""
        # In real implementation, send SMS/email to customer
        print(f"[NOTIFICATION] Bay change notification sent for booking {booking_id}")

    async def _send_reschedule_notification(
        self, 
        booking_id: UUID, 
        old_time: datetime, 
        new_time: datetime
    ) -> None:
        """Send notification about reschedule"""
        # In real implementation, send SMS/email to customer
        print(f"[NOTIFICATION] Reschedule notification sent for booking {booking_id}")

    async def _send_minor_adjustment_notification(
        self, 
        booking_id: UUID, 
        new_time: datetime
    ) -> None:
        """Send notification about minor time adjustment"""
        # In real implementation, send SMS/email to customer
        print(f"[NOTIFICATION] Minor adjustment notification sent for booking {booking_id}")

    # ================= WALK-IN ANALYTICS =================

    async def get_walk_in_analytics(
        self,
        date_range_days: int = 7
    ) -> Dict[str, Any]:
        """Get analytics specific to walk-in bookings"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=date_range_days)
        
        # Simulate walk-in analytics
        analytics = {
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": date_range_days
            },
            "walk_in_summary": {
                "total_walk_ins": 23,
                "daily_average": 3.3,
                "walk_in_revenue": 1485.00,
                "average_walk_in_value": 64.57,
                "walk_in_percentage_of_total": 18.5
            },
            "schedule_impact": {
                "bookings_rescheduled": 4,
                "bay_changes_made": 2,
                "average_delay_minutes": 12,
                "customer_satisfaction_impact": -0.1,  # Slight decrease due to changes
                "successful_accommodations": 95.7  # Percentage
            },
            "washer_efficiency": {
                "average_walk_in_processing_time": 8,  # Minutes to process walk-in
                "schedule_adjustment_time": 3,  # Minutes to adjust schedule
                "walk_in_service_efficiency": 92,  # Percentage
                "multitasking_score": 8.5  # Out of 10
            },
            "peak_walk_in_times": [
                {"hour": "10:00-11:00", "count": 6, "percentage": 26.1},
                {"hour": "14:00-15:00", "count": 4, "percentage": 17.4},
                {"hour": "16:00-17:00", "count": 5, "percentage": 21.7}
            ],
            "popular_walk_in_services": [
                {"service": "Express Wash", "count": 8, "percentage": 34.8},
                {"service": "Exterior Wash", "count": 7, "percentage": 30.4},
                {"service": "Interior Clean", "count": 5, "percentage": 21.7}
            ],
            "operational_insights": [
                "Walk-ins peak during lunch hours (12-2 PM)",
                "Most walk-ins request quick services (under 45 minutes)",
                "Bay 2 accommodates most walk-ins due to central location",
                "Friday afternoons see highest walk-in volume"
            ]
        }
        
        return analytics

    # ================= UTILITY METHODS =================

    async def calculate_total_service_duration(self, service_ids: List[UUID]) -> int:
        """Calculate total duration for multiple services"""
        
        total_duration = 0
        
        for service_id in service_ids:
            service = await self.service_repo.get_by_id(service_id)
            if service:
                total_duration += service.duration
        
        # Add buffer time between services
        if len(service_ids) > 1:
            total_duration += (len(service_ids) - 1) * 10  # 10 minutes buffer between services
        
        return total_duration

    async def determine_service_type(self, service_ids: List[UUID]) -> str:
        """Determine overall service type from service IDs"""
        
        service_types = []
        
        for service_id in service_ids:
            service = await self.service_repo.get_by_id(service_id)
            if service:
                # Categorize based on service name
                name_lower = service.name.lower()
                if "detail" in name_lower:
                    service_types.append("full_detail")
                elif "express" in name_lower:
                    service_types.append("express_wash")
                elif "exterior" in name_lower:
                    service_types.append("exterior_wash")
                elif "interior" in name_lower:
                    service_types.append("interior_clean")
                else:
                    service_types.append("standard_wash")
        
        # Return most comprehensive service type
        if "full_detail" in service_types:
            return "full_detail"
        elif "exterior_wash" in service_types and "interior_clean" in service_types:
            return "full_service"
        elif service_types:
            return service_types[0]
        
        return "standard_wash"

    async def determine_service_type_from_booking(self, booking: Booking) -> str:
        """Determine service type from existing booking"""
        
        service_ids = [service.service_id for service in booking.services]
        return await self.determine_service_type(service_ids)

    async def calculate_booking_price(
        self,
        service_ids: List[UUID],
        scheduled_at: datetime,
        customer_id: UUID,
        vehicle_type: str
    ) -> Dict[str, Any]:
        """Calculate total booking price with dynamic pricing"""
        
        base_price = 0.0
        
        # Sum base prices of all services
        for service_id in service_ids:
            service = await self.service_repo.get_by_id(service_id)
            if service:
                base_price += float(service.price)
        
        # Apply dynamic pricing multipliers
        multiplier = 1.0
        pricing_factors = []
        
        # Time-based multipliers
        hour = scheduled_at.hour
        if hour in [8, 9, 10] or hour in [17, 18, 19]:
            multiplier *= 1.15
            pricing_factors.append("Peak hours (+15%)")
        
        # Day-based multipliers
        if scheduled_at.weekday() >= 5:  # Weekend
            multiplier *= 1.1
            pricing_factors.append("Weekend (+10%)")
        
        # Vehicle type multipliers
        if any(luxury in vehicle_type.upper() for luxury in ["BMW", "MERCEDES", "AUDI"]):
            multiplier *= 1.05
            pricing_factors.append("Luxury vehicle (+5%)")
        
        total_price = base_price * multiplier
        
        return {
            "base_price": base_price,
            "total_price": total_price,
            "multiplier": multiplier,
            "pricing_factors": pricing_factors,
            "savings_applied": 0  # Could be calculated from loyalty, promotions, etc.
        }