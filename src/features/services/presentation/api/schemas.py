"""
Services API schemas
"""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator

from src.features.services.domain.enums import ServiceStatus, CategoryStatus, ServiceSortBy, CategorySortBy


# Category Schemas
class CategoryCreate(BaseModel):
    """Schema for creating a service category"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CategoryUpdate(BaseModel):
    """Schema for updating a service category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Category name cannot be empty')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class CategoryResponse(BaseModel):
    """Schema for category response"""
    id: UUID
    name: str
    description: Optional[str]
    status: CategoryStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CategoryListResponse(BaseModel):
    """Schema for category list response"""
    categories: List[CategoryResponse]
    total: int
    page: int
    size: int
    pages: int


# Service Schemas
class ServiceCreate(BaseModel):
    """Schema for creating a service"""
    name: str = Field(..., min_length=1, max_length=100, description="Service name")
    price: Decimal = Field(..., gt=0, description="Service price")
    duration: int = Field(..., gt=0, description="Service duration in minutes")
    category_id: UUID = Field(..., description="Category ID")
    description: Optional[str] = Field(None, description="Service description")
    point_description: Optional[List[str]] = Field(None, description="Service key points")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('point_description')
    def validate_point_description(cls, v):
        if v is not None:
            return [point.strip() for point in v if point.strip()]
        return v


class ServiceUpdate(BaseModel):
    """Schema for updating a service"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Service name")
    price: Optional[Decimal] = Field(None, gt=0, description="Service price")
    duration: Optional[int] = Field(None, gt=0, description="Service duration in minutes")
    category_id: Optional[UUID] = Field(None, description="Category ID")
    description: Optional[str] = Field(None, description="Service description")
    point_description: Optional[List[str]] = Field(None, description="Service key points")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Service name cannot be empty')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @validator('point_description')
    def validate_point_description(cls, v):
        if v is not None:
            return [point.strip() for point in v if point.strip()]
        return v


class ServiceResponse(BaseModel):
    """Schema for service response"""
    id: UUID
    name: str
    price: Decimal
    duration: int
    category_id: UUID
    description: Optional[str]
    point_description: List[str]
    status: ServiceStatus
    popular: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceWithCategoryResponse(BaseModel):
    """Schema for service response with category details"""
    id: UUID
    name: str
    price: Decimal
    duration: int
    category_id: UUID
    category_name: str
    description: Optional[str]
    point_description: List[str]
    status: ServiceStatus
    popular: bool
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(BaseModel):
    """Schema for service list response"""
    services: List[ServiceResponse]
    total: int
    page: int
    size: int
    pages: int


class ServiceSearchResponse(BaseModel):
    """Schema for service search response"""
    services: List[ServiceWithCategoryResponse]
    total: int
    page: int
    size: int
    pages: int
    query: str


# Query Parameter Schemas
class CategoryListParams(BaseModel):
    """Query parameters for category listing"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    status: Optional[CategoryStatus] = Field(None, description="Filter by status")
    search: Optional[str] = Field(None, description="Search in name and description")
    sort_by: CategorySortBy = Field(CategorySortBy.NAME, description="Sort field")
    sort_desc: bool = Field(False, description="Sort descending")


class ServiceListParams(BaseModel):
    """Query parameters for service listing"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    category_id: Optional[UUID] = Field(None, description="Filter by category")
    status: Optional[ServiceStatus] = Field(None, description="Filter by status")
    popular_only: bool = Field(False, description="Show only popular services")
    search: Optional[str] = Field(None, description="Search in name and description")
    sort_by: ServiceSortBy = Field(ServiceSortBy.NAME, description="Sort field")
    sort_desc: bool = Field(False, description="Sort descending")


class ServiceSearchParams(BaseModel):
    """Query parameters for service search"""
    q: str = Field(..., min_length=1, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    category_id: Optional[UUID] = Field(None, description="Filter by category")
    active_only: bool = Field(True, description="Show only active services")


# Status Update Schemas
class CategoryStatusUpdate(BaseModel):
    """Schema for updating category status"""
    status: CategoryStatus


class ServiceStatusUpdate(BaseModel):
    """Schema for updating service status"""
    status: ServiceStatus


class ServicePopularUpdate(BaseModel):
    """Schema for updating service popular flag"""
    popular: bool


# Response Models
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str