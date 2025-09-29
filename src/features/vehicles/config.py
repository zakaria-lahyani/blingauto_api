"""
Vehicle Feature Configuration
"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class VehicleConfig(BaseSettings):
    """Vehicle feature specific configuration"""
    
    # Feature settings
    table_prefix: str = Field(default="vehicle_", description="Table prefix for vehicle tables")
    cache_key_prefix: str = Field(default="vehicle", description="Cache key prefix")
    
    # Business rules
    max_vehicles_per_user: int = Field(default=10, description="Maximum vehicles per user")
    allow_duplicate_plates: bool = Field(default=False, description="Allow duplicate license plates")
    require_unique_plates: bool = Field(default=True, description="Require unique license plates")
    
    # Vehicle validation
    min_vehicle_year: int = Field(default=1900, description="Minimum vehicle year")
    max_future_years: int = Field(default=2, description="Max years in the future for vehicle year")
    
    # Default values
    default_vehicle_size: str = Field(default="standard", description="Default vehicle size")
    valid_vehicle_sizes: List[str] = Field(
        default=["compact", "standard", "large", "oversized"],
        description="Valid vehicle size options"
    )
    
    # License plate validation
    min_plate_length: int = Field(default=2, description="Minimum license plate length")
    max_plate_length: int = Field(default=20, description="Maximum license plate length")
    plate_regex_pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern for license plate validation"
    )
    
    # Soft delete behavior
    soft_delete_vehicles: bool = Field(default=True, description="Use soft delete for vehicles")
    auto_deactivate_on_delete: bool = Field(default=True, description="Auto deactivate on delete")
    
    # Performance
    cache_vehicle_list_ttl: int = Field(default=600, description="Cache TTL for vehicle lists")
    cache_vehicle_detail_ttl: int = Field(default=300, description="Cache TTL for vehicle details")
    
    # Audit settings
    track_vehicle_changes: bool = Field(default=True, description="Track vehicle modifications")
    
    class Config:
        env_prefix = "VEHICLE_"
        extra = "ignore"
    
    @validator("valid_vehicle_sizes")
    def validate_vehicle_sizes(cls, v):
        """Ensure at least one valid vehicle size"""
        if not v or len(v) == 0:
            raise ValueError("At least one valid vehicle size must be configured")
        return v
    
    @validator("max_vehicles_per_user")
    def validate_max_vehicles(cls, v):
        """Ensure max vehicles is positive"""
        if v < 1:
            raise ValueError("Max vehicles per user must be at least 1")
        return v
    
    def is_valid_vehicle_size(self, size: str) -> bool:
        """Check if vehicle size is valid"""
        return size in self.valid_vehicle_sizes
    
    def get_cache_key_for_user_vehicles(self, user_id: str) -> str:
        """Get cache key for user's vehicle list"""
        return f"{self.cache_key_prefix}:user:{user_id}:vehicles"
    
    def get_cache_key_for_vehicle(self, vehicle_id: str) -> str:
        """Get cache key for specific vehicle"""
        return f"{self.cache_key_prefix}:vehicle:{vehicle_id}"


# Singleton instance
_vehicle_config: Optional[VehicleConfig] = None


def get_vehicle_config() -> VehicleConfig:
    """Get vehicle configuration singleton"""
    global _vehicle_config
    if _vehicle_config is None:
        _vehicle_config = VehicleConfig()
    return _vehicle_config