# 🗄️ Database Schema & Architecture Documentation

## Overview

This document provides comprehensive documentation about the database schema, table relationships, and how the feature-based architecture manages data across different features in the refactored Car Wash API.

## 🏗️ Architecture Principles

### Feature-Based Data Organization
- **Each feature owns its data**: Features manage their own tables and relationships
- **Shared entities**: Common entities (like User) can be extended by features
- **Loose coupling**: Features communicate through events, not direct database dependencies
- **Configurable prefixes**: Table names can be prefixed per feature for multi-tenancy

### Database Design Philosophy
- **Domain-Driven Design (DDD)**: Tables reflect business domains
- **Event Sourcing Ready**: Events can be stored for audit trails
- **Scalable Architecture**: Easy to add new features without schema conflicts
- **Clear Ownership**: Each table belongs to a specific feature

## 📊 Current Database Schema

### 🔐 Auth Feature Tables

The auth feature manages all authentication-related data:

#### 1. `auth_users` (Primary Table)
```sql
CREATE TABLE auth_users (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                       VARCHAR(255) NOT NULL UNIQUE,
    password_hash               VARCHAR(255) NOT NULL,
    first_name                  VARCHAR(100) NOT NULL,
    last_name                   VARCHAR(100) NOT NULL,
    phone                       VARCHAR(20),
    role                        VARCHAR(20) NOT NULL DEFAULT 'client',
    is_active                   BOOLEAN NOT NULL DEFAULT true,
    
    -- Email verification
    email_verified              BOOLEAN NOT NULL DEFAULT false,
    email_verified_at           TIMESTAMP,
    email_verification_token    VARCHAR(255),
    email_verification_expires  TIMESTAMP,
    
    -- Password reset
    password_reset_token        VARCHAR(255),
    password_reset_expires      TIMESTAMP,
    password_reset_requested_at TIMESTAMP,
    password_changed_at         TIMESTAMP,
    
    -- Account lockout
    failed_login_attempts       INTEGER NOT NULL DEFAULT 0,
    locked_until               TIMESTAMP,
    lockout_count              INTEGER NOT NULL DEFAULT 0,
    last_failed_login          TIMESTAMP,
    
    -- Session management
    last_login                 TIMESTAMP,
    refresh_tokens             JSON DEFAULT '[]',
    
    -- Timestamps
    created_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_auth_users_email ON auth_users(email);
CREATE INDEX idx_auth_users_role ON auth_users(role);
CREATE INDEX idx_auth_users_is_active ON auth_users(is_active);
CREATE INDEX idx_auth_users_email_verification_token ON auth_users(email_verification_token);
CREATE INDEX idx_auth_users_password_reset_token ON auth_users(password_reset_token);
CREATE INDEX idx_auth_users_locked_until ON auth_users(locked_until);
```

**Field Descriptions:**

| Field | Purpose | Feature |
|-------|---------|---------|
| `id, email, password_hash, first_name, last_name` | Core user identity | Core Auth |
| `phone, role, is_active` | User profile and permissions | Core Auth |
| `email_verified, email_verified_at, email_verification_token, email_verification_expires` | Email verification system | Email Verification |
| `password_reset_token, password_reset_expires, password_reset_requested_at, password_changed_at` | Password reset functionality | Password Reset |
| `failed_login_attempts, locked_until, lockout_count, last_failed_login` | Account lockout protection | Account Lockout |
| `last_login, refresh_tokens` | Session and token management | Token Rotation |
| `created_at, updated_at` | Audit timestamps | Core Auth |

#### 2. Potential Future Auth Tables

As features grow, the auth module might add these tables:

```sql
-- User sessions (if detailed session tracking is needed)
CREATE TABLE auth_user_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    session_token   VARCHAR(255) NOT NULL UNIQUE,
    device_info     JSON,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true
);

-- Login attempts (for detailed security auditing)
CREATE TABLE auth_login_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL,
    user_id         UUID REFERENCES auth_users(id) ON DELETE SET NULL,
    ip_address      INET,
    user_agent      TEXT,
    success         BOOLEAN NOT NULL,
    failure_reason  VARCHAR(100),
    attempted_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- OAuth providers (if social login is added)
CREATE TABLE auth_oauth_providers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    provider        VARCHAR(50) NOT NULL, -- 'google', 'facebook', etc.
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email  VARCHAR(255),
    access_token    TEXT,
    refresh_token   TEXT,
    token_expires   TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(provider, provider_user_id)
);
```

### 🎯 Role Hierarchy & Permissions

The auth system uses a simple role-based hierarchy stored in the `role` field:

```
Admin (highest privileges)
  └── Can manage: Everyone
      ├── Manager
      │   └── Can manage: Washers, Clients
      ├── Washer  
      │   └── Can manage: Own profile
      └── Client (lowest privileges)
          └── Can manage: Own profile
```

**Role Definitions:**
- `admin`: Full system access, user management, system configuration
- `manager`: Business operations, staff management, reporting
- `washer`: Service execution, task management
- `client`: Service consumption, booking management

## 🔄 Future Feature Integration

### 🧽 Wash Service Feature (Planned)

When adding a wash service feature, it would create its own tables:

```sql
-- Wash services offered
CREATE TABLE wash_services (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    duration_minutes INTEGER NOT NULL,
    price_cents     INTEGER NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Customer bookings
CREATE TABLE wash_bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID NOT NULL, -- References auth_users(id)
    service_id      UUID NOT NULL REFERENCES wash_services(id),
    washer_id       UUID, -- References auth_users(id) where role='washer'
    
    -- Booking details
    scheduled_at    TIMESTAMP NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    vehicle_info    JSON,
    special_instructions TEXT,
    
    -- Pricing
    price_cents     INTEGER NOT NULL,
    paid_at         TIMESTAMP,
    payment_method  VARCHAR(20),
    
    -- Timestamps
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints handled at application level
    -- to avoid tight coupling between features
    CONSTRAINT chk_booking_status CHECK (status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled'))
);

-- Booking status history
CREATE TABLE wash_booking_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID NOT NULL REFERENCES wash_bookings(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL,
    changed_by      UUID, -- References auth_users(id)
    notes           TEXT,
    changed_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 💰 Payment Feature (Planned)

```sql
-- Payment transactions
CREATE TABLE payment_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id     UUID NOT NULL, -- References auth_users(id)
    booking_id      UUID, -- References wash_bookings(id)
    
    -- Transaction details
    amount_cents    INTEGER NOT NULL,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_method  VARCHAR(20) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- External payment processor
    processor       VARCHAR(20), -- 'stripe', 'paypal', etc.
    processor_transaction_id VARCHAR(255),
    processor_response JSON,
    
    -- Timestamps
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded'))
);
```

### 📍 Location Feature (Planned)

```sql
-- Wash locations
CREATE TABLE wash_locations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    address         TEXT NOT NULL,
    city            VARCHAR(50) NOT NULL,
    state           VARCHAR(20) NOT NULL,
    zip_code        VARCHAR(10) NOT NULL,
    country         VARCHAR(2) NOT NULL DEFAULT 'US',
    
    -- Geographic coordinates
    latitude        DECIMAL(10, 8),
    longitude       DECIMAL(11, 8),
    
    -- Operational details
    phone           VARCHAR(20),
    email           VARCHAR(255),
    operating_hours JSON,
    services_offered UUID[], -- Array of wash_services IDs
    max_concurrent_bookings INTEGER DEFAULT 5,
    
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Staff assignments to locations
CREATE TABLE wash_location_staff (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id     UUID NOT NULL REFERENCES wash_locations(id) ON DELETE CASCADE,
    staff_id        UUID NOT NULL, -- References auth_users(id) where role IN ('washer', 'manager')
    role            VARCHAR(20) NOT NULL,
    assigned_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    
    UNIQUE(location_id, staff_id)
);
```

## 🔗 Inter-Feature Relationships

### Relationship Management Strategy

**1. Loose Coupling via Application Layer:**
```python
# ❌ Avoid: Direct foreign key constraints between features
ALTER TABLE wash_bookings ADD CONSTRAINT fk_customer 
    FOREIGN KEY (customer_id) REFERENCES auth_users(id);

# ✅ Preferred: Application-level relationships
class BookingService:
    async def create_booking(self, customer_id: UUID, ...):
        # Verify customer exists via auth module
        customer = await auth_module.user_service.get_user_by_id(customer_id)
        if not customer:
            raise ValueError("Customer not found")
        
        # Create booking
        booking = await self._booking_repo.create(...)
```

**2. Event-Driven Communication:**
```python
# When user is deleted, publish event
await event_bus.publish(UserDeleted(user_id=user.id))

# Other features listen and clean up their data
class BookingEventHandler:
    async def handle_user_deleted(self, event: UserDeleted):
        await self._booking_service.cancel_user_bookings(event.user_id)
```

**3. Shared Value Objects:**
```python
# Common types used across features
@dataclass
class UserReference:
    id: UUID
    email: str
    role: str
    name: str

# Features use shared references instead of direct relationships
class Booking:
    customer: UserReference  # Not a direct DB relationship
    washer: Optional[UserReference] = None
```

## 📋 Table Naming Conventions

### Feature Prefixes
Each feature can have its own table prefix for organization:

```python
# Auth feature configuration
AUTH_TABLE_PREFIX = "auth_"
# Results in: auth_users, auth_sessions, etc.

# Booking feature configuration  
BOOKING_TABLE_PREFIX = "booking_"
# Results in: booking_services, booking_reservations, etc.

# Payment feature configuration
PAYMENT_TABLE_PREFIX = "payment_"
# Results in: payment_transactions, payment_methods, etc.
```

### Naming Rules
1. **Feature prefix**: `{feature}_` (e.g., `auth_`, `booking_`)
2. **Plural nouns**: Tables represent collections (`users`, not `user`)
3. **Snake case**: All lowercase with underscores (`wash_services`)
4. **Descriptive**: Clear purpose (`user_sessions`, not `sessions`)

## 🔧 Database Configuration

### Environment Variables
```bash
# Core database settings
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/carwash_db
DB_ECHO=false

# Feature-specific prefixes (optional)
AUTH_TABLE_PREFIX=auth_
BOOKING_TABLE_PREFIX=booking_
PAYMENT_TABLE_PREFIX=payment_

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
```

### Auto-Migration Strategy
```python
# Each feature manages its own migrations
class AuthModule:
    async def setup_database(self):
        """Create auth-specific tables"""
        from .infrastructure.database.models import AuthUserModel
        
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(AuthUserModel.metadata.create_all)
    
    async def migrate_database(self, target_version: str):
        """Run auth-specific migrations"""
        # Migration logic here
        pass
```

## 🔍 Query Patterns

### Cross-Feature Queries
```python
# ❌ Avoid: Direct cross-feature database joins
SELECT b.*, u.email, u.first_name 
FROM booking_reservations b 
JOIN auth_users u ON b.customer_id = u.id;

# ✅ Preferred: Service layer composition
class BookingService:
    async def get_booking_with_customer(self, booking_id: UUID):
        booking = await self._booking_repo.get_by_id(booking_id)
        customer = await self._auth_service.get_user_by_id(booking.customer_id)
        
        return BookingWithCustomer(
            booking=booking,
            customer=UserReference.from_user(customer)
        )
```

### Efficient Data Loading
```python
# Batch loading to avoid N+1 queries
class BookingService:
    async def get_bookings_with_customers(self, booking_ids: List[UUID]):
        bookings = await self._booking_repo.get_many(booking_ids)
        customer_ids = [b.customer_id for b in bookings]
        customers = await self._auth_service.get_users_by_ids(customer_ids)
        
        customer_map = {c.id: c for c in customers}
        return [
            BookingWithCustomer(
                booking=booking,
                customer=UserReference.from_user(customer_map[booking.customer_id])
            )
            for booking in bookings
        ]
```

## 📈 Scalability Considerations

### Database Scaling
1. **Read Replicas**: Each feature can have dedicated read replicas
2. **Sharding**: Features can be sharded independently
3. **Caching**: Feature-specific caching strategies
4. **Indexing**: Each feature manages its own indexes

### Performance Optimization
```sql
-- Feature-specific indexes
CREATE INDEX idx_auth_users_email_active ON auth_users(email) WHERE is_active = true;
CREATE INDEX idx_booking_status_date ON booking_reservations(status, scheduled_at);
CREATE INDEX idx_payment_customer_date ON payment_transactions(customer_id, created_at);

-- Partial indexes for common queries
CREATE INDEX idx_auth_users_locked ON auth_users(id) WHERE locked_until IS NOT NULL;
CREATE INDEX idx_booking_pending ON booking_reservations(customer_id) WHERE status = 'pending';
```

## 🚀 Getting Started

### 1. Current Implementation
The auth feature is fully implemented with the `auth_users` table. To see it in action:

```bash
# Run the application
python main.py

# The auth module automatically creates its tables
# Check the database:
\d auth_users  # In PostgreSQL
```

### 2. Adding New Features
When adding a new feature (e.g., booking):

1. **Create feature directory structure**:
   ```
   src/features/booking/
   ├── domain/entities.py
   ├── infrastructure/database/models.py
   ├── application/services/
   └── presentation/api/
   ```

2. **Define your models**:
   ```python
   # features/booking/infrastructure/database/models.py
   class BookingModel(Base):
       __tablename__ = "booking_reservations"
       # ... your fields
   ```

3. **Add to feature module**:
   ```python
   # features/booking/booking_module.py
   class BookingModule:
       async def setup_database(self):
           # Create booking tables
           pass
   ```

4. **Integrate in main app**:
   ```python
   # main.py
   auth_module = AuthModule(auth_config)
   booking_module = BookingModule(booking_config)
   
   auth_module.setup(app, prefix="/auth")
   booking_module.setup(app, prefix="/booking")
   ```

## 📚 Additional Resources

- **Auth Module Implementation**: See `src/features/auth/infrastructure/database/models.py`
- **Repository Pattern**: See `src/features/auth/infrastructure/database/repositories.py`
- **Event System**: See `src/shared/events/event_bus.py`
- **Configuration**: See `src/features/auth/config.py`

This architecture ensures that each feature is self-contained while allowing for flexible integration and scaling as your application grows.