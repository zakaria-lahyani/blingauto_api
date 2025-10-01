# Bookings Feature Rules

## Business Rules

### RG-BOK-001: Service Constraints
- Minimum 1 service per booking
- Maximum 10 services per booking

### RG-BOK-002: Duration Limits
- Minimum total duration: 30 minutes
- Maximum total duration: 240 minutes (4 hours)

### RG-BOK-003: Price Limits
- Minimum total price: $0.00
- Maximum total price: $10,000.00

### RG-BOK-004: Scheduling Constraints
- Cannot schedule in the past
- Minimum advance notice: 2 hours
- Maximum advance booking: 90 days

### RG-BOK-005: Mobile Bookings
- Require customer location (lat/lng coordinates)
- Latitude: -90 to 90
- Longitude: -180 to 180

### RG-BOK-006: Stationary Bookings
- Use facility wash bay resources
- No customer location required

### RG-BOK-007: Vehicle Size
- Valid sizes: SMALL, MEDIUM, LARGE, EXTRA_LARGE
- Affects pricing and resource allocation

### RG-BOK-008: Booking States
- States: PENDING, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW
- All states are terminal except PENDING and CONFIRMED

### RG-BOK-009: State Transitions
- PENDING → CONFIRMED, CANCELLED
- CONFIRMED → IN_PROGRESS, CANCELLED, NO_SHOW
- IN_PROGRESS → COMPLETED
- COMPLETED/CANCELLED/NO_SHOW → (terminal)

### RG-BOK-010: Cancellation Fees
- >24 hours: 0%
- 6-24 hours: 25%
- 2-6 hours: 50%
- <2 hours: 100%

### RG-BOK-011: No-Show Policy
- Grace period: 30 minutes after scheduled time
- No-show fee: 100% of booking price

### RG-BOK-012: Rescheduling
- Only PENDING/CONFIRMED bookings can be rescheduled
- Minimum 2 hours notice for new time

### RG-BOK-013: Adding Services
- Only allowed for PENDING bookings
- Must not exceed maximum service count

### RG-BOK-014: Removing Services
- Only allowed for PENDING bookings
- Must maintain minimum service count

### RG-BOK-015: Overtime Charges
- $1.00 per minute over expected duration

### RG-BOK-016: Quality Rating
- Only COMPLETED bookings can be rated
- One rating per booking
- Feedback: max 1000 characters

## Technical Rules

### RG-BOK-017: Data Validation
- All monetary amounts in Decimal format
- Timestamps in UTC
- Coordinates as float with proper precision

### RG-BOK-018: Business Intelligence
- Track booking patterns and trends
- Monitor cancellation rates
- Calculate revenue metrics