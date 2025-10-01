# Car Wash Management System - Functional Requirements

## 1. System Overview

### 1.1 System Purpose
The Car Wash Management System (BlingAuto API) is a comprehensive web-based application designed to manage all aspects of a car wash business, including customer management, vehicle registration, service booking, scheduling, and business operations. The system supports both in-facility (stationary) and mobile wash services.

### 1.2 System Architecture
- **Backend Framework**: FastAPI with Python
- **Architecture Pattern**: Clean Architecture with Domain-Driven Design
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based with refresh token rotation
- **Deployment**: Docker-containerized
- **API Style**: RESTful API with OpenAPI documentation

### 1.3 User Types
- **Admin**: Full system access and management
- **Manager**: Business operations and staff management
- **Washer**: Service delivery and booking management
- **Client**: Customer self-service portal

---

## 2. Authentication & Authorization

### 2.1 User Registration & Management

#### 2.1.1 User Registration
**Functional Requirements:**
- Users can register with email, password, first name, last name, and optional phone number
- Email verification is required before account activation
- Password must meet security requirements (minimum 8 characters)
- Duplicate email addresses are not allowed
- User data validation and sanitization

**Business Rules:**
- New registrations default to "Client" role
- Email verification token expires after 24 hours
- Account remains inactive until email verification
- Phone number format validation for international numbers

#### 2.1.2 User Authentication
**Functional Requirements:**
- Email/password-based login
- JWT access tokens with 15-minute expiration
- Refresh tokens with 7-day expiration and automatic rotation
- Account lockout after 5 failed login attempts
- Password reset via email with secure tokens

**Business Rules:**
- Account lockout duration increases with repeated violations
- Password reset tokens expire after 1 hour
- Users can have multiple active sessions
- Session management with token revocation

### 2.2 Role-Based Access Control (RBAC)

#### 2.2.1 Role Definitions
- **Admin**: Full system access, user management, business configuration
- **Manager**: Booking management, scheduling, staff oversight, reporting
- **Washer**: View assigned bookings, update booking status, mobile functionality
- **Client**: Personal bookings, vehicle management, profile updates

#### 2.2.2 Permission Matrix
| Feature | Admin | Manager | Washer | Client |
|---------|-------|---------|--------|--------|
| User Management | ✓ | ✓ (limited) | ✗ | ✗ |
| Booking Management | ✓ | ✓ | ✓ (assigned) | ✓ (own) |
| Vehicle Management | ✓ | ✓ | ✗ | ✓ (own) |
| Service Configuration | ✓ | ✓ | ✗ | ✗ |
| Facility Management | ✓ | ✓ | ✗ | ✗ |
| Analytics & Reporting | ✓ | ✓ | ✗ | ✗ |

---

## 3. Booking System

### 3.1 Booking Creation & Management

#### 3.1.1 Booking Creation
**Functional Requirements:**
- Create bookings with vehicle selection, service selection, and scheduling
- Support for both in-home (facility) and mobile wash types
- Real-time availability checking
- Service combination with automatic price and duration calculation
- Customer location capture for mobile services

**Business Rules:**
- Minimum 1 service, maximum 10 services per booking
- Total duration: 30-240 minutes
- Maximum booking price: $10,000
- Cannot schedule in the past
- Maximum 90 days advance booking
- Mobile bookings require GPS coordinates

#### 3.1.2 Booking Lifecycle
**Status Flow:**
1. **Pending** → Initial creation, can be modified
2. **Confirmed** → Approved booking, limited modifications
3. **In Progress** → Service started, actual times tracked
4. **Completed** → Service finished, available for rating
5. **Cancelled** → Cancelled with appropriate fees
6. **No Show** → Customer didn't appear, full fee charged

**Business Rules:**
- Bookings can only progress forward in status
- Modifications only allowed in "Pending" status
- Cancellation fees based on notice period:
  - >24 hours: Free
  - 6-24 hours: 25% fee
  - 2-6 hours: 50% fee
  - <2 hours: 100% fee
- No-show eligible after 30-minute grace period

#### 3.1.3 Service Management
**Functional Requirements:**
- Add/remove services to pending bookings
- Service combinations with conflict detection
- Dynamic pricing based on service selection
- Duration calculation and resource allocation

### 3.2 Quality Management

#### 3.2.1 Quality Rating
**Functional Requirements:**
- 5-star rating system (1-5 scale)
- Optional written feedback
- Rating only available after completion
- One-time rating per booking

**Business Rules:**
- Quality ratings are immutable once submitted
- Feedback character limit: 1000 characters
- Average ratings calculated for analytics

---

## 4. Scheduling & Resource Management

### 4.1 Facility Management

#### 4.1.1 Wash Bay Management
**Functional Requirements:**
- Configure wash bays with capacity and equipment
- Bay activation/deactivation
- Vehicle size accommodation (compact, standard, large, oversized)
- Equipment type tracking

**Business Rules:**
- Each bay has maximum vehicle size capacity
- Bays can be temporarily deactivated for maintenance
- Equipment requirements matched to service needs

#### 4.1.2 Mobile Team Management
**Functional Requirements:**
- Mobile team configuration with service radius
- Team capacity and equipment tracking
- Location-based service assignment
- Daily capacity limits (default: 8 vehicles/day)

**Business Rules:**
- Service radius limits mobile team assignments
- Teams can be deactivated for scheduling
- Distance calculation for service feasibility

### 4.2 Scheduling System

#### 4.2.1 Availability Management
**Functional Requirements:**
- Real-time availability checking
- Business hours configuration per day
- Break period management
- Resource conflict detection

**Business Rules:**
- Business hours vary by day of week
- Minimum 30-minute time slots
- 15-minute buffer between bookings
- Break periods block availability

#### 4.2.2 Smart Scheduling
**Functional Requirements:**
- Automatic resource assignment
- Conflict resolution
- Alternative time suggestions
- Preference-based scheduling

**Business Rules:**
- Preferred resources considered first
- Travel time factored for mobile services
- Buffer time maintained between appointments

---

## 5. Service & Category Management

### 5.1 Service Configuration

#### 5.1.1 Service Management
**Functional Requirements:**
- Create/update/delete services
- Service pricing and duration management
- Category assignment
- Popular service marking
- Service activation/deactivation

**Business Rules:**
- Service names must be unique within categories
- Prices must be positive values
- Duration must be positive (minutes)
- Deleted services retain historical data

#### 5.1.2 Category Management
**Functional Requirements:**
- Create/update/delete service categories
- Category activation/deactivation
- Hierarchical organization support

**Business Rules:**
- Category names must be unique
- Categories can be deactivated but not deleted if services exist
- Active categories required for service creation

---

## 6. Vehicle Management

### 6.1 Vehicle Registration

#### 6.1.1 Vehicle Information
**Functional Requirements:**
- Vehicle registration with make, model, year, color, license plate
- Default vehicle designation
- Vehicle activation/deactivation
- Vehicle ownership tracking

**Business Rules:**
- Each user can register multiple vehicles
- Only one default vehicle per user
- Vehicle year validation (1900 to current year + 2)
- License plate format validation
- Vehicle data normalization (title case, uppercase plates)

#### 6.1.2 Vehicle Operations
**Functional Requirements:**
- Update vehicle details
- Set/unset default vehicle
- Soft delete vehicles
- Vehicle history tracking

**Business Rules:**
- Default vehicles cannot be deleted
- Deleted vehicles cannot be used for new bookings
- Vehicle updates tracked with timestamps

---

## 7. Security & Compliance

### 7.1 Data Security

#### 7.1.1 Input Validation
**Functional Requirements:**
- Comprehensive input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

#### 7.1.2 Security Headers
**Functional Requirements:**
- Security headers middleware
- Content type validation
- Frame options protection
- XSS protection headers

### 7.2 Rate Limiting

#### 7.2.1 API Rate Limiting
**Functional Requirements:**
- Request rate limiting per user/IP
- Different limits for different endpoints
- Rate limit notifications
- Automatic lockout for abuse

---

## 8. System Features

### 8.1 Error Handling

#### 8.1.1 Standardized Error Responses
**Functional Requirements:**
- Consistent error response format
- Detailed error information
- Error code classification
- Request tracing

#### 8.1.2 Error Types
- **Authentication Errors** (401): Invalid credentials, expired tokens
- **Authorization Errors** (403): Insufficient permissions
- **Validation Errors** (400): Input validation failures
- **Not Found Errors** (404): Resource not found
- **Business Logic Errors** (422): Business rule violations
- **Rate Limit Errors** (429): Too many requests
- **Internal Errors** (500): System errors

### 8.2 Health Monitoring

#### 8.2.1 Health Endpoints
**Functional Requirements:**
- Basic health check endpoint
- Detailed system status endpoint
- Service dependency checking
- Database connectivity verification

### 8.3 Configuration Management

#### 8.3.1 Environment Configuration
**Functional Requirements:**
- Environment-specific configuration
- Secure secret management
- Database configuration
- Email service configuration
- JWT configuration

---

## 9. API Endpoints Summary

### 9.1 Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/logout` - User logout
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/forgot-password` - Password reset request
- `POST /api/auth/reset-password` - Password reset confirmation

### 9.2 User Management Endpoints
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/users` - List users (admin/manager)
- `PUT /api/auth/users/{user_id}/role` - Update user role (admin)

### 9.3 Vehicle Endpoints
- `GET /api/vehicles` - List user vehicles
- `POST /api/vehicles` - Register new vehicle
- `GET /api/vehicles/{vehicle_id}` - Get vehicle details
- `PUT /api/vehicles/{vehicle_id}` - Update vehicle
- `DELETE /api/vehicles/{vehicle_id}` - Delete vehicle
- `PUT /api/vehicles/{vehicle_id}/default` - Set default vehicle

### 9.4 Service Endpoints
- `GET /api/services/categories` - List service categories
- `POST /api/services/categories` - Create category (admin/manager)
- `GET /api/services` - List services
- `POST /api/services` - Create service (admin/manager)
- `PUT /api/services/{service_id}` - Update service (admin/manager)
- `DELETE /api/services/{service_id}` - Delete service (admin/manager)

### 9.5 Booking Endpoints
- `GET /api/bookings` - List bookings
- `POST /api/bookings` - Create booking
- `GET /api/bookings/{booking_id}` - Get booking details
- `PUT /api/bookings/{booking_id}` - Update booking
- `DELETE /api/bookings/{booking_id}` - Cancel booking
- `PUT /api/bookings/{booking_id}/reschedule` - Reschedule booking
- `POST /api/bookings/{booking_id}/rate` - Rate service quality
- `PUT /api/bookings/{booking_id}/status` - Update booking status

### 9.6 Scheduling Endpoints
- `GET /api/scheduling/availability` - Check availability
- `GET /api/scheduling/slots` - Get available time slots
- `POST /api/scheduling/book` - Book time slot
- `GET /api/facilities/wash-bays` - List wash bays
- `GET /api/facilities/mobile-teams` - List mobile teams

---

## 10. Data Models

### 10.1 Core Entities

#### 10.1.1 User Entity
- **Fields**: id, email, password_hash, first_name, last_name, phone, role, is_active
- **Authentication**: email_verified, verification_token, password_reset_token
- **Security**: failed_login_attempts, locked_until, refresh_tokens
- **Timestamps**: created_at, updated_at, last_login

#### 10.1.2 Vehicle Entity
- **Fields**: id, user_id, make, model, year, color, license_plate, is_default, status
- **Timestamps**: created_at, updated_at

#### 10.1.3 Booking Entity
- **Fields**: id, customer_id, vehicle_id, scheduled_at, booking_type, status
- **Services**: services[], total_price, total_duration
- **Quality**: quality_rating, quality_feedback
- **Timing**: actual_start_time, actual_end_time
- **Financial**: cancellation_fee
- **Timestamps**: created_at, updated_at

#### 10.1.4 Service Entity
- **Fields**: id, name, price, duration, category_id, description, point_description[]
- **Status**: status, popular
- **Timestamps**: created_at, updated_at

### 10.2 Business Rules Validation

#### 10.2.1 Data Integrity Rules
- All entities have UUID primary keys
- Foreign key constraints maintained
- Soft delete for historical data preservation
- Audit trail with timestamps
- Data validation at entity level

---

## 11. Technical Requirements

### 11.1 Performance Requirements
- API response time < 200ms for 95th percentile
- Support for 1000+ concurrent users
- Database query optimization
- Caching for frequently accessed data

### 11.2 Scalability Requirements
- Horizontal scaling capability
- Stateless application design
- Database connection pooling
- Load balancer compatibility

### 11.3 Reliability Requirements
- 99.9% uptime availability
- Graceful error handling
- Database transaction integrity
- Backup and disaster recovery

---

## 12. Future Enhancements

### 12.1 Planned Features
- Real-time notifications
- Mobile app integration
- Payment processing integration
- Advanced analytics and reporting
- Customer loyalty program
- Multi-location support
- Equipment maintenance tracking
- Staff scheduling optimization

### 12.2 Integration Capabilities
- Third-party calendar integration
- GPS tracking for mobile services
- SMS/email notification service
- Payment gateway integration
- Customer relationship management (CRM)
- Business intelligence tools

---

This comprehensive functional requirements document outlines all major features and capabilities of the Car Wash Management System. The system is designed to be scalable, secure, and user-friendly while maintaining business rule integrity and providing a robust platform for car wash business operations.