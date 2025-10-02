from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
import json

from app.features.services.domain import Category, Service
from app.features.services.ports import (
    ICacheService,
    IEventService,
    INotificationService,
    IAuditService,
    IAnalyticsService,
)


class RedisCacheService(ICacheService):
    """Redis-based cache service implementation for services."""
    
    def __init__(self, redis_client):
        self._redis = redis_client
    
    async def get_category(self, category_id: str) -> Optional[Category]:
        """Get cached category."""
        try:
            data = await self._redis.get(f"category:{category_id}")
            if data:
                # Deserialize category data
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_category(self, category: Category, ttl: int = 3600) -> bool:
        """Cache category data."""
        try:
            data = json.dumps({
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "status": category.status.value,
                "display_order": category.display_order,
            })
            await self._redis.setex(f"category:{category.id}", ttl, data)
            return True
        except Exception:
            return False
    
    async def delete_category(self, category_id: str) -> bool:
        """Remove category from cache."""
        try:
            await self._redis.delete(f"category:{category_id}")
            return True
        except Exception:
            return False
    
    async def get_service(self, service_id: str) -> Optional[Service]:
        """Get cached service."""
        try:
            data = await self._redis.get(f"service:{service_id}")
            if data:
                # Deserialize service data
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_service(self, service: Service, ttl: int = 3600) -> bool:
        """Cache service data."""
        try:
            data = json.dumps({
                "id": service.id,
                "category_id": service.category_id,
                "name": service.name,
                "description": service.description,
                "price": str(service.price),
                "duration_minutes": service.duration_minutes,
                "status": service.status.value,
                "is_popular": service.is_popular,
            })
            await self._redis.setex(f"service:{service.id}", ttl, data)
            return True
        except Exception:
            return False
    
    async def delete_service(self, service_id: str) -> bool:
        """Remove service from cache."""
        try:
            await self._redis.delete(f"service:{service_id}")
            return True
        except Exception:
            return False
    
    async def get_popular_services(self) -> Optional[List[Service]]:
        """Get cached popular services."""
        try:
            data = await self._redis.get("popular_services")
            if data:
                # Deserialize list of services
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_popular_services(
        self,
        services: List[Service],
        ttl: int = 1800,
    ) -> bool:
        """Cache popular services."""
        try:
            if not services:
                await self._redis.delete("popular_services")
                return True
            
            data = json.dumps([
                {
                    "id": s.id,
                    "name": s.name,
                    "price": str(s.price),
                    "duration_minutes": s.duration_minutes,
                }
                for s in services
            ])
            await self._redis.setex("popular_services", ttl, data)
            return True
        except Exception:
            return False
    
    async def get_category_services(
        self,
        category_id: str,
    ) -> Optional[List[Service]]:
        """Get cached services for a category."""
        try:
            data = await self._redis.get(f"category_services:{category_id}")
            if data:
                # Deserialize list of services
                return None  # Placeholder
            return None
        except Exception:
            return None
    
    async def set_category_services(
        self,
        category_id: str,
        services: List[Service],
        ttl: int = 1800,
    ) -> bool:
        """Cache services for a category."""
        try:
            data = json.dumps([
                {
                    "id": s.id,
                    "name": s.name,
                    "price": str(s.price),
                    "duration_minutes": s.duration_minutes,
                    "is_popular": s.is_popular,
                }
                for s in services
            ])
            await self._redis.setex(f"category_services:{category_id}", ttl, data)
            return True
        except Exception:
            return False
    
    async def delete_category_services(self, category_id: str) -> bool:
        """Remove category services from cache."""
        try:
            await self._redis.delete(f"category_services:{category_id}")
            return True
        except Exception:
            return False
    
    async def invalidate_services_cache(self) -> bool:
        """Invalidate all services cache."""
        try:
            pattern = "service:*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            
            await self._redis.delete("popular_services")
            
            pattern = "category_services:*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            
            return True
        except Exception:
            return False


class EventBusService(IEventService):
    """Event bus service implementation for services."""
    
    def __init__(self, event_bus):
        self._event_bus = event_bus
    
    async def publish_category_created(self, category: Category) -> bool:
        """Publish category created event."""
        try:
            event_data = {
                "event_type": "category_created",
                "category_id": category.id,
                "name": category.name,
                "status": category.status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("category.created", event_data)
            return True
        except Exception:
            return False
    
    async def publish_category_updated(
        self,
        category: Category,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish category updated event."""
        try:
            event_data = {
                "event_type": "category_updated",
                "category_id": category.id,
                "changes": changes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("category.updated", event_data)
            return True
        except Exception:
            return False
    
    async def publish_category_deactivated(self, category: Category) -> bool:
        """Publish category deactivated event."""
        try:
            event_data = {
                "event_type": "category_deactivated",
                "category_id": category.id,
                "name": category.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("category.deactivated", event_data)
            return True
        except Exception:
            return False
    
    async def publish_service_created(self, service: Service) -> bool:
        """Publish service created event."""
        try:
            event_data = {
                "event_type": "service_created",
                "service_id": service.id,
                "category_id": service.category_id,
                "name": service.name,
                "price": str(service.price),
                "duration_minutes": service.duration_minutes,
                "is_popular": service.is_popular,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("service.created", event_data)
            return True
        except Exception:
            return False
    
    async def publish_service_updated(
        self,
        service: Service,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish service updated event."""
        try:
            event_data = {
                "event_type": "service_updated",
                "service_id": service.id,
                "changes": changes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("service.updated", event_data)
            return True
        except Exception:
            return False
    
    async def publish_service_price_changed(
        self,
        service: Service,
        old_price: Decimal,
        new_price: Decimal,
    ) -> bool:
        """Publish service price change event."""
        try:
            event_data = {
                "event_type": "service_price_changed",
                "service_id": service.id,
                "name": service.name,
                "old_price": str(old_price),
                "new_price": str(new_price),
                "change_amount": str(new_price - old_price),
                "change_percent": float((new_price - old_price) / old_price * 100) if old_price > 0 else 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("service.price_changed", event_data)
            return True
        except Exception:
            return False
    
    async def publish_service_deactivated(self, service: Service) -> bool:
        """Publish service deactivated event."""
        try:
            event_data = {
                "event_type": "service_deactivated",
                "service_id": service.id,
                "name": service.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("service.deactivated", event_data)
            return True
        except Exception:
            return False
    
    async def publish_service_archived(self, service: Service) -> bool:
        """Publish service archived event."""
        try:
            event_data = {
                "event_type": "service_archived",
                "service_id": service.id,
                "name": service.name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("service.archived", event_data)
            return True
        except Exception:
            return False
    
    async def publish_service_marked_popular(
        self,
        service: Service,
        is_popular: bool,
    ) -> bool:
        """Publish service popularity change event."""
        try:
            event_data = {
                "event_type": "service_popularity_changed",
                "service_id": service.id,
                "name": service.name,
                "is_popular": is_popular,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._event_bus.publish("service.popularity_changed", event_data)
            return True
        except Exception:
            return False


class EmailNotificationService(INotificationService):
    """Email-based notification service for services."""
    
    def __init__(self, email_service):
        self._email_service = email_service
    
    async def notify_service_price_change(
        self,
        service: Service,
        old_price: Decimal,
        new_price: Decimal,
        affected_customers: List[str],
    ) -> bool:
        """Notify customers about service price change."""
        try:
            subject = f"Price Update: {service.name}"
            
            price_change = new_price - old_price
            change_type = "increased" if price_change > 0 else "decreased"
            
            body = f"""
            Dear Customer,
            
            We're writing to inform you about a price change for the service:
            {service.name}
            
            Previous Price: ${old_price:.2f}
            New Price: ${new_price:.2f}
            
            The price has {change_type} by ${abs(price_change):.2f}.
            
            This change will apply to future bookings.
            
            Thank you for your understanding.
            """
            
            # Send to all affected customers
            for customer_email in affected_customers:
                await self._email_service.send_email(
                    to_email=customer_email,
                    subject=subject,
                    body=body,
                )
            
            return True
        except Exception:
            return False
    
    async def notify_new_service_available(
        self,
        service: Service,
        interested_customers: List[str],
    ) -> bool:
        """Notify customers about new service availability."""
        try:
            subject = f"New Service Available: {service.name}"
            
            body = f"""
            Dear Customer,
            
            We're excited to announce a new service:
            
            {service.name}
            {service.description}
            
            Price: {service.price_display}
            Duration: {service.duration_display}
            
            Book now to try our new service!
            
            Thank you for choosing our service.
            """
            
            for customer_email in interested_customers:
                await self._email_service.send_email(
                    to_email=customer_email,
                    subject=subject,
                    body=body,
                )
            
            return True
        except Exception:
            return False
    
    async def notify_service_discontinued(
        self,
        service: Service,
        affected_customers: List[str],
        alternative_services: List[Service],
    ) -> bool:
        """Notify customers about service discontinuation."""
        try:
            subject = f"Service Update: {service.name}"
            
            alternatives_text = ""
            if alternative_services:
                alternatives_text = "\n\nWe recommend these alternatives:\n"
                for alt in alternative_services[:3]:
                    alternatives_text += f"- {alt.name}: {alt.price_display}\n"
            
            body = f"""
            Dear Customer,
            
            We regret to inform you that the following service will be discontinued:
            {service.name}
            
            {alternatives_text}
            
            We apologize for any inconvenience.
            
            Thank you for your understanding.
            """
            
            for customer_email in affected_customers:
                await self._email_service.send_email(
                    to_email=customer_email,
                    subject=subject,
                    body=body,
                )
            
            return True
        except Exception:
            return False


class AuditService(IAuditService):
    """Audit service implementation for services."""
    
    def __init__(self, audit_logger):
        self._logger = audit_logger
    
    async def log_category_creation(
        self,
        category: Category,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log category creation event."""
        try:
            log_entry = {
                "action": "category_created",
                "category_id": category.id,
                "name": category.name,
                "created_by": created_by,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_category_update(
        self,
        category: Category,
        updated_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log category update event."""
        try:
            log_entry = {
                "action": "category_updated",
                "category_id": category.id,
                "updated_by": updated_by,
                "changes": changes,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_category_deactivation(
        self,
        category: Category,
        deactivated_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log category deactivation event."""
        try:
            log_entry = {
                "action": "category_deactivated",
                "category_id": category.id,
                "name": category.name,
                "deactivated_by": deactivated_by,
                "reason": reason,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_service_creation(
        self,
        service: Service,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service creation event."""
        try:
            log_entry = {
                "action": "service_created",
                "service_id": service.id,
                "name": service.name,
                "price": str(service.price),
                "created_by": created_by,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_service_update(
        self,
        service: Service,
        updated_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service update event."""
        try:
            log_entry = {
                "action": "service_updated",
                "service_id": service.id,
                "updated_by": updated_by,
                "changes": changes,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_service_price_change(
        self,
        service: Service,
        changed_by: str,
        old_price: Decimal,
        new_price: Decimal,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service price change event."""
        try:
            log_entry = {
                "action": "service_price_changed",
                "service_id": service.id,
                "name": service.name,
                "changed_by": changed_by,
                "old_price": str(old_price),
                "new_price": str(new_price),
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False
    
    async def log_service_deactivation(
        self,
        service: Service,
        deactivated_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service deactivation event."""
        try:
            log_entry = {
                "action": "service_deactivated",
                "service_id": service.id,
                "name": service.name,
                "deactivated_by": deactivated_by,
                "reason": reason,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._logger.log_audit_event(log_entry)
            return True
        except Exception:
            return False


class AnalyticsService(IAnalyticsService):
    """Analytics service implementation for services."""
    
    def __init__(self, analytics_client=None):
        self._analytics = analytics_client
    
    async def get_service_performance_metrics(
        self,
        service_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Get performance metrics for a service."""
        # Would query analytics database
        return {
            "service_id": service_id,
            "booking_count": 150,
            "revenue": 3750.00,
            "average_rating": 4.5,
            "utilization_rate": 0.75,
            "popular_times": ["10:00", "14:00", "16:00"],
        }
    
    async def get_category_performance_metrics(
        self,
        category_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Get performance metrics for a category."""
        return {
            "category_id": category_id,
            "total_bookings": 500,
            "total_revenue": 12500.00,
            "top_services": ["Basic Wash", "Premium Wash", "Wax"],
            "growth_rate": 0.15,
        }
    
    async def get_demand_forecast(
        self,
        service_id: str,
        forecast_days: int = 30,
    ) -> Dict[str, Any]:
        """Get demand forecast for a service."""
        return {
            "service_id": service_id,
            "forecast_period": forecast_days,
            "expected_bookings": 45,
            "confidence_level": 0.85,
            "trend": "increasing",
        }
    
    async def get_pricing_recommendations(
        self,
        service_id: str,
    ) -> Dict[str, Any]:
        """Get pricing recommendations based on analytics."""
        return {
            "service_id": service_id,
            "current_price": 25.00,
            "recommended_price": 28.00,
            "expected_revenue_impact": 0.12,
            "competitor_average": 27.50,
        }
    
    async def get_service_comparison(
        self,
        service_ids: List[str],
        metrics: List[str],
    ) -> Dict[str, Any]:
        """Compare multiple services across metrics."""
        return {
            "comparison": {
                service_id: {
                    "bookings": 50,
                    "revenue": 1250.00,
                    "rating": 4.3,
                }
                for service_id in service_ids
            },
            "best_performer": service_ids[0] if service_ids else None,
        }