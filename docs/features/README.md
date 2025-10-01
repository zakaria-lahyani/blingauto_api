# Features Documentation

## Overview

BlingAuto API consists of 6 main features, each implementing a specific business domain. All features follow the same clean architecture pattern and are completely isolated from each other.

## Table of Contents

1. [Authentication & Authorization](#1-authentication--authorization)
2. [Bookings Management](#2-bookings-management)
3. [Services & Categories](#3-services--categories)
4. [Vehicles Management](#4-vehicles-management)
5. [Pricing Engine](#5-pricing-engine)
6. [Scheduling System](#6-scheduling-system)

---

## 1. Authentication & Authorization

**Base URL**: `/api/v1/auth`

### Purpose
Manages user accounts, authentication, and role-based access control.

### Roles
- **Admin**: Full system access
- **Manager**: Manage bookings, view reports
- **Washer**: Execute bookings, mark complete
- **Client**: Create bookings, manage vehicles

### Core Entities

#### User
```python
@dataclass
class User:
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole  # ADMIN, MANAGER, WASHER, CLIENT
    status: UserStatus  # ACTIVE, INACTIVE, SUSPENDED, DELETED
    hashed_password: str
    email_verified: bool
    failed_login_attempts: int
    locked_until: Optional[datetime]
```

### Business Rules

#### RG-AUTH-001: Email Validation
- Unique per system
- Valid format (regex)
- Max 255 characters

#### RG-AUTH-002: Password Requirements
- Minimum 8 characters
- Maximum 128 characters
- Hashed with bcrypt

#### RG-AUTH-006: Account Lockout
- 5 failed attempts
- Progressive lockout (30 min × multiplier)
- Auto-unlock after duration

#### RG-AUTH-007: Email Verification
- Required before login
- Token expires in 24 hours
- One-time use

### Use Cases

1. **RegisterUser** - Create new account
   - Validates email uniqueness
   - Hashes password
   - Creates email verification token
   - Sends verification email
   - Status: INACTIVE (until verified)

2. **LoginUser** - Authenticate user
   - Validates credentials
   - Checks account status
   - Checks email verification
   - Checks account lockout
   - Records failed attempts
   - Generates JWT tokens

3. **RefreshToken** - Get new access token
   - Validates refresh token
   - Rotates refresh token
   - Generates new access token

4. **VerifyEmail** - Activate account
   - Validates token (not expired, not used)
   - Marks email as verified
   - Activates account
   - Sends welcome email

5. **RequestPasswordReset** - Request reset link
   - Generates reset token (1h expiry)
   - Sends reset email

6. **ResetPassword** - Change password via token
   - Validates token
   - Updates password
   - Marks token as used

7. **ChangePassword** - Change password (authenticated)
   - Validates current password
   - Updates password
   - Invalidates all sessions

8. **UpdateProfile** - Update user info
   - Updates first_name, last_name, phone_number
   - Re-validates data

9. **Logout** - Logout from all devices
   - Revokes all refresh tokens
   - Blacklists current access token
   - Invalidates sessions

### Security Features

- **JWT Tokens**:
  - Access token: 15 minutes
  - Refresh token: 7 days
  - Token rotation on refresh

- **Progressive Lockout**:
  - 1st lockout: 30 minutes
  - 2nd lockout: 60 minutes
  - 3rd lockout: 120 minutes
  - 4th lockout: 240 minutes

- **Password Security**:
  - Bcrypt hashing
  - Salt rounds: 12
  - No password in logs/responses

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | Public | Register new user |
| POST | `/login` | Public | Login user |
| POST | `/refresh` | Public | Refresh access token |
| POST | `/verify-email` | Public | Verify email address |
| POST | `/request-password-reset` | Public | Request password reset |
| POST | `/reset-password` | Public | Reset password |
| GET | `/me` | Auth | Get current user |
| POST | `/change-password` | Auth | Change password |
| PUT | `/profile` | Auth | Update profile |
| POST | `/logout` | Auth | Logout |
| GET | `/users` | Admin | List all users |
| GET | `/users/{id}` | Admin | Get user by ID |
| PATCH | `/users/{id}/role` | Admin | Update user role |

---

## 2. Bookings Management

**Base URL**: `/api/v1/bookings`

### Purpose
Complete booking lifecycle from creation to completion, including cancellations, rescheduling, and quality rating.

### Core Entities

#### Booking
```python
@dataclass
class Booking:
    id: str
    customer_id: str
    vehicle_id: str
    scheduled_at: datetime
    services: List[BookingService]
    booking_type: BookingType  # MOBILE, STATIONARY
    status: BookingStatus
    total_price: float
    estimated_duration_minutes: int
    cancellation_fee: float
    quality_rating: Optional[QualityRating]  # 1-5 stars
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    overtime_charges: float
```

#### BookingStatus State Machine
```
PENDING → CONFIRMED → IN_PROGRESS → COMPLETED
   ↓           ↓
CANCELLED   NO_SHOW
```

### Business Rules

#### RG-BOK-001: Service Limits
- Minimum: 1 service
- Maximum: 10 services
- No duplicate services

#### RG-BOK-002: Duration Limits
- Minimum: 30 minutes
- Maximum: 240 minutes (4 hours)

#### RG-BOK-003: Price Limits
- Minimum: €0.00
- Maximum: €10,000.00

#### RG-BOK-004: Scheduling Limits
- Minimum advance: 2 hours
- Maximum advance: 90 days
- Cannot schedule in past

#### RG-BOK-005: Mobile Booking Requirements
- Requires customer GPS location
- Format: `{lat: float, lng: float}`

#### RG-BOK-010: Cancellation Fees
| Time Until Booking | Fee |
|-------------------|-----|
| > 24 hours | 0% |
| 6-24 hours | 25% |
| 2-6 hours | 50% |
| < 2 hours | 100% |

#### RG-BOK-011: No-Show Policy
- 30-minute grace period after scheduled time
- 100% fee charged
- Only CONFIRMED bookings can be marked as no-show
- Terminal state (cannot be changed)

#### RG-BOK-012: Rescheduling
- Minimum 2-hour notice required
- Only PENDING or CONFIRMED bookings
- Checks new time slot availability

#### RG-BOK-013: Add Service
- Only PENDING bookings
- Cannot exceed 10 services
- Recalculates total price and duration

#### RG-BOK-014: Remove Service
- Only PENDING bookings
- Must keep at least 1 service
- Recalculates totals

#### RG-BOK-015: Overtime Charges
- €1.00 per minute overtime
- Calculated on completion
- Based on actual vs estimated duration

#### RG-BOK-016: Quality Rating
- Scale: 1-5 stars
- Optional feedback (max 1000 chars)
- Only COMPLETED bookings
- One-time rating (immutable)

### Use Cases

1. **CreateBooking** - Create new booking
2. **ConfirmBooking** - Staff confirms (PENDING → CONFIRMED)
3. **StartBooking** - Start service (CONFIRMED → IN_PROGRESS)
4. **CompleteBooking** - Finish service (IN_PROGRESS → COMPLETED)
5. **CancelBooking** - Cancel with fee calculation
6. **MarkNoShow** - Mark as no-show after grace period
7. **RescheduleBooking** - Change scheduled time
8. **AddServiceToBooking** - Add service to PENDING booking
9. **RemoveServiceFromBooking** - Remove service from PENDING booking
10. **RateBooking** - Rate completed booking
11. **GetBooking** - Get booking details
12. **ListBookings** - List bookings (filtered)
13. **UpdateBooking** - Update notes, phone number

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/` | Client | Create booking |
| GET | `/` | Auth | List bookings |
| GET | `/{id}` | Auth | Get booking details |
| PATCH | `/{id}` | Auth | Update booking |
| POST | `/{id}/confirm` | Staff | Confirm booking |
| POST | `/{id}/start` | Staff | Start service |
| POST | `/{id}/complete` | Staff | Complete service |
| POST | `/{id}/cancel` | Auth | Cancel booking |
| POST | `/{id}/reschedule` | Auth | Reschedule booking |
| POST | `/{id}/services` | Client | Add service |
| DELETE | `/{id}/services/{service_id}` | Client | Remove service |
| POST | `/{id}/no-show` | Staff | Mark no-show |
| POST | `/{id}/rate` | Client | Rate booking |

---

## 3. Services & Categories

**Base URL**: `/api/v1/services`

### Purpose
Service catalog management with hierarchical categories.

### Core Entities

#### Category
```python
@dataclass
class Category:
    id: str
    name: str  # Unique
    description: str
    status: CategoryStatus  # ACTIVE, INACTIVE
    display_order: int
```

#### Service
```python
@dataclass
class Service:
    id: str
    category_id: str
    name: str  # Unique per category
    description: str
    price: Decimal  # €0.01 - €10,000
    duration_minutes: int  # 1 - 480 min (8h)
    status: ServiceStatus  # ACTIVE, INACTIVE, ARCHIVED
    is_popular: bool
    display_order: int
```

### Business Rules

#### RG-SVC-001: Category Name
- Required
- Unique
- Max 100 characters

#### RG-SVC-002: Category Deactivation
- Cannot delete if has active services
- Deactivation hides from catalog

#### RG-SVC-003: Service Name
- Required
- Unique per category
- Max 100 characters

#### RG-SVC-004: Service Price
- Minimum: €0.01
- Maximum: €10,000.00
- Stored as Decimal

#### RG-SVC-005: Service Duration
- Minimum: 1 minute
- Maximum: 480 minutes (8 hours)

#### RG-SVC-006: Popular Services
- Only ACTIVE services can be popular
- Used for homepage display

### Use Cases

1. **CreateCategory** - Create category
2. **UpdateCategory** - Update category details
3. **ActivateCategory** - Activate category
4. **DeactivateCategory** - Deactivate category
5. **ListCategories** - List categories (with services)
6. **CreateService** - Create service in category
7. **UpdateService** - Update service details
8. **UpdateServicePrice** - Change service price
9. **ActivateService** - Activate service
10. **DeactivateService** - Deactivate service
11. **ArchiveService** - Archive (soft delete)
12. **SetServicePopular** - Mark as popular
13. **ListServices** - List services (filtered)
14. **GetService** - Get service details

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/categories` | Public | List categories |
| POST | `/categories` | Manager | Create category |
| GET | `/categories/{id}` | Public | Get category |
| PATCH | `/categories/{id}` | Manager | Update category |
| POST | `/categories/{id}/activate` | Manager | Activate category |
| POST | `/categories/{id}/deactivate` | Manager | Deactivate category |
| GET | `/` | Public | List services |
| POST | `/` | Manager | Create service |
| GET | `/{id}` | Public | Get service |
| PATCH | `/{id}` | Manager | Update service |
| PATCH | `/{id}/price` | Manager | Update price |
| POST | `/{id}/activate` | Manager | Activate service |
| POST | `/{id}/deactivate` | Manager | Deactivate service |
| POST | `/{id}/archive` | Admin | Archive service |
| POST | `/{id}/popular` | Manager | Toggle popular |

---

## 4. Vehicles Management

**Base URL**: `/api/v1/vehicles`

### Purpose
Customer vehicle registry for booking purposes.

### Core Entities

#### Vehicle
```python
@dataclass
class Vehicle:
    id: str
    customer_id: str
    make: str  # e.g., "Toyota"
    model: str  # e.g., "Camry"
    year: int  # 1900 - (current_year + 2)
    color: str
    license_plate: str  # Unique per customer
    is_default: bool  # One per customer
    status: VehicleStatus  # ACTIVE, DELETED
```

### Business Rules

#### RG-VEH-001: License Plate
- Required
- Unique per customer (soft delete friendly)
- Max 20 characters

#### RG-VEH-002: Year Validation
- Minimum: 1900
- Maximum: Current year + 2

#### RG-VEH-003: Default Vehicle
- One default per customer
- Setting new default unsets previous

#### RG-VEH-004: Deletion
- Cannot delete if active bookings exist
- Soft delete (status = DELETED)

### Use Cases

1. **CreateVehicle** - Add vehicle to customer
2. **UpdateVehicle** - Update vehicle details
3. **DeleteVehicle** - Soft delete vehicle
4. **SetDefaultVehicle** - Set as default
5. **ListVehicles** - List customer vehicles
6. **GetVehicle** - Get vehicle details

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Client | List my vehicles |
| POST | `/` | Client | Create vehicle |
| GET | `/{id}` | Client | Get vehicle |
| PATCH | `/{id}` | Client | Update vehicle |
| DELETE | `/{id}` | Client | Delete vehicle |
| POST | `/{id}/set-default` | Client | Set as default |

---

## 5. Pricing Engine

**Base URL**: `/api/v1/pricing`

### Purpose
Calculate booking prices based on selected services.

### Business Rules

#### RG-PRC-001: Price Calculation
- Sum of all service prices
- Stored as Decimal for precision
- Rounded to 2 decimal places

#### RG-PRC-002: Discount Support (Future)
- Placeholder for future discounts
- Currently: sum of services only

### Use Cases

1. **QuotePricing** - Calculate price for service list
   - Input: List of service IDs
   - Output: Total price, total duration
   - No persistence (calculation only)

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/quote` | Auth | Calculate price quote |

---

## 6. Scheduling System

**Base URL**: `/api/v1/scheduling`

### Purpose
Availability checking and time slot suggestions.

### Core Concepts

#### Resources
- **Facility Bays**: Stationary wash bays (capacity: 1)
- **Mobile Units**: Mobile wash teams (radius: km)

#### Availability Rules
- Buffer: 15 minutes between bookings
- Operating hours: Per facility/team
- Blackout dates: Holidays, maintenance

### Business Rules

#### RG-SCH-001: Time Slot Validation
- Check resource availability
- Check operating hours
- Apply buffer time
- Consider booking duration

#### RG-SCH-002: Mobile Radius
- Check if location within service radius
- Calculate travel time

#### RG-SCH-003: Suggestions
- Provide alternative slots if requested slot unavailable
- Consider customer preferences (time, location)

### Use Cases

1. **CheckAvailability** - Check if time slot available
2. **SuggestSlots** - Suggest alternative time slots
3. **GetFacilityCapacity** - Get facility info
4. **GetMobileAvailability** - Get mobile team availability

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/check-availability` | Auth | Check time slot |
| POST | `/suggest-slots` | Auth | Get alternatives |
| GET | `/facilities` | Auth | List facilities |
| GET | `/mobile-teams` | Auth | List mobile teams |

---

## Feature Dependencies

### Dependency Graph

```
┌──────────┐
│   Auth   │ ← All features (authentication)
└──────────┘

┌──────────┐     ┌──────────┐
│ Services │ ←── │ Bookings │
└──────────┘     └────┬─────┘
                      │
┌──────────┐          │
│ Vehicles │ ←────────┘
└──────────┘

┌──────────┐     ┌──────────┐
│ Pricing  │ ←── │ Bookings │
└──────────┘     └──────────┘

┌────────────┐   ┌──────────┐
│ Scheduling │ ←─│ Bookings │
└────────────┘   └──────────┘
```

### Cross-Feature Communication

All cross-feature calls follow the pattern:
1. Consumer owns the port (interface)
2. Consumer implements adapter
3. Adapter calls provider's public use case

**Example**: Bookings validates Services
```
Bookings defines: IExternalServiceValidator (port)
Bookings implements: ExternalServiceValidatorAdapter (adapter)
Adapter calls: Services.GetServiceUseCase (public use case)
```

---

## Testing Each Feature

### Test Pyramid

```
      /\
     /E2E\      ← API tests (full flow)
    /━━━━━━\
   /  Integ \   ← Repository, adapter tests
  /━━━━━━━━━━\
 /    Unit    \ ← Domain, policy tests
/━━━━━━━━━━━━━━\
```

### Test Levels

1. **Unit Tests** (`tests/unit/`)
   - Domain entities
   - Business rules
   - Policies
   - No external dependencies

2. **Integration Tests** (`tests/integration/`)
   - Repositories (with DB)
   - Adapters (with Redis)
   - Cross-feature communication

3. **API Tests** (`tests/api/`)
   - HTTP endpoints
   - Request/response validation
   - RBAC checks
   - Error handling

---

## Common Patterns Across Features

### 1. Entity Creation
```python
# Factory method enforces business rules
booking = Booking.create(
    customer_id=customer_id,
    vehicle_id=vehicle_id,
    # ... other params
)
```

### 2. State Transitions
```python
# Domain method enforces valid transitions
booking.confirm()  # PENDING → CONFIRMED
booking.start_service()  # CONFIRMED → IN_PROGRESS
booking.complete_service()  # IN_PROGRESS → COMPLETED
```

### 3. Validation
```python
# Validation in domain __post_init__
def __post_init__(self):
    self._validate_services()
    self._validate_scheduled_time()
    self._validate_totals()
```

### 4. Use Case Pattern
```python
class SomeUseCase:
    def __init__(self, repo: IRepository, service: IService):
        self._repo = repo
        self._service = service

    async def execute(self, request: Request) -> Response:
        # 1. Validate input
        # 2. Load entities
        # 3. Apply business logic (via domain)
        # 4. Persist
        # 5. Return response
```

---

## Next Steps

- [API Reference](../api/README.md) - Detailed endpoint documentation
- [Development Guide](../development/README.md) - How to add features
- [Architecture](../architecture/README.md) - System design

---

**Last Updated**: 2025-10-01
