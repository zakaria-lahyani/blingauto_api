"""
Booking application service
"""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from src.shared.utils.timezone_handler import (
    RobustTimezoneHandler, 
    normalize_datetime_for_db, 
    safe_datetime_subtract_hours,
    safe_datetime_compare
)

from src.features.bookings.domain.entities import Booking, BookingService
from src.features.bookings.domain.enums import BookingStatus, BookingType, QualityRating, BookingSortBy
from src.features.bookings.domain.events import (
    BookingCreated, BookingConfirmed, BookingStarted, BookingCompleted,
    BookingCancelled, BookingRescheduled, NoShowDetected, QualityRated
)
from src.features.bookings.infrastructure.database.repositories import BookingRepository, BookingEventRepository
from src.features.services.infrastructure.database.repositories import ServiceRepository


class BookingApplicationService:
    """Application service for booking management"""
    
    def __init__(
        self,
        booking_repo: BookingRepository,
        event_repo: BookingEventRepository,
        service_repo: ServiceRepository
    ):
        self.booking_repo = booking_repo
        self.event_repo = event_repo
        self.service_repo = service_repo
    
    async def create_booking(
        self,
        customer_id: UUID,
        vehicle_id: UUID,
        scheduled_at: datetime,
        service_ids: List[UUID],
        notes: Optional[str] = None,
        booking_type: BookingType = BookingType.IN_HOME,
        vehicle_size: str = "standard",
        customer_location: Optional[dict] = None
    ) -> Booking:
        """Create a new booking"""
        # Normalize scheduled_at for database storage using robust timezone handling
        scheduled_at = normalize_datetime_for_db(scheduled_at)
            
        # Validate and get services
        services = await self._get_booking_services(service_ids)
        
        # Create booking entity
        booking = Booking(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            scheduled_at=scheduled_at,
            services=services,
            notes=notes,
            booking_type=booking_type,
            vehicle_size=vehicle_size,
            customer_location=customer_location
        )
        
        # Save to database
        saved_booking = await self.booking_repo.create(booking)
        
        # Fire domain event
        await self._fire_booking_created_event(saved_booking)
        
        return saved_booking
    
    async def create_booking_with_validation(
        self,
        customer_id: UUID,
        vehicle_id: UUID,
        scheduled_at: datetime,
        service_ids: List[UUID],
        notes: Optional[str] = None,
        booking_type: BookingType = BookingType.IN_HOME,
        vehicle_size: str = "standard",
        customer_location: Optional[dict] = None,
        auto_assign_resource: bool = False
    ) -> Tuple[Booking, List[str]]:
        """Create a new booking with validation and warnings"""
        warnings = []
        
        # Validate vehicle exists
        if not vehicle_id:
            raise ValueError("Vehicle ID is required")
        
        # Validate services exist and are not empty
        if not service_ids:
            raise ValueError("At least one service must be selected")
        
        # Validate scheduled time is in the future using robust timezone handling
        now = RobustTimezoneHandler.now_utc_aware()
        if not safe_datetime_compare(now, scheduled_at):
            raise ValueError("Booking must be scheduled in the future")
        
        # Normalize scheduled_at for database storage
        scheduled_at = normalize_datetime_for_db(scheduled_at)
        
        # Validate and get services
        services = await self._get_booking_services(service_ids)
        
        # Check for scheduling conflicts or warnings using robust timezone handling
        hours_until_booking = safe_datetime_subtract_hours(scheduled_at, RobustTimezoneHandler.now_utc_aware())
        if hours_until_booking is not None and hours_until_booking < 24:
            warnings.append(f"Booking is scheduled within {int(hours_until_booking)} hours. Rush charges may apply.")
        
        # Create booking entity
        booking = Booking(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            scheduled_at=scheduled_at,
            services=services,
            notes=notes,
            booking_type=booking_type,
            vehicle_size=vehicle_size,
            customer_location=customer_location
        )
        
        # Save to database with proper error handling
        try:
            saved_booking = await self.booking_repo.create(booking)
        except Exception as e:
            from sqlalchemy.exc import IntegrityError
            # Handle foreign key constraint violations specifically
            if isinstance(e, IntegrityError):
                error_msg = str(e).lower()
                if "vehicle_id" in error_msg and ("not present" in error_msg or "violates foreign key" in error_msg):
                    raise ValueError("Vehicle not found")
                elif "service" in error_msg and ("not present" in error_msg or "violates foreign key" in error_msg):
                    raise ValueError("One or more services not found")
                else:
                    raise ValueError(f"Data integrity error: {str(e).split('DETAIL:')[0].strip()}")
            else:
                # Re-raise other database errors
                raise e
        
        # Fire domain event
        await self._fire_booking_created_event(saved_booking)
        
        return saved_booking, warnings
    
    async def confirm_booking(self, booking_id: UUID) -> Booking:
        """Confirm a pending booking"""
        booking = await self._get_booking_or_raise(booking_id)
        
        booking.confirm()
        updated_booking = await self.booking_repo.update(booking)
        
        # Fire domain event
        await self._fire_booking_confirmed_event(updated_booking)
        
        return updated_booking
    
    async def start_service(self, booking_id: UUID) -> Booking:
        """Start the service (mark as in progress)"""
        booking = await self._get_booking_or_raise(booking_id)
        
        booking.start_service()
        updated_booking = await self.booking_repo.update(booking)
        
        # Fire domain event
        await self._fire_booking_started_event(updated_booking)
        
        return updated_booking
    
    async def complete_service(
        self,
        booking_id: UUID,
        actual_end_time: Optional[datetime] = None
    ) -> Booking:
        """Complete the service"""
        booking = await self._get_booking_or_raise(booking_id)
        
        booking.complete_service(actual_end_time)
        updated_booking = await self.booking_repo.update(booking)
        
        # Fire domain event
        await self._fire_booking_completed_event(updated_booking)
        
        return updated_booking
    
    async def cancel_booking(
        self,
        booking_id: UUID,
        cancellation_time: Optional[datetime] = None,
        reason: Optional[str] = None
    ) -> Booking:
        """Cancel a booking with fee calculation"""
        booking = await self._get_booking_or_raise(booking_id)
        
        cancel_time = cancellation_time or datetime.now(timezone.utc)
        notice_hours = (booking.scheduled_at - cancel_time).total_seconds() / 3600
        
        booking.cancel(cancel_time)
        updated_booking = await self.booking_repo.update(booking)
        
        # Fire domain event
        await self._fire_booking_cancelled_event(updated_booking, notice_hours, reason)
        
        return updated_booking
    
    async def reschedule_booking(
        self,
        booking_id: UUID,
        new_scheduled_at: datetime
    ) -> Booking:
        """Reschedule a booking to a new time"""
        booking = await self._get_booking_or_raise(booking_id)
        old_scheduled_at = booking.scheduled_at
        
        notice_hours = (new_scheduled_at - datetime.now(timezone.utc)).total_seconds() / 3600
        
        booking.reschedule(new_scheduled_at)
        updated_booking = await self.booking_repo.update(booking)
        
        # Fire domain event
        await self._fire_booking_rescheduled_event(updated_booking, old_scheduled_at, notice_hours)
        
        return updated_booking
    
    async def rate_service_quality(
        self,
        booking_id: UUID,
        rating: QualityRating,
        feedback: Optional[str] = None
    ) -> Booking:
        """Rate the service quality"""
        booking = await self._get_booking_or_raise(booking_id)
        
        booking.rate_quality(rating, feedback)
        updated_booking = await self.booking_repo.update(booking)
        
        # Fire domain event
        await self._fire_quality_rated_event(updated_booking)
        
        return updated_booking
    
    async def add_service_to_booking(
        self,
        booking_id: UUID,
        service_id: UUID
    ) -> Booking:
        """Add a service to an existing booking"""
        booking = await self._get_booking_or_raise(booking_id)
        
        # Get service details
        service_entity = await self.service_repo.get(service_id)
        if not service_entity:
            raise ValueError(f"Service not found: {service_id}")
        
        booking_service = BookingService(
            service_id=service_entity.id,
            service_name=service_entity.name,
            price=service_entity.price,
            duration=service_entity.duration
        )
        
        booking.add_service(booking_service)
        updated_booking = await self.booking_repo.update(booking)
        
        return updated_booking
    
    async def remove_service_from_booking(
        self,
        booking_id: UUID,
        service_id: UUID
    ) -> Booking:
        """Remove a service from an existing booking"""
        booking = await self._get_booking_or_raise(booking_id)
        
        booking.remove_service(service_id)
        updated_booking = await self.booking_repo.update(booking)
        
        return updated_booking
    
    async def get_booking(self, booking_id: UUID) -> Optional[Booking]:
        """Get a booking by ID"""
        return await self.booking_repo.get(booking_id)
    
    async def list_bookings(
        self,
        customer_id: Optional[UUID] = None,
        vehicle_id: Optional[UUID] = None,
        status: Optional[BookingStatus] = None,
        scheduled_date: Optional[datetime] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        search: Optional[str] = None,
        sort_by: BookingSortBy = BookingSortBy.CREATED_AT,
        sort_desc: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Booking], int]:
        """List bookings with filtering and pagination"""
        return await self.booking_repo.list_bookings(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            status=status,
            scheduled_date=scheduled_date,
            date_range=date_range,
            search=search,
            sort_by=sort_by,
            sort_desc=sort_desc,
            page=page,
            page_size=page_size
        )
    
    async def get_customer_bookings(
        self,
        customer_id: UUID,
        status_filter: Optional[List[BookingStatus]] = None,
        limit: int = 10
    ) -> List[Booking]:
        """Get recent bookings for a customer"""
        return await self.booking_repo.get_customer_bookings(
            customer_id=customer_id,
            status_filter=status_filter,
            limit=limit
        )
    
    async def process_no_show_detection(self) -> List[Booking]:
        """Process no-show detection for overdue bookings"""
        # Calculate cutoff time (scheduled time + grace period)
        grace_period = timedelta(minutes=Booking.GRACE_PERIOD_MINUTES)
        cutoff_time = datetime.now(timezone.utc) - grace_period
        
        # Get eligible bookings
        eligible_bookings = await self.booking_repo.get_bookings_for_no_show_check(cutoff_time)
        
        no_show_bookings = []
        for booking in eligible_bookings:
            if booking.is_no_show_eligible():
                booking.mark_no_show()
                updated_booking = await self.booking_repo.update(booking)
                
                # Fire domain event
                await self._fire_no_show_detected_event(updated_booking)
                
                no_show_bookings.append(updated_booking)
        
        return no_show_bookings
    
    async def calculate_cancellation_info(
        self,
        booking_id: UUID,
        cancellation_time: Optional[datetime] = None
    ) -> dict:
        """Calculate cancellation policy and fee for a booking"""
        booking = await self._get_booking_or_raise(booking_id)
        
        cancel_time = cancellation_time or datetime.now(timezone.utc)
        policy = booking.get_cancellation_policy(cancel_time)
        fee = booking._calculate_cancellation_fee(cancel_time)
        notice_hours = (booking.scheduled_at - cancel_time).total_seconds() / 3600
        
        return {
            "policy": policy.value,
            "fee": fee,
            "notice_hours": notice_hours,
            "total_price": booking.total_price
        }
    
    async def get_booking_analytics(
        self,
        customer_id: Optional[UUID] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> dict:
        """Get booking analytics and metrics"""
        if not date_range:
            # Default to last 30 days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
        
        bookings = await self.booking_repo.get_bookings_by_date_range(
            date_range[0], date_range[1]
        )
        
        if customer_id:
            bookings = [b for b in bookings if b.customer_id == customer_id]
        
        # Calculate metrics
        total_bookings = len(bookings)
        completed_bookings = len([b for b in bookings if b.status == BookingStatus.COMPLETED])
        cancelled_bookings = len([b for b in bookings if b.status == BookingStatus.CANCELLED])
        no_show_bookings = len([b for b in bookings if b.status == BookingStatus.NO_SHOW])
        
        total_revenue = sum(b.total_price for b in bookings if b.status == BookingStatus.COMPLETED)
        total_fees = sum(b.cancellation_fee for b in bookings if b.cancellation_fee > 0)
        
        # Quality ratings
        rated_bookings = [b for b in bookings if b.quality_rating is not None]
        avg_rating = None
        if rated_bookings:
            avg_rating = sum(b.quality_rating.value for b in rated_bookings) / len(rated_bookings)
        
        return {
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "no_show_bookings": no_show_bookings,
            "completion_rate": completed_bookings / total_bookings if total_bookings > 0 else 0,
            "cancellation_rate": cancelled_bookings / total_bookings if total_bookings > 0 else 0,
            "no_show_rate": no_show_bookings / total_bookings if total_bookings > 0 else 0,
            "total_revenue": total_revenue,
            "total_fees": total_fees,
            "average_rating": avg_rating,
            "rated_bookings_count": len(rated_bookings),
            "date_range": date_range
        }
    
    async def _get_booking_services(self, service_ids: List[UUID]) -> List[BookingService]:
        """Get and validate booking services"""
        services = []
        for service_id in service_ids:
            service_entity = await self.service_repo.get(service_id)
            if not service_entity:
                raise ValueError(f"Service not found: {service_id}")
            
            if not service_entity.is_active:
                raise ValueError(f"Service is not active: {service_id}")
            
            booking_service = BookingService(
                service_id=service_entity.id,
                service_name=service_entity.name,
                price=service_entity.price,
                duration=service_entity.duration
            )
            services.append(booking_service)
        
        return services
    
    async def _get_booking_or_raise(self, booking_id: UUID) -> Booking:
        """Get booking or raise exception if not found"""
        booking = await self.booking_repo.get(booking_id)
        if not booking:
            raise ValueError(f"Booking not found: {booking_id}")
        return booking
    
    # Event firing methods
    async def _fire_booking_created_event(self, booking: Booking) -> None:
        """Fire booking created event"""
        event = BookingCreated(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            vehicle_id=booking.vehicle_id,
            scheduled_at=booking.scheduled_at,
            service_ids=booking.service_ids,
            total_price=booking.total_price,
            total_duration=booking.total_duration,
            notes=booking.notes
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "vehicle_id": str(event.vehicle_id),
                "scheduled_at": event.scheduled_at.isoformat(),
                "service_ids": [str(sid) for sid in event.service_ids],
                "total_price": str(event.total_price),
                "total_duration": event.total_duration,
                "notes": event.notes
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_booking_confirmed_event(self, booking: Booking) -> None:
        """Fire booking confirmed event"""
        event = BookingConfirmed(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            scheduled_at=booking.scheduled_at,
            total_price=booking.total_price
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "scheduled_at": event.scheduled_at.isoformat(),
                "total_price": str(event.total_price)
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_booking_started_event(self, booking: Booking) -> None:
        """Fire booking started event"""
        event = BookingStarted(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            scheduled_at=booking.scheduled_at,
            actual_start_time=booking.actual_start_time,
            service_ids=booking.service_ids
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "scheduled_at": event.scheduled_at.isoformat(),
                "actual_start_time": event.actual_start_time.isoformat() if event.actual_start_time else None,
                "service_ids": [str(sid) for sid in event.service_ids]
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_booking_completed_event(self, booking: Booking) -> None:
        """Fire booking completed event"""
        overtime_charge = booking.calculate_overtime_charge()
        
        event = BookingCompleted(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            scheduled_at=booking.scheduled_at,
            actual_start_time=booking.actual_start_time,
            actual_end_time=booking.actual_end_time,
            total_price=booking.total_price,
            overtime_charge=overtime_charge,
            service_ids=booking.service_ids
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "scheduled_at": event.scheduled_at.isoformat(),
                "actual_start_time": event.actual_start_time.isoformat() if event.actual_start_time else None,
                "actual_end_time": event.actual_end_time.isoformat() if event.actual_end_time else None,
                "total_price": str(event.total_price),
                "overtime_charge": str(event.overtime_charge),
                "service_ids": [str(sid) for sid in event.service_ids]
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_booking_cancelled_event(
        self,
        booking: Booking,
        notice_hours: float,
        reason: Optional[str]
    ) -> None:
        """Fire booking cancelled event"""
        event = BookingCancelled(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            scheduled_at=booking.scheduled_at,
            cancellation_fee=booking.cancellation_fee,
            notice_hours=notice_hours,
            reason=reason
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "scheduled_at": event.scheduled_at.isoformat(),
                "cancellation_fee": str(event.cancellation_fee),
                "notice_hours": event.notice_hours,
                "reason": event.reason
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_booking_rescheduled_event(
        self,
        booking: Booking,
        old_scheduled_at: datetime,
        notice_hours: float
    ) -> None:
        """Fire booking rescheduled event"""
        event = BookingRescheduled(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            old_scheduled_at=old_scheduled_at,
            new_scheduled_at=booking.scheduled_at,
            notice_hours=notice_hours
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "old_scheduled_at": event.old_scheduled_at.isoformat(),
                "new_scheduled_at": event.new_scheduled_at.isoformat(),
                "notice_hours": event.notice_hours
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_no_show_detected_event(self, booking: Booking) -> None:
        """Fire no-show detected event"""
        grace_period_end = booking.scheduled_at + timedelta(minutes=Booking.GRACE_PERIOD_MINUTES)
        
        event = NoShowDetected(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            scheduled_at=booking.scheduled_at,
            grace_period_end=grace_period_end,
            penalty_fee=booking.cancellation_fee
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "scheduled_at": event.scheduled_at.isoformat(),
                "grace_period_end": event.grace_period_end.isoformat(),
                "penalty_fee": str(event.penalty_fee)
            }),
            occurred_at=event.occurred_at
        )
    
    async def _fire_quality_rated_event(self, booking: Booking) -> None:
        """Fire quality rated event"""
        event = QualityRated(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            occurred_at=datetime.now(timezone.utc),
            rating=booking.quality_rating,
            feedback=booking.quality_feedback,
            service_ids=booking.service_ids
        )
        
        await self.event_repo.create_event(
            booking_id=booking.id,
            customer_id=booking.customer_id,
            event_type=event.event_type,
            event_data=json.dumps({
                "rating": event.rating.value,
                "feedback": event.feedback,
                "service_ids": [str(sid) for sid in event.service_ids]
            }),
            occurred_at=event.occurred_at
        )
    # Additional methods for enhanced scheduling
    async def get_available_times_for_date(
        self,
        date: datetime,
        service_ids: List[UUID],
        customer_id: UUID
    ) -> List[datetime]:
        """Get available time slots for a specific date"""
        # For now, return sample time slots
        available_times = []
        start_hour = 8  # 8 AM
        end_hour = 18   # 6 PM
        
        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:  # Every 30 minutes
                time_slot = date.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=timezone.utc)
                if time_slot > datetime.now(timezone.utc):  # Only future times
                    available_times.append(time_slot)
        
        return available_times
    
    async def suggest_alternative_times(
        self,
        customer_id: UUID,
        preferred_time: datetime,
        service_ids: List[UUID],
        days_to_search: int = 7
    ) -> List[datetime]:
        """Suggest alternative booking times"""
        alternatives = []
        current_date = preferred_time.date()
        
        for day_offset in range(days_to_search):
            check_date = datetime.combine(
                current_date + timedelta(days=day_offset),
                preferred_time.time(),
                tzinfo=timezone.utc
            )
            
            if check_date > datetime.now(timezone.utc):
                # Add times around the preferred time
                for hour_offset in [-2, -1, 1, 2]:
                    alt_time = check_date + timedelta(hours=hour_offset)
                    if alt_time > datetime.now(timezone.utc) and 8 <= alt_time.hour < 18:
                        alternatives.append(alt_time)
        
        return alternatives[:10]  # Return up to 10 alternatives
    
    async def reschedule_booking_with_validation(
        self,
        booking_id: UUID,
        new_scheduled_at: datetime,
        customer_id: UUID
    ) -> Tuple[Booking, List[str]]:
        """Reschedule a booking with validation"""
        warnings = []
        
        # Get the booking
        booking = await self._get_booking_or_raise(booking_id)
        
        # Verify ownership
        if booking.customer_id != customer_id:
            raise ValueError("You can only reschedule your own bookings")
        
        # Validate new time
        if new_scheduled_at <= datetime.now(timezone.utc):
            raise ValueError("Cannot reschedule to a past time")
        
        # Check if rescheduling is too close to the original time
        hours_until_original = (booking.scheduled_at - datetime.now(timezone.utc)).total_seconds() / 3600
        if hours_until_original < 2:
            warnings.append("Rescheduling within 2 hours of original booking time may incur fees")
        
        # Reschedule the booking
        rescheduled_booking = await self.reschedule_booking(booking_id, new_scheduled_at)
        
        return rescheduled_booking, warnings

