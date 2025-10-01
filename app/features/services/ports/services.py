from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from decimal import Decimal

from app.features.services.domain import Category, Service


class ICacheService(ABC):
    """Cache service interface for services performance."""
    
    @abstractmethod
    async def get_category(self, category_id: str) -> Optional[Category]:
        """Get cached category."""
        pass
    
    @abstractmethod
    async def set_category(self, category: Category, ttl: int = 3600) -> bool:
        """Cache category data."""
        pass
    
    @abstractmethod
    async def delete_category(self, category_id: str) -> bool:
        """Remove category from cache."""
        pass
    
    @abstractmethod
    async def get_service(self, service_id: str) -> Optional[Service]:
        """Get cached service."""
        pass
    
    @abstractmethod
    async def set_service(self, service: Service, ttl: int = 3600) -> bool:
        """Cache service data."""
        pass
    
    @abstractmethod
    async def delete_service(self, service_id: str) -> bool:
        """Remove service from cache."""
        pass
    
    @abstractmethod
    async def get_popular_services(self) -> Optional[List[Service]]:
        """Get cached popular services."""
        pass
    
    @abstractmethod
    async def set_popular_services(
        self,
        services: List[Service],
        ttl: int = 1800,
    ) -> bool:
        """Cache popular services."""
        pass
    
    @abstractmethod
    async def get_category_services(
        self,
        category_id: str,
    ) -> Optional[List[Service]]:
        """Get cached services for a category."""
        pass
    
    @abstractmethod
    async def set_category_services(
        self,
        category_id: str,
        services: List[Service],
        ttl: int = 1800,
    ) -> bool:
        """Cache services for a category."""
        pass
    
    @abstractmethod
    async def invalidate_services_cache(self) -> bool:
        """Invalidate all services cache."""
        pass


class IEventService(ABC):
    """Event service interface for service domain events."""
    
    @abstractmethod
    async def publish_category_created(self, category: Category) -> bool:
        """Publish category created event."""
        pass
    
    @abstractmethod
    async def publish_category_updated(
        self,
        category: Category,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish category updated event."""
        pass
    
    @abstractmethod
    async def publish_category_deactivated(self, category: Category) -> bool:
        """Publish category deactivated event."""
        pass
    
    @abstractmethod
    async def publish_service_created(self, service: Service) -> bool:
        """Publish service created event."""
        pass
    
    @abstractmethod
    async def publish_service_updated(
        self,
        service: Service,
        changes: Dict[str, Any],
    ) -> bool:
        """Publish service updated event."""
        pass
    
    @abstractmethod
    async def publish_service_price_changed(
        self,
        service: Service,
        old_price: Decimal,
        new_price: Decimal,
    ) -> bool:
        """Publish service price change event."""
        pass
    
    @abstractmethod
    async def publish_service_deactivated(self, service: Service) -> bool:
        """Publish service deactivated event."""
        pass
    
    @abstractmethod
    async def publish_service_archived(self, service: Service) -> bool:
        """Publish service archived event."""
        pass
    
    @abstractmethod
    async def publish_service_marked_popular(
        self,
        service: Service,
        is_popular: bool,
    ) -> bool:
        """Publish service popularity change event."""
        pass


class INotificationService(ABC):
    """Notification service interface for service events."""
    
    @abstractmethod
    async def notify_service_price_change(
        self,
        service: Service,
        old_price: Decimal,
        new_price: Decimal,
        affected_customers: List[str],
    ) -> bool:
        """Notify customers about service price change."""
        pass
    
    @abstractmethod
    async def notify_new_service_available(
        self,
        service: Service,
        interested_customers: List[str],
    ) -> bool:
        """Notify customers about new service availability."""
        pass
    
    @abstractmethod
    async def notify_service_discontinued(
        self,
        service: Service,
        affected_customers: List[str],
        alternative_services: List[Service],
    ) -> bool:
        """Notify customers about service discontinuation."""
        pass


class IAuditService(ABC):
    """Audit service interface for service changes."""
    
    @abstractmethod
    async def log_category_creation(
        self,
        category: Category,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log category creation event."""
        pass
    
    @abstractmethod
    async def log_category_update(
        self,
        category: Category,
        updated_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log category update event."""
        pass
    
    @abstractmethod
    async def log_category_deactivation(
        self,
        category: Category,
        deactivated_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log category deactivation event."""
        pass
    
    @abstractmethod
    async def log_service_creation(
        self,
        service: Service,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service creation event."""
        pass
    
    @abstractmethod
    async def log_service_update(
        self,
        service: Service,
        updated_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service update event."""
        pass
    
    @abstractmethod
    async def log_service_price_change(
        self,
        service: Service,
        changed_by: str,
        old_price: Decimal,
        new_price: Decimal,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service price change event."""
        pass
    
    @abstractmethod
    async def log_service_deactivation(
        self,
        service: Service,
        deactivated_by: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log service deactivation event."""
        pass


class IAnalyticsService(ABC):
    """Analytics service interface for service insights."""
    
    @abstractmethod
    async def get_service_performance_metrics(
        self,
        service_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Get performance metrics for a service."""
        pass
    
    @abstractmethod
    async def get_category_performance_metrics(
        self,
        category_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Get performance metrics for a category."""
        pass
    
    @abstractmethod
    async def get_demand_forecast(
        self,
        service_id: str,
        forecast_days: int = 30,
    ) -> Dict[str, Any]:
        """Get demand forecast for a service."""
        pass
    
    @abstractmethod
    async def get_pricing_recommendations(
        self,
        service_id: str,
    ) -> Dict[str, Any]:
        """Get pricing recommendations based on analytics."""
        pass
    
    @abstractmethod
    async def get_service_comparison(
        self,
        service_ids: List[str],
        metrics: List[str],
    ) -> Dict[str, Any]:
        """Compare multiple services across metrics."""
        pass