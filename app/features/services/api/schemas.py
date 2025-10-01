from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class CreateCategorySchema(BaseModel):
    """Schema for creating a new category."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str = Field("", max_length=500, description="Category description")
    display_order: int = Field(0, ge=0, description="Display order")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate category name."""
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()


class CreateServiceSchema(BaseModel):
    """Schema for creating a new service."""
    category_id: str = Field(..., description="Category ID")
    name: str = Field(..., min_length=1, max_length=100, description="Service name")
    description: str = Field("", max_length=1000, description="Service description")
    price: Decimal = Field(..., gt=0, le=10000, description="Service price")
    duration_minutes: int = Field(..., gt=0, le=480, description="Duration in minutes")
    is_popular: bool = Field(False, description="Mark as popular service")
    display_order: int = Field(0, ge=0, description="Display order")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate service name."""
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()
    
    @validator('duration_minutes')
    def validate_duration_increment(cls, v):
        """Validate duration is in 15-minute increments."""
        if v % 15 != 0:
            raise ValueError('Duration must be in 15-minute increments')
        return v
    
    @validator('price')
    def validate_price_precision(cls, v):
        """Validate price precision."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price cannot have more than 2 decimal places')
        return v


class UpdateServicePriceSchema(BaseModel):
    """Schema for updating service price."""
    new_price: Decimal = Field(..., gt=0, le=10000, description="New service price")
    notify_customers: bool = Field(True, description="Notify affected customers")
    
    @validator('new_price')
    def validate_price_precision(cls, v):
        """Validate price precision."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price cannot have more than 2 decimal places')
        return v


class SetServicePopularSchema(BaseModel):
    """Schema for setting service popularity."""
    is_popular: bool = Field(..., description="Set as popular service")


class CategoryResponseSchema(BaseModel):
    """Schema for category response."""
    id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    status: str = Field(..., description="Category status")
    display_order: int = Field(..., description="Display order")
    service_count: Optional[int] = Field(None, description="Number of services in category")
    
    class Config:
        from_attributes = True


class ServiceResponseSchema(BaseModel):
    """Schema for service response."""
    id: str = Field(..., description="Service ID")
    category_id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    price: Decimal = Field(..., description="Service price")
    duration_minutes: int = Field(..., description="Duration in minutes")
    status: str = Field(..., description="Service status")
    is_popular: bool = Field(..., description="Is popular service")
    display_order: int = Field(..., description="Display order")
    price_display: str = Field(..., description="Formatted price")
    duration_display: str = Field(..., description="Formatted duration")
    
    class Config:
        from_attributes = True


class ServiceSummarySchema(BaseModel):
    """Schema for service summary in lists."""
    id: str = Field(..., description="Service ID")
    category_id: str = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    price: Decimal = Field(..., description="Service price")
    duration_minutes: int = Field(..., description="Duration in minutes")
    status: str = Field(..., description="Service status")
    is_popular: bool = Field(..., description="Is popular service")
    price_display: str = Field(..., description="Formatted price")
    duration_display: str = Field(..., description="Formatted duration")
    
    class Config:
        from_attributes = True


class ServiceListResponseSchema(BaseModel):
    """Schema for paginated service list response."""
    services: List[ServiceSummarySchema] = Field(..., description="List of services")
    total_count: int = Field(..., ge=0, description="Total number of services")
    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    filters_applied: dict = Field(..., description="Applied filters")
    
    class Config:
        from_attributes = True


class CreateCategoryResponseSchema(BaseModel):
    """Schema for create category response."""
    category_id: str = Field(..., description="Created category ID")
    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    status: str = Field(..., description="Category status")
    display_order: int = Field(..., description="Display order")
    
    class Config:
        from_attributes = True


class CreateServiceResponseSchema(BaseModel):
    """Schema for create service response."""
    service_id: str = Field(..., description="Created service ID")
    category_id: str = Field(..., description="Category ID")
    name: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    price: Decimal = Field(..., description="Service price")
    duration_minutes: int = Field(..., description="Duration in minutes")
    status: str = Field(..., description="Service status")
    is_popular: bool = Field(..., description="Is popular service")
    display_order: int = Field(..., description="Display order")
    price_display: str = Field(..., description="Formatted price")
    duration_display: str = Field(..., description="Formatted duration")
    
    class Config:
        from_attributes = True


class UpdateServicePriceResponseSchema(BaseModel):
    """Schema for update service price response."""
    service_id: str = Field(..., description="Service ID")
    old_price: Decimal = Field(..., description="Previous price")
    new_price: Decimal = Field(..., description="New price")
    price_change_percent: Decimal = Field(..., description="Price change percentage")
    affected_future_bookings: int = Field(..., description="Number of affected future bookings")
    customers_notified: int = Field(..., description="Number of customers notified")
    price_display: str = Field(..., description="Formatted new price")
    
    class Config:
        from_attributes = True


class SetServicePopularResponseSchema(BaseModel):
    """Schema for set service popular response."""
    service_id: str = Field(..., description="Service ID")
    name: str = Field(..., description="Service name")
    is_popular: bool = Field(..., description="Is popular service")
    category_popular_count: int = Field(..., description="Number of popular services in category")
    message: str = Field(..., description="Response message")
    
    class Config:
        from_attributes = True


class CategoryListResponseSchema(BaseModel):
    """Schema for category list response."""
    categories: List[CategoryResponseSchema] = Field(..., description="List of categories")
    total_count: int = Field(..., ge=0, description="Total number of categories")
    
    class Config:
        from_attributes = True


class PopularServicesResponseSchema(BaseModel):
    """Schema for popular services response."""
    services: List[ServiceSummarySchema] = Field(..., description="List of popular services")
    total_count: int = Field(..., ge=0, description="Total number of popular services")
    
    class Config:
        from_attributes = True