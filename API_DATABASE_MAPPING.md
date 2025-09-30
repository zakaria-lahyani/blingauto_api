# API Endpoints to Database Mapping Documentation

## Table of Contents
- [Database Schema Overview](#database-schema-overview)
- [Authentication & Users](#authentication--users)
- [Services Management](#services-management)
- [Vehicle Management](#vehicle-management)
- [Booking System](#booking-system)
- [Walk-in Bookings](#walk-in-bookings)
- [Scheduling System](#scheduling-system)
- [Notifications](#notifications)
- [Audit & Logging](#audit--logging)

---

## Database Schema Overview

### Core Tables
```yaml
core_tables:
  users:
    description: "User accounts and authentication"
    primary_key: "id (UUID)"
    
  services:
    description: "Available car wash services"
    primary_key: "id (UUID)"
    
  vehicles:
    description: "Customer vehicles"
    primary_key: "id (UUID)"
    foreign_keys: ["user_id"]
    
  bookings:
    description: "Service bookings and appointments"
    primary_key: "id (UUID)"
    foreign_keys: ["customer_id", "vehicle_id"]
    
  booking_services:
    description: "Many-to-many relationship for booking services"
    foreign_keys: ["booking_id", "service_id"]
```

---

## Authentication & Users

### User Registration
```yaml
endpoint: "POST /auth/register"
database_operations:
  creates:
    users:
      - id: "UUID (auto-generated)"
      - email: "User email (unique)"
      - password_hash: "Bcrypt hashed password"
      - first_name: "User first name"
      - last_name: "User last name"
      - role: "Default: CLIENT"
      - is_active: "Default: true"
      - is_verified: "Default: false"
      - created_at: "Timestamp"
      - updated_at: "Timestamp"
    
    email_verifications:
      - id: "UUID"
      - user_id: "Foreign key to users"
      - token: "Verification token"
      - expires_at: "Token expiration"
      - created_at: "Timestamp"
```

### User Login
```yaml
endpoint: "POST /auth/login"
database_operations:
  reads:
    users:
      - "Fetch user by email"
      - "Verify password_hash"
  
  creates:
    user_sessions:
      - id: "UUID"
      - user_id: "Foreign key to users"
      - access_token: "JWT token"
      - refresh_token: "Refresh JWT"
      - ip_address: "Client IP"
      - user_agent: "Client user agent"
      - expires_at: "Session expiration"
      - created_at: "Timestamp"
  
  updates:
    users:
      - last_login_at: "Current timestamp"
      - login_count: "Increment by 1"
```

### Email Verification
```yaml
endpoint: "POST /auth/verify-email"
database_operations:
  reads:
    email_verifications:
      - "Find by token"
      - "Check expiration"
  
  updates:
    users:
      - is_verified: "true"
      - verified_at: "Current timestamp"
  
  deletes:
    email_verifications:
      - "Remove used token"
```

### Password Reset
```yaml
endpoint: "POST /auth/forgot-password"
database_operations:
  creates:
    password_resets:
      - id: "UUID"
      - user_id: "Foreign key to users"
      - token: "Reset token"
      - expires_at: "Token expiration"
      - created_at: "Timestamp"
  
  reads:
    users:
      - "Find by email"

endpoint: "POST /auth/reset-password"
database_operations:
  reads:
    password_resets:
      - "Find by token"
      - "Check expiration"
  
  updates:
    users:
      - password_hash: "New hashed password"
      - password_changed_at: "Current timestamp"
  
  deletes:
    password_resets:
      - "Remove used token"
```

### User Profile Management
```yaml
endpoint: "PUT /auth/me"
database_operations:
  updates:
    users:
      - first_name: "Updated value"
      - last_name: "Updated value"
      - phone: "Updated value"
      - date_of_birth: "Updated value"
      - address: "Updated value"
      - city: "Updated value"
      - postal_code: "Updated value"
      - updated_at: "Current timestamp"

endpoint: "POST /auth/change-password"
database_operations:
  updates:
    users:
      - password_hash: "New hashed password"
      - password_changed_at: "Current timestamp"
  
  creates:
    security_events:
      - event_type: "PASSWORD_CHANGE"
      - user_id: "User ID"
      - ip_address: "Client IP"
      - timestamp: "Current timestamp"
```

---

## Services Management

### Service Categories
```yaml
endpoint: "POST /services/categories"
database_operations:
  creates:
    service_categories:
      - id: "UUID"
      - name: "Category name"
      - description: "Category description"
      - icon: "Icon identifier"
      - display_order: "Sort order"
      - is_active: "Default: true"
      - created_at: "Timestamp"
      - created_by: "Admin/Manager ID"

endpoint: "PUT /services/categories/{id}"
database_operations:
  updates:
    service_categories:
      - name: "Updated value"
      - description: "Updated value"
      - icon: "Updated value"
      - display_order: "Updated value"
      - is_active: "Updated value"
      - updated_at: "Current timestamp"
      - updated_by: "Admin/Manager ID"

endpoint: "DELETE /services/categories/{id}"
database_operations:
  updates:
    service_categories:
      - is_active: "false (soft delete)"
      - deleted_at: "Current timestamp"
      - deleted_by: "Admin/Manager ID"
```

### Services CRUD
```yaml
endpoint: "POST /services"
database_operations:
  creates:
    services:
      - id: "UUID"
      - category_id: "Foreign key to service_categories"
      - name: "Service name"
      - description: "Service description"
      - base_price: "Decimal price"
      - duration_minutes: "Integer duration"
      - is_popular: "Boolean"
      - is_active: "Default: true"
      - requires_appointment: "Boolean"
      - max_vehicles_per_day: "Integer limit"
      - created_at: "Timestamp"
      - created_by: "Admin/Manager ID"

endpoint: "PATCH /services/{id}/mark-popular"
database_operations:
  updates:
    services:
      - is_popular: "true"
      - popular_since: "Current timestamp"
      - updated_at: "Current timestamp"
```

---

## Vehicle Management

### Vehicle Registration
```yaml
endpoint: "POST /vehicles"
database_operations:
  creates:
    vehicles:
      - id: "UUID"
      - user_id: "Owner's user ID"
      - make: "Vehicle make"
      - model: "Vehicle model"
      - year: "Manufacturing year"
      - color: "Vehicle color"
      - license_plate: "Unique plate number"
      - vin: "Vehicle identification number"
      - vehicle_type: "car/suv/truck/van"
      - is_default: "Boolean"
      - status: "ACTIVE"
      - created_at: "Timestamp"
  
  updates:
    vehicles:
      - is_default: "false for other vehicles if new is default"

endpoint: "PUT /vehicles/{id}"
database_operations:
  updates:
    vehicles:
      - make: "Updated value"
      - model: "Updated value"
      - year: "Updated value"
      - color: "Updated value"
      - license_plate: "Updated value"
      - updated_at: "Current timestamp"

endpoint: "DELETE /vehicles/{id}"
database_operations:
  updates:
    vehicles:
      - status: "DELETED"
      - deleted_at: "Current timestamp"
```

---

## Booking System

### Booking Creation
```yaml
endpoint: "POST /bookings"
database_operations:
  creates:
    bookings:
      - id: "UUID"
      - customer_id: "User ID"
      - vehicle_id: "Vehicle ID"
      - scheduled_at: "Appointment datetime"
      - booking_type: "MOBILE/IN_HOME"
      - status: "PENDING"
      - total_price: "Calculated price"
      - total_duration: "Calculated duration"
      - notes: "Customer notes"
      - confirmation_code: "Unique code"
      - created_at: "Timestamp"
    
    booking_services:
      - booking_id: "Foreign key to bookings"
      - service_id: "Foreign key to services"
      - price: "Service price at booking time"
      - duration: "Service duration"
      - created_at: "Timestamp"
    
    booking_events:
      - id: "UUID"
      - booking_id: "Foreign key to bookings"
      - event_type: "CREATED"
      - event_data: "JSON metadata"
      - created_by: "User ID"
      - created_at: "Timestamp"
  
  updates:
    time_slots:
      - status: "BOOKED"
      - booking_id: "New booking ID"
      - updated_at: "Current timestamp"
```

### Booking Status Updates
```yaml
endpoint: "PATCH /bookings/{id}/confirm"
database_operations:
  updates:
    bookings:
      - status: "CONFIRMED"
      - confirmed_at: "Current timestamp"
      - confirmed_by: "Manager/Admin ID"
  
  creates:
    booking_events:
      - event_type: "CONFIRMED"
      - booking_id: "Booking ID"
      - created_by: "Manager/Admin ID"
      - created_at: "Timestamp"

endpoint: "PATCH /bookings/{id}/start"
database_operations:
  updates:
    bookings:
      - status: "IN_PROGRESS"
      - actual_start_time: "Current timestamp"
      - assigned_washer_id: "Washer ID"
  
  creates:
    booking_events:
      - event_type: "SERVICE_STARTED"
      - booking_id: "Booking ID"
      - created_by: "Washer ID"

endpoint: "PATCH /bookings/{id}/complete"
database_operations:
  updates:
    bookings:
      - status: "COMPLETED"
      - actual_end_time: "Current timestamp"
      - completed_by: "Washer ID"
  
  creates:
    booking_events:
      - event_type: "SERVICE_COMPLETED"
      - booking_id: "Booking ID"
      - created_by: "Washer ID"
    
    service_history:
      - vehicle_id: "Vehicle ID"
      - booking_id: "Booking ID"
      - service_date: "Completion date"
      - services_performed: "JSON array"
      - total_cost: "Final price"
```

### Booking Cancellation
```yaml
endpoint: "POST /bookings/{id}/cancel"
database_operations:
  updates:
    bookings:
      - status: "CANCELLED"
      - cancelled_at: "Current timestamp"
      - cancellation_reason: "Reason text"
      - cancellation_fee: "Calculated fee"
      - cancelled_by: "User ID"
  
  creates:
    booking_events:
      - event_type: "CANCELLED"
      - booking_id: "Booking ID"
      - event_data: "{'reason': '...', 'fee': ...}"
      - created_by: "User ID"
  
  updates:
    time_slots:
      - status: "AVAILABLE"
      - booking_id: "NULL"
```

### Service Rating
```yaml
endpoint: "POST /bookings/{id}/rate"
database_operations:
  updates:
    bookings:
      - quality_rating: "1-5 stars"
      - quality_feedback: "Text feedback"
      - rated_at: "Current timestamp"
  
  creates:
    service_ratings:
      - id: "UUID"
      - booking_id: "Foreign key to bookings"
      - customer_id: "User ID"
      - washer_id: "Assigned washer"
      - rating: "1-5 stars"
      - feedback: "Text feedback"
      - created_at: "Timestamp"
  
  updates:
    users: # For washer
      - total_ratings: "Increment"
      - average_rating: "Recalculated average"
```

---

## Walk-in Bookings

### Walk-in Customer Registration
```yaml
endpoint: "POST /bookings/walk-in/register-customer"
database_operations:
  creates:
    users:
      - id: "UUID"
      - email: "Generated or provided"
      - first_name: "Customer name"
      - last_name: "Customer name"
      - phone: "Phone number"
      - role: "CLIENT"
      - is_walk_in: "true"
      - registered_by: "Washer ID"
      - created_at: "Timestamp"
    
    walk_in_customers:
      - id: "UUID"
      - user_id: "Foreign key to users"
      - registered_by_washer: "Washer ID"
      - registration_date: "Current date"
      - notes: "Optional notes"
```

### Walk-in Vehicle Registration
```yaml
endpoint: "POST /bookings/walk-in/register-vehicle"
database_operations:
  creates:
    vehicles:
      - id: "UUID"
      - user_id: "Walk-in customer ID"
      - make: "Vehicle make"
      - model: "Vehicle model"
      - year: "Year"
      - color: "Color"
      - license_plate: "Plate number"
      - is_walk_in: "true"
      - created_at: "Timestamp"
```

### Walk-in Booking Creation
```yaml
endpoint: "POST /bookings/walk-in/create-booking"
database_operations:
  creates:
    bookings:
      - id: "UUID"
      - customer_id: "Walk-in customer ID"
      - vehicle_id: "Walk-in vehicle ID"
      - booking_type: "WALK_IN"
      - status: "IN_PROGRESS"
      - scheduled_at: "Current time"
      - actual_start_time: "Current time"
      - assigned_washer_id: "Creating washer"
      - is_walk_in: "true"
    
    work_sessions:
      - id: "UUID"
      - booking_id: "Foreign key to bookings"
      - washer_id: "Washer ID"
      - bay_id: "Assigned bay"
      - start_time: "Current timestamp"
      - status: "ACTIVE"
```

### Work Session Management
```yaml
endpoint: "POST /bookings/walk-in/work-sessions/{id}/complete-service"
database_operations:
  creates:
    work_session_services:
      - session_id: "Work session ID"
      - service_id: "Service ID"
      - completed_at: "Current timestamp"
      - duration_minutes: "Actual duration"
      - quality_check: "Pass/Fail"
  
  updates:
    work_sessions:
      - services_completed: "Increment counter"
      - last_update: "Current timestamp"

endpoint: "POST /bookings/walk-in/work-sessions/{id}/complete"
database_operations:
  updates:
    work_sessions:
      - status: "COMPLETED"
      - end_time: "Current timestamp"
      - total_duration: "Calculated duration"
      - services_completed: "Final count"
  
    bookings:
      - status: "COMPLETED"
      - actual_end_time: "Current timestamp"
  
  creates:
    washer_accounting:
      - id: "UUID"
      - washer_id: "Washer ID"
      - work_session_id: "Session ID"
      - booking_id: "Booking ID"
      - date: "Current date"
      - hours_worked: "Calculated hours"
      - services_completed: "Service count"
      - revenue_generated: "Total revenue"
      - labor_cost: "Calculated cost"
      - commission: "If applicable"
```

---

## Scheduling System

### Business Hours Management
```yaml
endpoint: "PUT /scheduling/business-hours/{day}"
database_operations:
  updates:
    business_hours:
      - day_of_week: "0-6 (Mon-Sun)"
      - open_time: "Opening time"
      - close_time: "Closing time"
      - is_closed: "Boolean"
      - break_periods: "JSON array"
      - updated_at: "Current timestamp"
      - updated_by: "Manager/Admin ID"
```

### Resource Management
```yaml
endpoint: "POST /scheduling/resources"
database_operations:
  creates:
    resources:
      - id: "UUID"
      - name: "Resource name"
      - resource_type: "BAY/EQUIPMENT/STAFF"
      - capacity: "Integer capacity"
      - status: "AVAILABLE/BUSY/MAINTENANCE"
      - skills: "JSON array"
      - hourly_rate: "Decimal rate"
      - created_at: "Timestamp"
      - created_by: "Manager/Admin ID"

endpoint: "PATCH /scheduling/resources/{id}/status"
database_operations:
  updates:
    resources:
      - status: "New status"
      - status_changed_at: "Current timestamp"
      - status_reason: "Optional reason"
  
  creates:
    resource_status_logs:
      - resource_id: "Resource ID"
      - old_status: "Previous status"
      - new_status: "New status"
      - changed_by: "User ID"
      - reason: "Change reason"
      - timestamp: "Current timestamp"
```

### Wash Bay Management
```yaml
endpoint: "POST /scheduling/wash-bays"
database_operations:
  creates:
    wash_bays:
      - id: "UUID"
      - name: "Bay name"
      - bay_type: "STANDARD/PREMIUM/EXPRESS"
      - is_active: "Boolean"
      - has_lift: "Boolean"
      - has_pressure_washer: "Boolean"
      - has_vacuum: "Boolean"
      - max_vehicle_size: "SMALL/MEDIUM/LARGE/XL"
      - created_at: "Timestamp"
  
  creates:
    resources:
      - resource_type: "BAY"
      - reference_id: "Wash bay ID"
      - name: "Bay name"
      - capacity: "1"
```

### Time Slot Generation
```yaml
endpoint: "Internal - Scheduled Job"
database_operations:
  creates:
    time_slots:
      - id: "UUID"
      - start_time: "Slot start"
      - end_time: "Slot end"
      - resource_id: "Resource ID"
      - status: "AVAILABLE"
      - slot_type: "REGULAR/PREMIUM"
      - created_at: "Timestamp"
    
  note: "Generated for next 30 days based on business hours"
```

### Mobile Team Management
```yaml
endpoint: "POST /scheduling/mobile-teams"
database_operations:
  creates:
    mobile_teams:
      - id: "UUID"
      - team_name: "Team name"
      - team_size: "Number of members"
      - vehicle_id: "Company vehicle"
      - service_radius_km: "Coverage radius"
      - is_active: "Boolean"
      - created_at: "Timestamp"
    
    mobile_team_members:
      - team_id: "Team ID"
      - user_id: "Washer ID"
      - role: "LEAD/MEMBER"
      - joined_at: "Timestamp"
```

---

## Notifications

### Notification Creation
```yaml
endpoint: "Internal - Event Triggered"
database_operations:
  creates:
    notifications:
      - id: "UUID"
      - user_id: "Recipient ID"
      - type: "BOOKING_CONFIRMATION/REMINDER/etc"
      - title: "Notification title"
      - message: "Notification body"
      - data: "JSON metadata"
      - is_read: "false"
      - created_at: "Timestamp"
    
    notification_queue:
      - notification_id: "Notification ID"
      - channel: "EMAIL/SMS/PUSH"
      - status: "PENDING"
      - scheduled_for: "Send time"
      - created_at: "Timestamp"
```

### Notification Updates
```yaml
endpoint: "PATCH /notifications/{id}/read"
database_operations:
  updates:
    notifications:
      - is_read: "true"
      - read_at: "Current timestamp"

endpoint: "POST /notifications/broadcast"
database_operations:
  creates:
    broadcast_notifications:
      - id: "UUID"
      - title: "Broadcast title"
      - message: "Broadcast message"
      - target_audience: "ALL/ROLE/CUSTOM"
      - criteria: "JSON filter"
      - sent_by: "Admin ID"
      - sent_at: "Timestamp"
    
    notifications: # Multiple records
      - "One record per targeted user"
```

---

## Audit & Logging

### Security Events
```yaml
triggered_by: "Authentication endpoints"
database_operations:
  creates:
    security_events:
      - id: "UUID"
      - event_type: "LOGIN/LOGOUT/PASSWORD_CHANGE/etc"
      - user_id: "User ID"
      - ip_address: "Client IP"
      - user_agent: "Client user agent"
      - success: "Boolean"
      - failure_reason: "If failed"
      - timestamp: "Event time"
```

### API Audit Log
```yaml
triggered_by: "All protected endpoints"
database_operations:
  creates:
    api_audit_logs:
      - id: "UUID"
      - user_id: "User making request"
      - method: "HTTP method"
      - endpoint: "API endpoint"
      - request_body: "Sanitized request"
      - response_status: "HTTP status"
      - ip_address: "Client IP"
      - duration_ms: "Request duration"
      - timestamp: "Request time"
```

### Data Change Log
```yaml
triggered_by: "All UPDATE/DELETE operations"
database_operations:
  creates:
    change_logs:
      - id: "UUID"
      - table_name: "Affected table"
      - record_id: "Affected record ID"
      - operation: "UPDATE/DELETE"
      - old_values: "JSON of previous values"
      - new_values: "JSON of new values"
      - changed_by: "User ID"
      - changed_at: "Timestamp"
```

---

## Database Transaction Patterns

### Atomic Operations
```yaml
booking_creation:
  transaction_boundary: "Single transaction"
  operations_order:
    1: "Validate available time slots"
    2: "Create booking record"
    3: "Create booking_services records"
    4: "Update time_slots status"
    5: "Create booking_event"
    6: "Queue notification"
  rollback_on_failure: true

walk_in_flow:
  transaction_boundary: "Multiple transactions"
  operations:
    transaction_1: "Create customer"
    transaction_2: "Create vehicle"
    transaction_3: "Create booking + work session"
  note: "Each step can fail independently"
```

### Data Consistency Rules
```yaml
constraints:
  unique_constraints:
    - "users.email"
    - "vehicles.license_plate"
    - "bookings.confirmation_code"
    - "services.name + category_id"
  
  foreign_key_constraints:
    - "vehicles.user_id -> users.id (CASCADE DELETE)"
    - "bookings.customer_id -> users.id (RESTRICT)"
    - "bookings.vehicle_id -> vehicles.id (RESTRICT)"
    - "booking_services.booking_id -> bookings.id (CASCADE)"
  
  check_constraints:
    - "bookings.actual_end_time > actual_start_time"
    - "services.base_price >= 0"
    - "vehicles.year between 1900 and current_year + 1"
```

### Soft Delete Pattern
```yaml
soft_delete_tables:
  - users: "is_active = false, deleted_at = timestamp"
  - services: "is_active = false, deleted_at = timestamp"
  - vehicles: "status = 'DELETED', deleted_at = timestamp"
  - bookings: "Never deleted, status = 'DELETED' for audit"
  
hard_delete_tables:
  - user_sessions: "After expiration"
  - email_verifications: "After use or expiration"
  - password_resets: "After use or expiration"
  - notifications: "After 90 days"
```

---

## Performance Considerations

### Indexed Columns
```yaml
indexes:
  users:
    - "email (UNIQUE)"
    - "role"
    - "is_active"
    - "created_at"
  
  bookings:
    - "customer_id"
    - "vehicle_id"
    - "status"
    - "scheduled_at"
    - "confirmation_code (UNIQUE)"
    - "created_at"
  
  vehicles:
    - "user_id"
    - "license_plate (UNIQUE)"
    - "status"
  
  services:
    - "category_id"
    - "is_popular"
    - "is_active"
```

### Batch Operations
```yaml
bulk_operations:
  notification_sending:
    batch_size: 100
    tables_affected: ["notifications", "notification_queue"]
  
  time_slot_generation:
    batch_size: 500
    tables_affected: ["time_slots"]
  
  report_generation:
    read_batch_size: 1000
    tables_read: ["bookings", "booking_services", "users"]
```

---

**Note**: This documentation represents the complete database impact of each API endpoint. Database operations may vary based on business rules, validation requirements, and feature flags. Always refer to the actual implementation for precise behavior.