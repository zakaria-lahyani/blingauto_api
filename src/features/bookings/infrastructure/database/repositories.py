"""
Booking repository implementations
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from src.shared.database.base import BaseRepository
from src.features.bookings.domain.entities import Booking, BookingService
from src.features.bookings.domain.enums import BookingStatus, QualityRating, BookingSortBy
from .models import BookingModel, BookingServiceModel, BookingEventModel


class BookingRepository(BaseRepository[Booking, BookingModel]):
    """Repository for booking management"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session, BookingModel)
        self.db_session = db_session  # Keep for backwards compatibility
    
    async def create(self, booking: Booking) -> Booking:
        """Create a new booking"""
        # Create booking model using from_entity which handles timezone conversion
        booking_model = BookingModel.from_entity(booking)
        
        self.db_session.add(booking_model)
        
        # Create associated services
        for service in booking.services:
            service_model = BookingServiceModel(
                id=service.id,
                booking_id=booking.id,
                service_id=service.service_id,
                service_name=service.service_name,
                price=service.price,
                duration=service.duration
            )
            self.db_session.add(service_model)
        
        await self.db_session.flush()
        return booking
    
    async def get(self, booking_id: UUID) -> Optional[Booking]:
        """Get booking by ID"""
        query = select(BookingModel).options(
            selectinload(BookingModel.services),
            selectinload(BookingModel.vehicle)
        ).where(BookingModel.id == booking_id)
        
        result = await self.db_session.execute(query)
        booking_model = result.scalar_one_or_none()
        
        if not booking_model:
            return None
        
        return self._model_to_entity(booking_model)
    
    async def list(self, limit: int = 100, offset: int = 0) -> List[Booking]:
        """List bookings - base repository interface"""
        query = select(BookingModel).options(
            selectinload(BookingModel.services)
        ).limit(limit).offset(offset)
        
        result = await self.db_session.execute(query)
        booking_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in booking_models]
    
    async def update(self, booking: Booking) -> Booking:
        """Update an existing booking"""
        query = select(BookingModel).where(BookingModel.id == booking.id)
        result = await self.db_session.execute(query)
        booking_model = result.scalar_one_or_none()
        
        if not booking_model:
            raise ValueError(f"Booking not found: {booking.id}")
        
        # Update booking fields
        booking_model.customer_id = booking.customer_id
        booking_model.vehicle_id = booking.vehicle_id
        booking_model.scheduled_at = booking.scheduled_at
        booking_model.status = booking.status.value
        booking_model.notes = booking.notes
        booking_model.total_price = booking.total_price
        booking_model.total_duration = booking.total_duration
        booking_model.cancellation_fee = booking.cancellation_fee
        booking_model.quality_rating = booking.quality_rating.value if booking.quality_rating else None
        booking_model.quality_feedback = booking.quality_feedback
        booking_model.actual_start_time = booking.actual_start_time
        booking_model.actual_end_time = booking.actual_end_time
        booking_model.updated_at = booking.updated_at
        
        await self.db_session.flush()
        return booking
    
    async def delete(self, booking_id: UUID) -> bool:
        """Delete a booking"""
        query = select(BookingModel).where(BookingModel.id == booking_id)
        result = await self.db_session.execute(query)
        booking_model = result.scalar_one_or_none()
        
        if not booking_model:
            return False
        
        await self.db_session.delete(booking_model)
        await self.db_session.flush()
        return True
    
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
        query = select(BookingModel).options(
            selectinload(BookingModel.services),
            selectinload(BookingModel.vehicle)
        )
        
        # Apply filters
        if customer_id:
            query = query.where(BookingModel.customer_id == customer_id)
        
        if vehicle_id:
            query = query.where(BookingModel.vehicle_id == vehicle_id)
        
        if status:
            query = query.where(BookingModel.status == status.value)
        
        if scheduled_date:
            # Filter for specific date (ignoring time)
            start_of_day = scheduled_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.where(
                and_(
                    BookingModel.scheduled_at >= start_of_day,
                    BookingModel.scheduled_at < end_of_day
                )
            )
        
        if date_range:
            start_date, end_date = date_range
            query = query.where(
                and_(
                    BookingModel.scheduled_at >= start_date,
                    BookingModel.scheduled_at <= end_date
                )
            )
        
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(BookingModel.notes).like(search_pattern),
                    func.lower(BookingModel.quality_feedback).like(search_pattern)
                )
            )
        
        # Count total results
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db_session.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        if sort_by == BookingSortBy.CREATED_AT:
            order_field = BookingModel.created_at
        elif sort_by == BookingSortBy.SCHEDULED_AT:
            order_field = BookingModel.scheduled_at
        elif sort_by == BookingSortBy.TOTAL_PRICE:
            order_field = BookingModel.total_price
        elif sort_by == BookingSortBy.STATUS:
            order_field = BookingModel.status
        else:
            order_field = BookingModel.created_at
        
        if sort_desc:
            query = query.order_by(desc(order_field))
        else:
            query = query.order_by(asc(order_field))
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db_session.execute(query)
        booking_models = result.scalars().all()
        
        bookings = [self._model_to_entity(model) for model in booking_models]
        return bookings, total
    
    async def get_bookings_by_status(self, status: BookingStatus) -> List[Booking]:
        """Get all bookings with specific status"""
        query = select(BookingModel).options(
            selectinload(BookingModel.services)
        ).where(BookingModel.status == status.value)
        
        result = await self.db_session.execute(query)
        booking_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in booking_models]
    
    async def get_bookings_for_no_show_check(self, cutoff_time: datetime) -> List[Booking]:
        """Get confirmed bookings that are eligible for no-show status"""
        query = select(BookingModel).options(
            selectinload(BookingModel.services)
        ).where(
            and_(
                BookingModel.status == BookingStatus.CONFIRMED.value,
                BookingModel.scheduled_at < cutoff_time
            )
        )
        
        result = await self.db_session.execute(query)
        booking_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in booking_models]
    
    async def get_customer_bookings(
        self,
        customer_id: UUID,
        status_filter: Optional[List[BookingStatus]] = None,
        limit: int = 10
    ) -> List[Booking]:
        """Get recent bookings for a customer"""
        query = select(BookingModel).options(
            selectinload(BookingModel.services)
        ).where(BookingModel.customer_id == customer_id)
        
        if status_filter:
            status_values = [status.value for status in status_filter]
            query = query.where(BookingModel.status.in_(status_values))
        
        query = query.order_by(desc(BookingModel.created_at)).limit(limit)
        
        result = await self.db_session.execute(query)
        booking_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in booking_models]
    
    async def get_bookings_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Booking]:
        """Get all bookings within a date range"""
        query = select(BookingModel).options(
            selectinload(BookingModel.services)
        ).where(
            and_(
                BookingModel.scheduled_at >= start_date,
                BookingModel.scheduled_at <= end_date
            )
        ).order_by(BookingModel.scheduled_at)
        
        result = await self.db_session.execute(query)
        booking_models = result.scalars().all()
        
        return [self._model_to_entity(model) for model in booking_models]
    
    async def count_customer_bookings(
        self,
        customer_id: UUID,
        status: Optional[BookingStatus] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> int:
        """Count customer bookings with optional filters"""
        query = select(func.count(BookingModel.id)).where(
            BookingModel.customer_id == customer_id
        )
        
        if status:
            query = query.where(BookingModel.status == status.value)
        
        if date_range:
            start_date, end_date = date_range
            query = query.where(
                and_(
                    BookingModel.scheduled_at >= start_date,
                    BookingModel.scheduled_at <= end_date
                )
            )
        
        result = await self.db_session.execute(query)
        return result.scalar()
    
    def _model_to_entity(self, model: BookingModel) -> Booking:
        """Convert database model to domain entity"""
        # Convert services
        services = []
        for service_model in model.services:
            service = BookingService(
                service_id=service_model.service_id,
                service_name=service_model.service_name,
                price=service_model.price,
                duration=service_model.duration,
                id=service_model.id
            )
            services.append(service)
        
        # Convert quality rating
        quality_rating = None
        if model.quality_rating:
            quality_rating = QualityRating(model.quality_rating)
        
        return Booking(
            customer_id=model.customer_id,
            vehicle_id=model.vehicle_id,
            scheduled_at=model.scheduled_at,
            services=services,
            notes=model.notes,
            id=model.id,
            status=BookingStatus(model.status),
            total_price=model.total_price,
            total_duration=model.total_duration,
            cancellation_fee=model.cancellation_fee,
            quality_rating=quality_rating,
            quality_feedback=model.quality_feedback,
            actual_start_time=model.actual_start_time,
            actual_end_time=model.actual_end_time,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class BookingEventRepository:
    """Repository for booking domain events"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create_event(
        self,
        booking_id: UUID,
        customer_id: UUID,
        event_type: str,
        event_data: Optional[str] = None,
        occurred_at: Optional[datetime] = None
    ) -> UUID:
        """Create a new booking event"""
        event_model = BookingEventModel(
            booking_id=booking_id,
            customer_id=customer_id,
            event_type=event_type,
            event_data=event_data,
            occurred_at=occurred_at or datetime.utcnow()
        )
        
        self.db_session.add(event_model)
        await self.db_session.flush()
        return event_model.id
    
    async def get_booking_events(
        self,
        booking_id: UUID,
        limit: int = 50
    ) -> List[BookingEventModel]:
        """Get events for a booking"""
        query = select(BookingEventModel).where(
            BookingEventModel.booking_id == booking_id
        ).order_by(desc(BookingEventModel.occurred_at)).limit(limit)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def mark_event_processed(self, event_id: UUID) -> bool:
        """Mark an event as processed"""
        query = select(BookingEventModel).where(BookingEventModel.id == event_id)
        result = await self.db_session.execute(query)
        event_model = result.scalar_one_or_none()
        
        if not event_model:
            return False
        
        event_model.processed = True
        event_model.processed_at = datetime.utcnow()
        await self.db_session.flush()
        return True
    
    async def get_unprocessed_events(self, limit: int = 100) -> List[BookingEventModel]:
        """Get unprocessed events for integration"""
        query = select(BookingEventModel).where(
            BookingEventModel.processed == False
        ).order_by(BookingEventModel.occurred_at).limit(limit)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()