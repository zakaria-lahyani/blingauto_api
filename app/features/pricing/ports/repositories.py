"""
Pricing ports for repositories.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.entities import ServiceItem


class IServiceCatalogRepository(ABC):
    """Port for service catalog repository."""
    
    @abstractmethod
    async def get_service_by_id(self, service_id: str) -> Optional[ServiceItem]:
        """Get service by ID."""
        pass
    
    @abstractmethod
    async def get_services_by_ids(self, service_ids: List[str]) -> List[ServiceItem]:
        """Get multiple services by IDs."""
        pass
    
    @abstractmethod
    async def get_all_active_services(self) -> List[ServiceItem]:
        """Get all active services."""
        pass
    
    @abstractmethod
    async def is_service_active(self, service_id: str) -> bool:
        """Check if service is active."""
        pass