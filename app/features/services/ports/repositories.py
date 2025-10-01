from abc import ABC, abstractmethod
from typing import Optional, List
from decimal import Decimal

from app.features.services.domain import Category, Service


class ICategoryRepository(ABC):
    """Category repository interface."""
    
    @abstractmethod
    async def get_by_id(self, category_id: str) -> Optional[Category]:
        """Get category by ID."""
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        pass
    
    @abstractmethod
    async def create(self, category: Category) -> Category:
        """Create a new category."""
        pass
    
    @abstractmethod
    async def update(self, category: Category) -> Category:
        """Update an existing category."""
        pass
    
    @abstractmethod
    async def delete(self, category_id: str) -> bool:
        """Delete a category (hard delete)."""
        pass
    
    @abstractmethod
    async def list_all(
        self,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Category]:
        """List all categories."""
        pass
    
    @abstractmethod
    async def count(self, include_inactive: bool = False) -> int:
        """Count categories."""
        pass
    
    @abstractmethod
    async def list_active(self) -> List[Category]:
        """List active categories."""
        pass
    
    @abstractmethod
    async def count_services_in_category(
        self,
        category_id: str,
        include_inactive: bool = False,
    ) -> int:
        """Count services in a category."""
        pass
    
    @abstractmethod
    async def exists_by_name(
        self,
        name: str,
        exclude_category_id: Optional[str] = None,
    ) -> bool:
        """Check if category exists by name."""
        pass


class IServiceRepository(ABC):
    """Service repository interface."""
    
    @abstractmethod
    async def get_by_id(self, service_id: str) -> Optional[Service]:
        """Get service by ID."""
        pass
    
    @abstractmethod
    async def get_by_name_in_category(
        self,
        name: str,
        category_id: str,
    ) -> Optional[Service]:
        """Get service by name within a category."""
        pass
    
    @abstractmethod
    async def create(self, service: Service) -> Service:
        """Create a new service."""
        pass
    
    @abstractmethod
    async def update(self, service: Service) -> Service:
        """Update an existing service."""
        pass
    
    @abstractmethod
    async def delete(self, service_id: str) -> bool:
        """Delete a service (hard delete)."""
        pass
    
    @abstractmethod
    async def list_by_category(
        self,
        category_id: str,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Service]:
        """List services in a category."""
        pass
    
    @abstractmethod
    async def list_all(
        self,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Service]:
        """List all services."""
        pass
    
    @abstractmethod
    async def list_popular(self, limit: int = 10) -> List[Service]:
        """List popular services."""
        pass
    
    @abstractmethod
    async def list_by_price_range(
        self,
        min_price: Decimal,
        max_price: Decimal,
        category_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Service]:
        """List services within a price range."""
        pass
    
    @abstractmethod
    async def list_by_duration_range(
        self,
        min_duration: int,
        max_duration: int,
        category_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Service]:
        """List services within a duration range."""
        pass
    
    @abstractmethod
    async def count_by_category(
        self,
        category_id: str,
        include_inactive: bool = False,
    ) -> int:
        """Count services in a category."""
        pass
    
    @abstractmethod
    async def count_popular_in_category(self, category_id: str) -> int:
        """Count popular services in a category."""
        pass
    
    @abstractmethod
    async def exists_by_name_in_category(
        self,
        name: str,
        category_id: str,
        exclude_service_id: Optional[str] = None,
    ) -> bool:
        """Check if service exists by name in category."""
        pass
    
    @abstractmethod
    async def get_multiple_by_ids(self, service_ids: List[str]) -> List[Service]:
        """Get multiple services by their IDs."""
        pass
    
    @abstractmethod
    async def search_services(
        self,
        query: str,
        category_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Service]:
        """Search services by name or description."""
        pass


class IBookingRepository(ABC):
    """Booking repository interface for service statistics."""
    
    @abstractmethod
    async def count_bookings_for_service(
        self,
        service_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> int:
        """Count bookings for a service."""
        pass
    
    @abstractmethod
    async def get_service_revenue(
        self,
        service_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Decimal:
        """Get total revenue for a service."""
        pass
    
    @abstractmethod
    async def get_popular_services_by_bookings(
        self,
        limit: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[dict]:
        """Get most popular services by booking count."""
        pass