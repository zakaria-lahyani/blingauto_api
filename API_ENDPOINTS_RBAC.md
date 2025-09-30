# API Endpoints and RBAC Documentation

## Table of Contents
- [Authentication Endpoints](#authentication-endpoints)
- [User Management Endpoints](#user-management-endpoints)
- [Services Endpoints](#services-endpoints)
- [Vehicles Endpoints](#vehicles-endpoints)
- [Bookings Endpoints](#bookings-endpoints)
- [Walk-in Booking Endpoints](#walk-in-booking-endpoints)
- [Scheduling Management Endpoints](#scheduling-management-endpoints)
- [Smart Booking Endpoints](#smart-booking-endpoints)
- [Advanced Features Endpoints](#advanced-features-endpoints)
- [Notifications Endpoints](#notifications-endpoints)

## Authentication Endpoints

### Public Endpoints
```json
{
    "public_endpoints": [
        "POST /auth/register - Register new user account",
        "POST /auth/login - User login",
        "POST /auth/refresh - Refresh access token",
        "POST /auth/forgot-password - Request password reset",
        "POST /auth/reset-password - Reset password with token",
        "POST /auth/verify-email - Verify email address",
        "POST /auth/resend-verification - Resend verification email",
        "GET /auth/check-email?email={email} - Check if email exists"
    ]
}
```

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "GET /auth/me - Get current user profile",
        "PUT /auth/me - Update current user profile",
        "POST /auth/change-password - Change password",
        "POST /auth/logout - Logout user",
        "GET /auth/sessions - Get user sessions",
        "DELETE /auth/sessions/{session_id} - Revoke specific session"
    ],
    "admin_only_endpoints": [
        "GET /auth/users - List all users (Admin)",
        "GET /auth/users/{user_id} - Get specific user (Admin)",
        "PUT /auth/users/{user_id} - Update user (Admin)",
        "DELETE /auth/users/{user_id} - Delete user (Admin)",
        "PATCH /auth/users/{user_id}/role - Change user role (Admin)",
        "PATCH /auth/users/{user_id}/activate - Activate user (Admin)",
        "PATCH /auth/users/{user_id}/deactivate - Deactivate user (Admin)",
        "GET /auth/sessions/all - Get all active sessions (Admin)"
    ]
}
```

## User Management Endpoints

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "GET /users/profile - Get user profile",
        "PUT /users/profile - Update user profile",
        "POST /users/preferences - Set user preferences",
        "GET /users/preferences - Get user preferences",
        "DELETE /users/account - Request account deletion"
    ],
    "admin_endpoints": [
        "GET /users/list - List all users with filters (Admin)",
        "POST /users/bulk-import - Import multiple users (Admin)",
        "GET /users/export - Export user data (Admin)",
        "GET /users/statistics - Get user statistics (Admin)"
    ]
}
```

## Services Endpoints

### Public Endpoints
```json
{
    "public_endpoints": [
        "GET /services/categories - List service categories",
        "GET /services/categories/{id} - Get specific category",
        "GET /services - List all services",
        "GET /services/{id} - Get specific service",
        "GET /services/popular - Get popular services",
        "GET /services/search?q={term} - Search services",
        "GET /services/recommendations - Get service recommendations"
    ]
}
```

### Protected Endpoints
```json
{
    "manager_admin_endpoints": [
        "POST /services/categories - Create category (Manager/Admin)",
        "PUT /services/categories/{id} - Update category (Manager/Admin)",
        "DELETE /services/categories/{id} - Delete category (Manager/Admin)",
        "POST /services - Create service (Manager/Admin)",
        "PUT /services/{id} - Update service (Manager/Admin)",
        "DELETE /services/{id} - Delete service (Manager/Admin)",
        "PATCH /services/{id}/mark-popular - Mark as popular (Manager/Admin)",
        "PATCH /services/{id}/unmark-popular - Unmark popular (Manager/Admin)",
        "PATCH /services/{id}/pricing - Update pricing (Manager/Admin)",
        "POST /services/bulk-update - Bulk update services (Manager/Admin)"
    ]
}
```

## Vehicles Endpoints

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "GET /vehicles - List user's vehicles",
        "GET /vehicles/{id} - Get specific vehicle",
        "POST /vehicles - Add new vehicle",
        "PUT /vehicles/{id} - Update vehicle",
        "DELETE /vehicles/{id} - Delete vehicle",
        "PATCH /vehicles/{id}/set-default - Set as default vehicle",
        "GET /vehicles/{id}/service-history - Get vehicle service history"
    ],
    "admin_endpoints": [
        "GET /vehicles/all - List all vehicles (Admin)",
        "GET /vehicles/statistics - Vehicle statistics (Admin)"
    ]
}
```

## Bookings Endpoints

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "POST /bookings - Create new booking",
        "GET /bookings - List user's bookings",
        "GET /bookings/my - Get current user's recent bookings",
        "GET /bookings/{booking_id} - Get specific booking",
        "PUT /bookings/{booking_id} - Update booking notes",
        "POST /bookings/{booking_id}/cancel - Cancel booking",
        "POST /bookings/{booking_id}/reschedule - Reschedule booking",
        "POST /bookings/{booking_id}/rate - Rate service quality",
        "POST /bookings/{booking_id}/services - Add service to booking",
        "DELETE /bookings/{booking_id}/services/{service_id} - Remove service",
        "GET /bookings/{booking_id}/cancellation-info - Get cancellation policy"
    ],
    "staff_endpoints": [
        "PATCH /bookings/{booking_id}/confirm - Confirm booking (Manager/Admin)",
        "PATCH /bookings/{booking_id}/start - Start service (Manager/Admin)",
        "PATCH /bookings/{booking_id}/complete - Complete service (Manager/Admin)",
        "GET /bookings/analytics/summary - Get booking analytics"
    ],
    "enhanced_booking_endpoints": [
        "POST /bookings/create-with-validation - Create with validation",
        "POST /bookings/create-with-capacity - Create with capacity check",
        "GET /bookings/available-times/{date} - Get available times",
        "POST /bookings/suggest-alternatives - Get alternative times",
        "PUT /bookings/{booking_id}/reschedule-with-validation - Smart reschedule"
    ]
}
```

## Walk-in Booking Endpoints

### Protected Endpoints (Washer/Manager/Admin Only)
```json
{
    "walk_in_endpoints": [
        "POST /bookings/walk-in/register-customer - Register walk-in customer (Washer+)",
        "POST /bookings/walk-in/register-vehicle - Register vehicle on-spot (Washer+)",
        "POST /bookings/walk-in/create-booking - Create walk-in booking (Washer+)",
        "GET /bookings/walk-in/work-sessions/active - Get active sessions (Washer+)",
        "POST /bookings/walk-in/work-sessions/{id}/complete-service - Complete service (Washer+)",
        "POST /bookings/walk-in/work-sessions/{id}/complete - Complete session (Washer+)",
        "GET /bookings/walk-in/dashboard - Get washer dashboard (Washer+)",
        "GET /bookings/walk-in/accounting/daily - Daily accounting (Washer+)",
        "GET /bookings/walk-in/accounting/weekly - Weekly accounting (Washer+)"
    ]
}
```

## Scheduling Management Endpoints

### Public Endpoints
```json
{
    "public_endpoints": [
        "GET /scheduling/business-hours - Get business hours",
        "GET /scheduling/business-hours/{day} - Get hours for specific day"
    ]
}
```

### Protected Endpoints
```json
{
    "manager_admin_endpoints": [
        "PUT /scheduling/business-hours/{day} - Update business hours (Manager/Admin)",
        "POST /scheduling/business-hours/bulk-update - Bulk update hours (Manager/Admin)",
        "GET /scheduling/resources - List resources (Manager/Admin)",
        "POST /scheduling/resources - Create resource (Manager/Admin)",
        "PUT /scheduling/resources/{id} - Update resource (Manager/Admin)",
        "DELETE /scheduling/resources/{id} - Delete resource (Manager/Admin)",
        "PATCH /scheduling/resources/{id}/status - Update status (Manager/Admin)",
        "POST /scheduling/wash-bays - Create wash bay (Manager/Admin)",
        "GET /scheduling/wash-bays - List wash bays",
        "GET /scheduling/wash-bays/{id} - Get specific wash bay",
        "PUT /scheduling/wash-bays/{id} - Update wash bay (Manager/Admin)",
        "DELETE /scheduling/wash-bays/{id} - Delete wash bay (Manager/Admin)",
        "POST /scheduling/mobile-teams - Create mobile team (Manager/Admin)",
        "GET /scheduling/mobile-teams - List mobile teams",
        "PUT /scheduling/mobile-teams/{id} - Update team (Manager/Admin)"
    ]
}
```

## Smart Booking Endpoints

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "POST /smart-booking/check-availability - Check time availability",
        "POST /smart-booking/find-best-slot - Find optimal booking slot",
        "POST /smart-booking/suggest-alternatives - Get alternative times",
        "GET /smart-booking/peak-times - Get peak time information",
        "POST /smart-booking/estimate-duration - Estimate service duration",
        "POST /smart-booking/calculate-price - Calculate dynamic price"
    ],
    "admin_endpoints": [
        "GET /smart-booking/utilization - Get resource utilization (Admin)",
        "GET /smart-booking/capacity-report - Capacity analysis (Admin)",
        "POST /smart-booking/optimize-schedule - Optimize schedule (Admin)"
    ]
}
```

## Advanced Features Endpoints

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "GET /vehicles/{vehicle_id}/history - Get vehicle history",
        "GET /vehicles/{vehicle_id}/recommendations - Service recommendations"
    ],
    "public_endpoints": [
        "GET /pricing/dynamic - Get dynamic pricing",
        "GET /pricing/estimate - Get price estimate"
    ],
    "manager_admin_endpoints": [
        "GET /analytics/revenue - Revenue analytics (Manager/Admin)",
        "GET /analytics/utilization - Resource utilization (Manager/Admin)",
        "GET /analytics/customer-insights - Customer insights (Manager/Admin)",
        "GET /analytics/service-performance - Service performance (Manager/Admin)",
        "POST /analytics/generate-report - Generate custom report (Manager/Admin)",
        "GET /optimization/suggestions - Get optimization suggestions (Manager/Admin)",
        "POST /optimization/apply - Apply optimizations (Manager/Admin)"
    ]
}
```

## Notifications Endpoints

### Protected Endpoints
```json
{
    "authenticated_user_endpoints": [
        "GET /notifications - List user notifications",
        "GET /notifications/unread - Get unread notifications",
        "PATCH /notifications/{id}/read - Mark as read",
        "PATCH /notifications/read-all - Mark all as read",
        "DELETE /notifications/{id} - Delete notification",
        "GET /notifications/preferences - Get preferences",
        "PUT /notifications/preferences - Update preferences",
        "POST /notifications/subscribe-push - Subscribe to push notifications",
        "DELETE /notifications/unsubscribe-push - Unsubscribe from push"
    ],
    "admin_endpoints": [
        "POST /notifications/broadcast - Send broadcast (Admin)",
        "POST /notifications/targeted - Send targeted notification (Admin)",
        "GET /notifications/templates - List templates (Admin)",
        "POST /notifications/templates - Create template (Admin)",
        "PUT /notifications/templates/{id} - Update template (Admin)"
    ]
}
```

## RBAC Role Definitions

### Role Hierarchy
```yaml
roles:
  CLIENT:
    description: "Regular customer/client"
    permissions:
      - View public information
      - Manage own profile
      - Manage own vehicles
      - Create/manage own bookings
      - View own history
      - Rate services
  
  WASHER:
    description: "Car wash employee/washer"
    inherits: CLIENT
    additional_permissions:
      - Register walk-in customers
      - Create walk-in bookings
      - Track work sessions
      - Complete services
      - View washer dashboard
      - Access accounting reports
  
  MANAGER:
    description: "Business manager"
    inherits: WASHER
    additional_permissions:
      - Manage services and pricing
      - Manage business hours
      - Manage resources and wash bays
      - Confirm/start/complete any booking
      - View analytics and reports
      - Manage staff schedules
  
  ADMIN:
    description: "System administrator"
    inherits: MANAGER
    additional_permissions:
      - Manage all users
      - Change user roles
      - Access all system data
      - Perform system maintenance
      - Configure system settings
      - Access audit logs
```

## Authentication Requirements

### Token Types
```yaml
authentication:
  bearer_token:
    type: "JWT"
    header: "Authorization: Bearer {token}"
    expiry: "15 minutes"
    
  refresh_token:
    type: "JWT"
    cookie: "refresh_token"
    expiry: "7 days"
    
  api_key:
    type: "String"
    header: "X-API-Key"
    usage: "Third-party integrations (Admin only)"
```

## Rate Limiting

### Endpoint Rate Limits
```yaml
rate_limits:
  public_endpoints:
    requests_per_minute: 60
    requests_per_hour: 1000
    
  authenticated_endpoints:
    requests_per_minute: 120
    requests_per_hour: 3000
    
  admin_endpoints:
    requests_per_minute: 300
    requests_per_hour: 10000
    
  auth_endpoints:
    login:
      requests_per_minute: 5
      requests_per_hour: 20
    register:
      requests_per_minute: 3
      requests_per_hour: 10
    password_reset:
      requests_per_minute: 3
      requests_per_hour: 5
```

## Error Responses

### Standard Error Format
```json
{
    "success": false,
    "error": "ErrorType",
    "message": "Human-readable error message",
    "details": [
        {
            "field": "field_name",
            "message": "Field-specific error",
            "code": "ERROR_CODE"
        }
    ],
    "status_code": 400,
    "timestamp": "2025-01-30T12:00:00Z",
    "path": "/api/endpoint",
    "request_id": "uuid-here"
}
```

### Common Status Codes
```yaml
status_codes:
  200: "Success"
  201: "Created"
  204: "No Content"
  400: "Bad Request - Invalid input"
  401: "Unauthorized - Invalid/missing token"
  403: "Forbidden - Insufficient permissions"
  404: "Not Found"
  409: "Conflict - Resource already exists"
  422: "Unprocessable Entity - Validation failed"
  429: "Too Many Requests - Rate limit exceeded"
  500: "Internal Server Error"
  503: "Service Unavailable"
```

## Testing Endpoints

### Health Check Endpoints
```json
{
    "monitoring_endpoints": [
        "GET / - API information and status",
        "GET /health - Health check with database status",
        "GET /docs - OpenAPI documentation",
        "GET /redoc - ReDoc API documentation"
    ]
}
```

## WebSocket Endpoints (If Implemented)

### Real-time Endpoints
```json
{
    "websocket_endpoints": [
        "WS /ws/notifications - Real-time notifications (Authenticated)",
        "WS /ws/booking-updates - Booking status updates (Authenticated)",
        "WS /ws/washer-dashboard - Live washer dashboard (Washer+)",
        "WS /ws/admin-monitor - System monitoring (Admin)"
    ]
}
```

---

## Usage Examples

### Authentication Flow
```bash
# 1. Register
POST /auth/register
{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
}

# 2. Verify Email
POST /auth/verify-email
{
    "token": "verification-token-from-email"
}

# 3. Login
POST /auth/login
{
    "email": "user@example.com",
    "password": "SecurePassword123!"
}

# 4. Use Access Token
GET /bookings
Headers: {
    "Authorization": "Bearer eyJhbGc..."
}
```

### Walk-in Booking Flow (Washer Only)
```bash
# 1. Register Walk-in Customer
POST /bookings/walk-in/register-customer
Headers: { "Authorization": "Bearer {washer_token}" }
{
    "first_name": "Walk-in",
    "last_name": "Customer",
    "phone": "+1234567890"
}

# 2. Register Vehicle
POST /bookings/walk-in/register-vehicle
{
    "customer_id": "customer-uuid",
    "make": "Toyota",
    "model": "Camry",
    "year": 2022,
    "license_plate": "ABC123"
}

# 3. Create Walk-in Booking
POST /bookings/walk-in/create-booking
{
    "customer_id": "customer-uuid",
    "vehicle_id": "vehicle-uuid",
    "service_ids": ["service-uuid-1", "service-uuid-2"]
}
```

---

**Note**: This documentation represents the complete API surface with RBAC requirements. Some endpoints may require additional configuration or features to be enabled. Always refer to the latest API documentation at `/docs` for the most current information.