"""
Services Feature Configuration
"""
from typing import List, Optional, Dict
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class ServicesConfig(BaseSettings):
    """Services feature specific configuration"""
    
    # Feature settings
    table_prefix: str = Field(default="service_", description="Table prefix for service tables")
    cache_key_prefix: str = Field(default="service", description="Cache key prefix")
    
    # Business rules
    max_services_per_category: int = Field(default=50, description="Maximum services per category")
    max_categories: int = Field(default=20, description="Maximum service categories")
    allow_inactive_services: bool = Field(default=True, description="Allow inactive services to be shown")
    
    # Service validation
    min_service_duration_minutes: int = Field(default=5, description="Minimum service duration")
    max_service_duration_minutes: int = Field(default=480, description="Maximum service duration (8 hours)")
    min_service_price: float = Field(default=0.0, description="Minimum service price")
    max_service_price: float = Field(default=10000.0, description="Maximum service price")
    
    # Default values
    default_service_duration: int = Field(default=30, description="Default service duration in minutes")
    default_currency: str = Field(default="USD", description="Default currency for pricing")
    
    # Service pricing
    allow_zero_price_services: bool = Field(default=True, description="Allow free services")
    require_price_for_active: bool = Field(default=False, description="Require price for active services")
    
    # Category management
    auto_create_default_category: bool = Field(default=True, description="Auto-create default category")
    default_category_name: str = Field(default="General Services", description="Default category name")
    allow_empty_categories: bool = Field(default=False, description="Allow categories with no services")
    
    # Soft delete behavior
    soft_delete_services: bool = Field(default=True, description="Use soft delete for services")
    soft_delete_categories: bool = Field(default=True, description="Use soft delete for categories")
    cascade_category_delete: bool = Field(default=False, description="Delete services when category deleted")
    
    # Performance
    cache_service_list_ttl: int = Field(default=1800, description="Cache TTL for service lists (30 min)")
    cache_category_list_ttl: int = Field(default=3600, description="Cache TTL for category lists (1 hour)")
    cache_service_detail_ttl: int = Field(default=600, description="Cache TTL for service details")
    
    # Search and filtering
    enable_service_search: bool = Field(default=True, description="Enable service search functionality")
    search_min_chars: int = Field(default=2, description="Minimum characters for search")
    max_search_results: int = Field(default=100, description="Maximum search results")
    
    # Audit settings
    track_service_changes: bool = Field(default=True, description="Track service modifications")
    track_price_changes: bool = Field(default=True, description="Track price changes specifically")
    
    class Config:
        env_prefix = "SERVICES_"
        extra = "ignore"
    
    @validator("max_services_per_category")
    def validate_max_services(cls, v):
        """Ensure max services is positive"""
        if v < 1:
            raise ValueError("Max services per category must be at least 1")
        return v
    
    @validator("min_service_duration_minutes", "max_service_duration_minutes")
    def validate_duration_positive(cls, v):
        """Ensure durations are positive"""
        if v < 1:
            raise ValueError("Service duration must be positive")
        return v
    
    @validator("max_service_duration_minutes")
    def validate_max_duration(cls, v, values):
        """Ensure max duration is greater than min"""
        min_duration = values.get("min_service_duration_minutes", 5)
        if v <= min_duration:
            raise ValueError("Max duration must be greater than min duration")
        return v
    
    @validator("max_service_price")
    def validate_max_price(cls, v, values):
        """Ensure max price is greater than min"""
        min_price = values.get("min_service_price", 0.0)
        if v <= min_price:
            raise ValueError("Max price must be greater than min price")
        return v
    
    def is_valid_service_price(self, price: float) -> bool:
        """Check if service price is valid"""
        if not self.allow_zero_price_services and price == 0.0:
            return False
        return self.min_service_price <= price <= self.max_service_price
    
    def is_valid_service_duration(self, duration_minutes: int) -> bool:
        """Check if service duration is valid"""
        return self.min_service_duration_minutes <= duration_minutes <= self.max_service_duration_minutes
    
    def get_cache_key_for_category_services(self, category_id: str) -> str:
        """Get cache key for category's service list"""
        return f"{self.cache_key_prefix}:category:{category_id}:services"
    
    def get_cache_key_for_service(self, service_id: str) -> str:
        """Get cache key for specific service"""
        return f"{self.cache_key_prefix}:service:{service_id}"
    
    def get_cache_key_for_active_services(self) -> str:
        """Get cache key for active services list"""
        return f"{self.cache_key_prefix}:active_services"


# Singleton instance
_services_config: Optional[ServicesConfig] = None


def get_services_config() -> ServicesConfig:
    """Get services configuration singleton"""
    global _services_config
    if _services_config is None:
        _services_config = ServicesConfig()
    return _services_config