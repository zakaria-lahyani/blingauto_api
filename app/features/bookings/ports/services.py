from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.features.bookings.domain import Booking


class INotificationService(ABC):
    """Notification service interface for booking events."""
    
    @abstractmethod
    async def send_booking_confirmation(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
        services_data: List[Dict[str, Any]],
        vehicle_data: Dict[str, Any],
    ) -> bool:
        """Send booking confirmation email."""
        pass
    
    @abstractmethod
    async def send_booking_cancellation(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send booking cancellation email."""
        pass
    
    @abstractmethod
    async def send_booking_reminder(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
        hours_before: int = 24,
    ) -> bool:
        """Send booking reminder email."""
        pass
    
    @abstractmethod
    async def send_booking_updated(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
        changes: Dict[str, Any],
    ) -> bool:
        """Send booking update notification."""
        pass


class IPaymentService(ABC):
    """Payment service interface for booking payments."""
    
    @abstractmethod
    async def create_payment_intent(
        self,
        booking: Booking,
        customer_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create payment intent for booking."""
        pass
    
    @abstractmethod
    async def confirm_payment(
        self,
        payment_intent_id: str,
        booking_id: str,
    ) -> Dict[str, Any]:
        """Confirm payment for booking."""
        pass
    
    @abstractmethod
    async def refund_payment(
        self,
        payment_intent_id: str,
        booking_id: str,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer",
    ) -> Dict[str, Any]:
        """Process refund for cancelled booking."""
        pass
    
    @abstractmethod
    async def get_payment_status(
        self,
        payment_intent_id: str,
    ) -> Dict[str, Any]:
        """Get current payment status."""
        pass


class ICacheService(ABC):
    """Cache service interface for booking performance."""
    
    @abstractmethod
    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get cached booking."""
        pass
    
    @abstractmethod
    async def set_booking(self, booking: Booking, ttl: int = 3600) -> bool:
        """Cache booking data."""
        pass
    
    @abstractmethod
    async def delete_booking(self, booking_id: str) -> bool:
        """Remove booking from cache."""
        pass
    
    @abstractmethod
    async def get_customer_bookings(
        self,
        customer_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached customer bookings."""
        pass
    
    @abstractmethod
    async def set_customer_bookings(
        self,
        customer_id: str,
        bookings: List[Dict[str, Any]],
        page: int = 1,
        limit: int = 20,
        ttl: int = 1800,
    ) -> bool:
        """Cache customer bookings."""
        pass
    
    @abstractmethod
    async def invalidate_customer_cache(self, customer_id: str) -> bool:
        """Invalidate all cached data for customer."""
        pass


class IEventService(ABC):
    """Event service interface for booking domain events."""
    
    @abstractmethod
    async def publish_booking_created(self, booking: Booking) -> bool:
        """Publish booking created event."""
        pass
    
    @abstractmethod
    async def publish_booking_confirmed(self, booking: Booking) -> bool:
        """Publish booking confirmed event."""
        pass
    
    @abstractmethod
    async def publish_booking_cancelled(
        self,
        booking: Booking,
        cancelled_by: str,
        reason: str,
    ) -> bool:
        """Publish booking cancelled event."""
        pass
    
    @abstractmethod
    async def publish_booking_completed(self, booking: Booking) -> bool:
        """Publish booking completed event."""
        pass
    
    @abstractmethod
    async def publish_booking_updated(
        self,
        booking: Booking,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish booking updated event."""
        pass


class ILockService(ABC):
    """Distributed lock service for booking concurrency control."""
    
    @abstractmethod
    async def acquire_booking_lock(
        self,
        booking_id: str,
        timeout: int = 30,
    ) -> Optional[str]:
        """Acquire exclusive lock for booking."""
        pass
    
    @abstractmethod
    async def acquire_time_slot_lock(
        self,
        scheduled_at: datetime,
        duration_minutes: int,
        booking_type: str,
        timeout: int = 30,
    ) -> Optional[str]:
        """Acquire lock for time slot to prevent double booking."""
        pass
    
    @abstractmethod
    async def release_lock(self, lock_id: str) -> bool:
        """Release acquired lock."""
        pass
    
    @abstractmethod
    async def extend_lock(self, lock_id: str, additional_time: int = 30) -> bool:
        """Extend lock expiry time."""
        pass