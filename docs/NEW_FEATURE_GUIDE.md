# 🎯 Adding New Features - Step-by-Step Guide

## Overview

This guide shows exactly how to add a new feature to the refactored Car Wash API, using the existing auth feature as a template and maintaining the clean architecture.

## 🏗️ Feature Structure Template

Every feature follows this exact structure:

```
src/features/{feature_name}/
├── __init__.py                    # Feature public interface
├── config.py                     # Feature configuration
├── {feature_name}_module.py      # Main feature module
├── domain/
│   ├── __init__.py
│   ├── entities.py               # Business entities
│   ├── enums.py                  # Domain enumerations
│   └── events.py                 # Domain events
├── application/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       └── {service_name}.py     # Business logic services
├── infrastructure/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy models
│   │   └── repositories.py      # Data access layer
│   └── security/                 # Feature-specific security (if needed)
│       ├── __init__.py
│       └── {security_component}.py
└── presentation/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── router.py             # FastAPI routes
    │   ├── schemas.py            # Request/response models
    │   └── dependencies.py      # API dependencies
    └── middleware/               # Feature-specific middleware (if needed)
        ├── __init__.py
        └── {middleware_name}.py
```

## 🎪 Example: Creating a Booking Feature

Let's create a complete booking feature step by step:

### Step 1: Create Feature Directory Structure

```bash
mkdir -p src/features/booking/{domain,application/services,infrastructure/database,presentation/api}
touch src/features/booking/__init__.py
touch src/features/booking/config.py
touch src/features/booking/booking_module.py
touch src/features/booking/domain/{__init__.py,entities.py,enums.py,events.py}
touch src/features/booking/application/{__init__.py,services/__init__.py,services/booking_service.py}
touch src/features/booking/infrastructure/{__init__.py,database/__init__.py,database/models.py,database/repositories.py}
touch src/features/booking/presentation/{__init__.py,api/__init__.py,api/router.py,api/schemas.py,api/dependencies.py}
```

### Step 2: Define Configuration

**`src/features/booking/config.py`**
```python
"""
Booking Feature Configuration
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum


class BookingFeature(str, Enum):
    """Available booking features"""
    SERVICE_CATALOG = "service_catalog"
    ONLINE_BOOKING = "online_booking"
    STAFF_ASSIGNMENT = "staff_assignment"
    BOOKING_NOTIFICATIONS = "booking_notifications"
    RECURRING_BOOKINGS = "recurring_bookings"


class BookingConfig(BaseSettings):
    """Booking feature configuration"""
    
    # Core settings
    enabled_features: List[BookingFeature] = Field(
        default=[
            BookingFeature.SERVICE_CATALOG,
            BookingFeature.ONLINE_BOOKING,
            BookingFeature.STAFF_ASSIGNMENT,
            BookingFeature.BOOKING_NOTIFICATIONS
        ]
    )
    
    # Database settings
    table_prefix: str = Field(default="booking_")
    
    # Business rules
    max_advance_booking_days: int = Field(default=30)
    min_advance_booking_hours: int = Field(default=2)
    max_concurrent_bookings_per_user: int = Field(default=3)
    default_booking_duration_minutes: int = Field(default=60)
    
    # Scheduling
    business_hours_start: int = Field(default=8)  # 8 AM
    business_hours_end: int = Field(default=18)   # 6 PM
    booking_slot_duration_minutes: int = Field(default=30)
    
    # Notifications
    reminder_hours_before: List[int] = Field(default=[24, 2])
    
    class Config:
        env_prefix = "BOOKING_"
        env_file = ".env"
        case_sensitive = False
    
    def is_feature_enabled(self, feature: BookingFeature) -> bool:
        """Check if a feature is enabled"""
        return feature in self.enabled_features
    
    def get_table_name(self, base_name: str) -> str:
        """Get prefixed table name"""
        return f"{self.table_prefix}{base_name}"
```

### Step 3: Define Domain Entities

**`src/features/booking/domain/enums.py`**
```python
"""
Booking domain enumerations
"""
from enum import Enum


class BookingStatus(str, Enum):
    """Booking status values"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ServiceCategory(str, Enum):
    """Service category types"""
    BASIC = "basic"
    PREMIUM = "premium"
    DELUXE = "deluxe"
    CUSTOM = "custom"


class VehicleType(str, Enum):
    """Vehicle type classifications"""
    SEDAN = "sedan"
    SUV = "suv"
    TRUCK = "truck"
    MOTORCYCLE = "motorcycle"
    VAN = "van"
```

**`src/features/booking/domain/entities.py`**
```python
"""
Booking domain entities
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from .enums import BookingStatus, ServiceCategory, VehicleType


@dataclass
class WashService:
    """Wash service entity"""
    
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    category: ServiceCategory = ServiceCategory.BASIC
    duration_minutes: int = 60
    base_price_cents: int = 0
    
    # Vehicle type pricing
    pricing_by_vehicle: Dict[VehicleType, int] = field(default_factory=dict)
    
    # Service details
    features: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_price_for_vehicle(self, vehicle_type: VehicleType) -> int:
        """Get price for specific vehicle type"""
        return self.pricing_by_vehicle.get(vehicle_type, self.base_price_cents)


@dataclass
class Booking:
    """Booking entity"""
    
    id: UUID = field(default_factory=uuid4)
    
    # References (managed at application level)
    customer_id: UUID = field(default=None)
    service_id: UUID = field(default=None)
    washer_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    
    # Scheduling
    scheduled_at: datetime = field(default=None)
    duration_minutes: int = 60
    status: BookingStatus = BookingStatus.PENDING
    
    # Vehicle information
    vehicle_type: VehicleType = VehicleType.SEDAN
    vehicle_info: Dict[str, Any] = field(default_factory=dict)
    
    # Service details
    special_instructions: str = ""
    estimated_price_cents: int = 0
    final_price_cents: Optional[int] = None
    
    # Status tracking
    confirmed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: str = ""
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def confirm(self) -> None:
        """Confirm the booking"""
        self.status = BookingStatus.CONFIRMED
        self.confirmed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def start_service(self) -> None:
        """Start the service"""
        self.status = BookingStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_service(self, final_price_cents: Optional[int] = None) -> None:
        """Complete the service"""
        self.status = BookingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if final_price_cents is not None:
            self.final_price_cents = final_price_cents
        self.updated_at = datetime.utcnow()
    
    def cancel(self, reason: str = "") -> None:
        """Cancel the booking"""
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        self.updated_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if booking is in an active state"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]
    
    @property
    def estimated_end_time(self) -> datetime:
        """Calculate estimated end time"""
        return self.scheduled_at + timedelta(minutes=self.duration_minutes)
```

### Step 4: Define Domain Events

**`src/features/booking/domain/events.py`**
```python
"""
Booking domain events
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from shared.events import DomainEvent


@dataclass
class BookingCreated(DomainEvent):
    """Booking created event"""
    booking_id: UUID
    customer_id: UUID
    service_id: UUID
    scheduled_at: datetime
    estimated_price_cents: int


@dataclass
class BookingConfirmed(DomainEvent):
    """Booking confirmed event"""
    booking_id: UUID
    customer_id: UUID
    washer_id: Optional[UUID]
    scheduled_at: datetime


@dataclass
class BookingStarted(DomainEvent):
    """Booking service started event"""
    booking_id: UUID
    customer_id: UUID
    washer_id: UUID
    started_at: datetime


@dataclass
class BookingCompleted(DomainEvent):
    """Booking completed event"""
    booking_id: UUID
    customer_id: UUID
    washer_id: UUID
    completed_at: datetime
    final_price_cents: int


@dataclass
class BookingCancelled(DomainEvent):
    """Booking cancelled event"""
    booking_id: UUID
    customer_id: UUID
    cancelled_at: datetime
    cancellation_reason: str
    refund_amount_cents: int
```

### Step 5: Create Database Models

**`src/features/booking/infrastructure/database/models.py`**
```python
"""
Booking database models
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
from uuid import uuid4

from shared.database import Base


class WashServiceModel(Base):
    """Wash service database model"""
    
    __tablename__ = "booking_services"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Service details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(20), nullable=False, default="basic")
    duration_minutes = Column(Integer, nullable=False, default=60)
    base_price_cents = Column(Integer, nullable=False, default=0)
    
    # Pricing and features
    pricing_by_vehicle = Column(JSON, default={})
    features = Column(JSON, default=[])
    requirements = Column(JSON, default=[])
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class BookingModel(Base):
    """Booking database model"""
    
    __tablename__ = "booking_reservations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # References (no FK constraints for loose coupling)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    washer_id = Column(UUID(as_uuid=True))
    location_id = Column(UUID(as_uuid=True))
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    status = Column(String(20), nullable=False, default="pending")
    
    # Vehicle information
    vehicle_type = Column(String(20), nullable=False, default="sedan")
    vehicle_info = Column(JSON, default={})
    
    # Service details
    special_instructions = Column(Text)
    estimated_price_cents = Column(Integer, nullable=False, default=0)
    final_price_cents = Column(Integer)
    
    # Status timestamps
    confirmed_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    
    # Audit timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
```

### Step 6: Create Feature Module

**`src/features/booking/booking_module.py`**
```python
"""
Booking Feature Module
"""
import logging
from typing import Dict, Any

from .config import BookingConfig, BookingFeature

logger = logging.getLogger(__name__)


class BookingModule:
    """Booking feature module"""
    
    def __init__(self, config: BookingConfig):
        self.config = config
        self._initialized = False
        
        # Services will be initialized lazily
        self._booking_service = None
    
    def setup(self, app, prefix: str = "/booking"):
        """Setup booking module with FastAPI app"""
        from .presentation.api.router import create_booking_router
        
        router = create_booking_router(self)
        app.include_router(router, prefix=prefix, tags=["Booking"])
        
        logger.info(f"Booking module setup complete with prefix: {prefix}")
    
    async def initialize(self):
        """Initialize booking module"""
        if self._initialized:
            return
        
        try:
            # Initialize database tables
            await self._setup_database()
            
            self._initialized = True
            logger.info("Booking module initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize booking module: {e}")
            raise
    
    async def _setup_database(self):
        """Setup booking database tables"""
        from .infrastructure.database.models import WashServiceModel, BookingModel
        from shared.database import get_engine
        
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(WashServiceModel.metadata.create_all)
            await conn.run_sync(BookingModel.metadata.create_all)
        
        logger.info("Booking database tables created")
    
    @property
    def booking_service(self):
        """Get booking service"""
        if self._booking_service is None:
            from .application.services.booking_service import BookingService
            self._booking_service = BookingService(self.config)
        return self._booking_service
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of booking features"""
        return {
            feature.value: self.config.is_feature_enabled(feature)
            for feature in BookingFeature
        }
```

### Step 7: Create Public Interface

**`src/features/booking/__init__.py`**
```python
"""
Booking Feature Module - Standalone & Reusable

Complete booking system for wash services:

🎯 FEATURES:
- Service catalog management
- Online booking system
- Staff assignment
- Booking notifications
- Vehicle type support
- Flexible pricing

🚀 INTEGRATION:
    from features.booking import BookingModule, BookingConfig
    
    # 1. Create booking module
    booking = BookingModule(BookingConfig())
    
    # 2. Setup with FastAPI app
    booking.setup(app, prefix="/booking")
    
    # 3. Initialize (in startup event)
    await booking.initialize()

📋 AVAILABLE ENDPOINTS:
- POST /booking/services - Create wash service
- GET /booking/services - List available services
- POST /booking/reservations - Create booking
- GET /booking/reservations - List bookings
- PUT /booking/reservations/{id}/confirm - Confirm booking
- PUT /booking/reservations/{id}/start - Start service
- PUT /booking/reservations/{id}/complete - Complete service
- DELETE /booking/reservations/{id} - Cancel booking
"""

from .config import BookingConfig, BookingFeature
from .booking_module import BookingModule
from .domain.entities import Booking, WashService
from .domain.enums import BookingStatus, ServiceCategory, VehicleType

__all__ = [
    # Core module
    'BookingModule', 
    'BookingConfig', 
    'BookingFeature',
    
    # Domain entities
    'Booking', 
    'WashService',
    'BookingStatus',
    'ServiceCategory', 
    'VehicleType'
]
```

## 🔗 Integration with Main Application

### Update main.py to include the new feature:

```python
# main.py
from features.auth import AuthModule, AuthConfig
from features.booking import BookingModule, BookingConfig  # Add this

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Initialize database
    init_database(database_url)
    
    # Setup auth module
    auth_config = AuthConfig()
    auth_module = AuthModule(auth_config)
    auth_module.setup(app, prefix="/auth")
    
    # Setup booking module  
    booking_config = BookingConfig()  # Add this
    booking_module = BookingModule(booking_config)  # Add this
    booking_module.setup(app, prefix="/booking")  # Add this
    
    # Store modules for access in endpoints
    app.state.auth = auth_module
    app.state.booking = booking_module  # Add this
    
    @app.on_event("startup")
    async def startup_event():
        await auth_module.initialize()
        await booking_module.initialize()  # Add this
    
    return app
```

## 📋 Table Creation Verification

After adding the booking feature, these tables will be created:

```sql
-- Auth feature tables (existing)
auth_users

-- Booking feature tables (new)
booking_services
booking_reservations
```

Check with:
```sql
-- List all tables
\dt

-- Describe booking tables
\d booking_services
\d booking_reservations
```

## 🔄 Inter-Feature Communication

### Using the booking feature with auth:

```python
# In a booking endpoint
@router.post("/reservations")
async def create_booking(
    booking_data: CreateBookingRequest,
    current_user: AuthUser = Depends(auth_module.get_current_user)  # Auth integration
):
    # Use the authenticated user
    booking = await booking_module.booking_service.create_booking(
        customer_id=current_user.id,  # From auth feature
        service_id=booking_data.service_id,
        scheduled_at=booking_data.scheduled_at
    )
    return booking
```

## ✅ Checklist for New Features

When creating a new feature, ensure you have:

- [ ] **Config**: Feature configuration with environment variables
- [ ] **Entities**: Domain entities with business logic
- [ ] **Enums**: Domain enumerations for type safety
- [ ] **Events**: Domain events for inter-feature communication
- [ ] **Models**: SQLAlchemy models with proper table names
- [ ] **Repositories**: Data access layer
- [ ] **Services**: Business logic services
- [ ] **Module**: Main feature module with setup/initialization
- [ ] **Router**: FastAPI routes and endpoints
- [ ] **Schemas**: Request/response models
- [ ] **Dependencies**: Feature-specific dependencies
- [ ] **Public Interface**: Clean __init__.py with exports
- [ ] **Integration**: Added to main.py
- [ ] **Testing**: Feature-specific tests

This pattern ensures consistency, maintainability, and scalability across all features in your application.