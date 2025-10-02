from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json
import uuid

from app.features.bookings.domain import Booking
from app.features.bookings.ports import (
    INotificationService,
    IPaymentService,
    ICacheService,
    IEventService,
    ILockService,
)


class EmailNotificationService(INotificationService):
    """Email-based notification service implementation."""
    
    def __init__(self, email_service):
        self._email_service = email_service
    
    async def send_booking_confirmation(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
        services_data: List[Dict[str, Any]],
        vehicle_data: Dict[str, Any],
    ) -> bool:
        """Send booking confirmation email."""
        try:
            subject = f"Booking Confirmation - {booking.id}"
            
            services_list = ", ".join([s["name"] for s in services_data])
            vehicle_info = f"{vehicle_data['year']} {vehicle_data['make']} {vehicle_data['model']}"
            
            body = f"""
            Dear {customer_data['first_name']},
            
            Your booking has been confirmed!
            
            Booking Details:
            - Booking ID: {booking.id}
            - Vehicle: {vehicle_info}
            - Services: {services_list}
            - Scheduled: {booking.scheduled_at.strftime('%Y-%m-%d %H:%M')}
            - Total Price: ${booking.total_price:.2f}
            - Estimated Duration: {booking.estimated_duration_minutes} minutes
            
            Thank you for choosing our service!
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False
    
    async def send_booking_cancellation(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
    ) -> bool:
        """Send booking cancellation email."""
        try:
            subject = f"Booking Cancelled - {booking.id}"
            
            body = f"""
            Dear {customer_data['first_name']},
            
            Your booking {booking.id} has been cancelled.
            
            If you have any questions, please contact us.
            
            Thank you.
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False
    
    async def send_booking_reminder(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
        hours_before: int = 24,
    ) -> bool:
        """Send booking reminder email."""
        try:
            subject = f"Booking Reminder - {booking.id}"
            
            body = f"""
            Dear {customer_data['first_name']},
            
            This is a reminder that you have a booking scheduled for:
            {booking.scheduled_at.strftime('%Y-%m-%d %H:%M')}
            
            Booking ID: {booking.id}
            Total Price: ${booking.total_price:.2f}
            
            See you soon!
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False
    
    async def send_booking_updated(
        self,
        customer_email: str,
        booking: Booking,
        customer_data: Dict[str, Any],
        changes: Dict[str, Any],
    ) -> bool:
        """Send booking update notification."""
        try:
            subject = f"Booking Updated - {booking.id}"
            
            changes_text = ", ".join(changes.keys())
            
            body = f"""
            Dear {customer_data['first_name']},
            
            Your booking {booking.id} has been updated.
            
            Changes made: {changes_text}
            
            Updated details:
            - Scheduled: {booking.scheduled_at.strftime('%Y-%m-%d %H:%M')}
            - Total Price: ${booking.total_price:.2f}
            
            Thank you.
            """
            
            return await self._email_service.send_email(
                to_email=customer_email,
                subject=subject,
                body=body,
            )
        except Exception:
            return False


class StripePaymentService(IPaymentService):
    """Stripe payment service implementation."""
    
    def __init__(self, stripe_client):
        self._stripe = stripe_client
    
    async def create_payment_intent(
        self,
        booking: Booking,
        customer_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create payment intent for booking."""
        try:
            # Create Stripe payment intent
            amount_cents = int(booking.total_price * 100)
            
            intent = await self._stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                metadata={
                    "booking_id": booking.id,
                    "customer_id": booking.customer_id,
                },
                description=f"Booking {booking.id}",
            )
            
            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "amount": booking.total_price,
                "status": intent.status,
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
            }
    
    async def confirm_payment(
        self,
        payment_intent_id: str,
        booking_id: str,
    ) -> Dict[str, Any]:
        """Confirm payment for booking."""
        try:
            intent = await self._stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount_paid": intent.amount / 100,
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
            }
    
    async def refund_payment(
        self,
        payment_intent_id: str,
        booking_id: str,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer",
    ) -> Dict[str, Any]:
        """Process refund for cancelled booking."""
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
                "reason": reason,
            }
            
            if amount:
                refund_params["amount"] = int(amount * 100)
            
            refund = await self._stripe.Refund.create(**refund_params)
            
            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount_refunded": refund.amount / 100,
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed",
            }
    
    async def get_payment_status(
        self,
        payment_intent_id: str,
    ) -> Dict[str, Any]:
        """Get current payment status."""
        try:
            intent = await self._stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "unknown",
            }


class RedisCacheService(ICacheService):
    """Redis-based cache service implementation."""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    async def get_booking(self, booking_id: str) -> Optional[Booking]:
        """Get cached booking."""
        try:
            data = await self._redis.get(f"booking:{booking_id}")
            if data:
                # Deserialize booking data back to domain entity
                # This would require custom serialization logic
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_booking(self, booking: Booking, ttl: int = 3600) -> bool:
        """Cache booking data."""
        try:
            # Serialize booking to JSON
            # This would require custom serialization logic
            data = json.dumps({
                "id": booking.id,
                "customer_id": booking.customer_id,
                # ... other fields
            })
            
            await self._redis.setex(f"booking:{booking.id}", ttl, data)
            return True
        except Exception:
            return False
    
    async def delete_booking(self, booking_id: str) -> bool:
        """Remove booking from cache."""
        try:
            await self._redis.delete(f"booking:{booking_id}")
            return True
        except Exception:
            return False
    
    async def get_customer_bookings(
        self,
        customer_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached customer bookings."""
        try:
            key = f"customer_bookings:{customer_id}:{page}:{limit}"
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    async def set_customer_bookings(
        self,
        customer_id: str,
        bookings: List[Dict[str, Any]],
        page: int = 1,
        limit: int = 20,
        ttl: int = 1800,
    ) -> bool:
        """Cache customer bookings."""
        try:
            key = f"customer_bookings:{customer_id}:{page}:{limit}"
            data = json.dumps(bookings)
            await self._redis.setex(key, ttl, data)
            return True
        except Exception:
            return False
    
    async def invalidate_customer_cache(self, customer_id: str) -> bool:
        """Invalidate all cached data for customer."""
        try:
            pattern = f"customer_bookings:{customer_id}:*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            return True
        except Exception:
            return False


class EventBusService(IEventService):
    """Event bus service implementation."""
    
    def __init__(self, event_bus):
        self._event_bus = event_bus
    
    async def publish_booking_created(self, booking: Booking) -> bool:
        """Publish booking created event."""
        try:
            event_data = {
                "event_type": "booking_created",
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "scheduled_at": booking.scheduled_at.isoformat(),
                "total_price": booking.total_price,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("booking.created", event_data)
            return True
        except Exception:
            return False
    
    async def publish_booking_confirmed(self, booking: Booking) -> bool:
        """Publish booking confirmed event."""
        try:
            event_data = {
                "event_type": "booking_confirmed",
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("booking.confirmed", event_data)
            return True
        except Exception:
            return False
    
    async def publish_booking_cancelled(
        self,
        booking: Booking,
        cancelled_by: str,
        reason: str,
    ) -> bool:
        """Publish booking cancelled event."""
        try:
            event_data = {
                "event_type": "booking_cancelled",
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "cancelled_by": cancelled_by,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("booking.cancelled", event_data)
            return True
        except Exception:
            return False
    
    async def publish_booking_completed(self, booking: Booking) -> bool:
        """Publish booking completed event."""
        try:
            event_data = {
                "event_type": "booking_completed",
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("booking.completed", event_data)
            return True
        except Exception:
            return False
    
    async def publish_booking_updated(
        self,
        booking: Booking,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish booking updated event."""
        try:
            event_data = {
                "event_type": "booking_updated",
                "booking_id": booking.id,
                "customer_id": booking.customer_id,
                "changes": changes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await self._event_bus.publish("booking.updated", event_data)
            return True
        except Exception:
            return False


class RedisLockService(ILockService):
    """Redis-based distributed lock service with atomic operations."""

    # Lua script for atomic lock release (only release if we own the lock)
    RELEASE_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    # Lua script for atomic lock extension (only extend if we own the lock)
    EXTEND_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("expire", KEYS[1], ARGV[2])
    else
        return 0
    end
    """

    def __init__(self, redis_client):
        """Initialize lock service with Redis client."""
        self._redis = redis_client
        # Track lock_id to key mapping for release/extend operations
        self._lock_keys: Dict[str, str] = {}

    async def acquire_booking_lock(
        self,
        booking_id: str,
        timeout: int = 30,
    ) -> Optional[str]:
        """Acquire exclusive lock for booking."""
        try:
            lock_id = str(uuid.uuid4())
            key = f"lock:booking:{booking_id}"

            # SET with NX (only if not exists) and EX (expiry)
            result = self._redis.set(key, lock_id, ex=timeout, nx=True)

            if result:
                self._lock_keys[lock_id] = key
                return lock_id
            return None
        except Exception as e:
            # Log error but don't expose details
            return None

    async def acquire_time_slot_lock(
        self,
        scheduled_at: datetime,
        duration_minutes: int,
        booking_type: str,
        timeout: int = 30,
    ) -> Optional[str]:
        """Acquire lock for time slot to prevent double booking."""
        try:
            lock_id = str(uuid.uuid4())
            # Create a unique key based on time slot and type
            time_str = scheduled_at.strftime("%Y%m%d_%H%M")
            key = f"lock:timeslot:{booking_type}:{time_str}:{duration_minutes}"

            # SET with NX (only if not exists) and EX (expiry)
            result = self._redis.set(key, lock_id, ex=timeout, nx=True)

            if result:
                self._lock_keys[lock_id] = key
                return lock_id
            return None
        except Exception as e:
            return None

    async def release_lock(self, lock_id: str) -> bool:
        """Release acquired lock atomically (only if we own it)."""
        try:
            # Get the key for this lock_id
            key = self._lock_keys.get(lock_id)
            if not key:
                # Lock not found in tracking - might already be released
                return False

            # Use Lua script to atomically check ownership and delete
            result = self._redis.eval(
                self.RELEASE_LOCK_SCRIPT,
                1,  # number of keys
                key,  # KEYS[1]
                lock_id  # ARGV[1]
            )

            # Clean up tracking
            if result:
                self._lock_keys.pop(lock_id, None)
                return True

            return False
        except Exception as e:
            return False

    async def extend_lock(self, lock_id: str, additional_time: int = 30) -> bool:
        """Extend lock expiry time atomically (only if we own it)."""
        try:
            # Get the key for this lock_id
            key = self._lock_keys.get(lock_id)
            if not key:
                # Lock not found in tracking
                return False

            # Use Lua script to atomically check ownership and extend expiry
            result = self._redis.eval(
                self.EXTEND_LOCK_SCRIPT,
                1,  # number of keys
                key,  # KEYS[1]
                lock_id,  # ARGV[1]
                additional_time  # ARGV[2]
            )

            return bool(result)
        except Exception as e:
            return False