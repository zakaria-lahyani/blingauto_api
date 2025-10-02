# BlingAuto API - Complete Endpoints Reference

**Base URL**: `/api/v1`
**Authentication**: Bearer token in `Authorization` header
**Content-Type**: `application/json`

## Table of Contents

1. [Authentication & Authorization](#1-authentication--authorization)
2. [Booking Management](#2-booking-management)
3. [Service Catalog](#3-service-catalog)
4. [Vehicle Management](#4-vehicle-management)
5. [Pricing Engine](#5-pricing-engine)
6. [Facility Management](#6-facility-management)
7. [Staff Management](#7-staff-management)
8. [Walk-in Services](#8-walk-in-services)
9. [Inventory Management](#9-inventory-management)
10. [Expense Management](#10-expense-management)
11. [Analytics & Reporting](#11-analytics--reporting)
12. [Health Checks](#12-health-checks)

---

## 1. Authentication & Authorization

### Register User
```http
POST /api/v1/auth/register
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "client",
  "is_active": false,
  "is_verified": false
}
```

### Login
```http
POST /api/v1/auth/login
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** `200 OK`:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "client"
  }
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh
```

**Request Body**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

### Verify Email
```http
POST /api/v1/auth/verify-email
```

**Request Body**:
```json
{
  "token": "verification-token-from-email"
}
```

### Request Password Reset
```http
POST /api/v1/auth/forgot-password
```

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

### Reset Password
```http
POST /api/v1/auth/reset-password
```

**Request Body**:
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

### Change Password
```http
POST /api/v1/auth/change-password
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePass123!"
}
```

### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
```

### List Users (Admin/Manager)
```http
GET /api/v1/auth/users?page=1&limit=20&role=client&is_active=true
Authorization: Bearer {access_token}
```

### Update User Role (Admin)
```http
PUT /api/v1/auth/users/{user_id}/role
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "role": "manager"
}
```

---

## 2. Booking Management

### Create Booking
```http
POST /api/v1/bookings
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "customer_id": "uuid",
  "vehicle_id": "uuid",
  "service_ids": ["service-uuid-1", "service-uuid-2"],
  "scheduled_at": "2025-10-15T10:00:00Z",
  "booking_type": "in_home",
  "notes": "Please use eco-friendly products",
  "phone_number": "+1234567890"
}
```

**Response** `201 Created`:
```json
{
  "id": "booking-uuid",
  "booking_number": "BK-20251015-001",
  "customer_id": "uuid",
  "vehicle_id": "uuid",
  "status": "pending",
  "booking_type": "in_home",
  "scheduled_at": "2025-10-15T10:00:00Z",
  "estimated_duration_minutes": 90,
  "total_price": 150.00,
  "services": [...],
  "created_at": "2025-10-02T..."
}
```

### List Bookings
```http
GET /api/v1/bookings?customer_id={uuid}&status=confirmed&start_date=2025-10-01&end_date=2025-10-31&page=1&limit=20
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `customer_id`: Filter by customer (optional, auto-set for non-admin users)
- `status`: Filter by status (pending, confirmed, in_progress, completed, cancelled, no_show)
- `start_date`: Filter bookings from this date
- `end_date`: Filter bookings up to this date
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

### Get Booking Details
```http
GET /api/v1/bookings/{booking_id}
Authorization: Bearer {access_token}
```

### Update Booking
```http
PUT /api/v1/bookings/{booking_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "scheduled_at": "2025-10-15T14:00:00Z",
  "service_ids": ["service-uuid-1", "service-uuid-3"],
  "notes": "Updated notes"
}
```

### Confirm Booking (Staff)
```http
POST /api/v1/bookings/{booking_id}/confirm
Authorization: Bearer {access_token}
```

**Roles**: Admin, Manager, Washer

**Request Body**:
```json
{
  "notes": "Confirmed by manager"
}
```

### Start Booking (Staff)
```http
POST /api/v1/bookings/{booking_id}/start
Authorization: Bearer {access_token}
```

**Roles**: Admin, Manager, Washer

### Complete Booking (Staff)
```http
POST /api/v1/bookings/{booking_id}/complete
Authorization: Bearer {access_token}
```

**Roles**: Admin, Manager, Washer

**Request Body**:
```json
{
  "actual_end_time": "2025-10-15T12:30:00Z"
}
```

### Cancel Booking
```http
POST /api/v1/bookings/{booking_id}/cancel
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "reason": "Customer requested cancellation"
}
```

**Response**: Includes cancellation fee calculation based on timing

### Reschedule Booking
```http
POST /api/v1/bookings/{booking_id}/reschedule
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "new_scheduled_at": "2025-10-16T10:00:00Z",
  "reason": "Customer conflict"
}
```

**Business Rule**: Minimum 2 hours notice required

### Add Services to Booking
```http
POST /api/v1/bookings/{booking_id}/services
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "service_ids": ["service-uuid-4", "service-uuid-5"]
}
```

**Business Rule**: Can only add to PENDING bookings, max 10 services total

### Remove Service from Booking
```http
DELETE /api/v1/bookings/{booking_id}/services/{service_id}
Authorization: Bearer {access_token}
```

**Business Rule**: Can only remove from PENDING bookings, minimum 1 service must remain

### Mark No-Show (Staff)
```http
POST /api/v1/bookings/{booking_id}/no-show
Authorization: Bearer {access_token}
```

**Roles**: Admin, Manager, Washer

**Request Body**:
```json
{
  "reason": "Customer did not arrive within grace period"
}
```

**Business Rule**: Charges 100% cancellation fee

### Rate Booking
```http
POST /api/v1/bookings/{booking_id}/rate
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "rating": 5,
  "feedback": "Excellent service!"
}
```

**Business Rule**: Rating 1-5, only for COMPLETED bookings, once per booking

### Get Booking Statistics (Admin/Manager)
```http
GET /api/v1/bookings/admin/stats?start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

---

## 3. Service Catalog

### Create Category (Admin/Manager)
```http
POST /api/v1/services/categories
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "name": "Premium Services",
  "description": "High-end detailing services",
  "display_order": 1
}
```

### List Categories
```http
GET /api/v1/services/categories?include_inactive=false
```

**Public endpoint** - no authentication required

### Create Service (Admin/Manager)
```http
POST /api/v1/services
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "category_id": "category-uuid",
  "name": "Premium Interior Detailing",
  "description": "Complete interior deep clean and conditioning",
  "price": 89.99,
  "duration_minutes": 120,
  "is_popular": false
}
```

### List Services
```http
GET /api/v1/services?category_id={uuid}&is_active=true&is_popular=true
```

**Query Parameters**:
- `category_id`: Filter by category
- `is_active`: Filter by active status (default: true)
- `is_popular`: Show only popular services
- `search`: Search in name and description

### Get Service Details
```http
GET /api/v1/services/{service_id}
```

### Update Service Price (Admin/Manager)
```http
PUT /api/v1/services/{service_id}/price
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "new_price": 99.99,
  "reason": "Price adjustment for 2025"
}
```

### Set Service Popular Status (Admin/Manager)
```http
PUT /api/v1/services/{service_id}/popular
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "is_popular": true
}
```

**Business Rule**: Maximum 5 popular services per category

### Deactivate Service (Admin/Manager)
```http
DELETE /api/v1/services/{service_id}
Authorization: Bearer {access_token}
```

**Note**: Soft delete - preserves data but marks as inactive

### Get Popular Services
```http
GET /api/v1/services/popular?limit=10
```

### Search Services
```http
GET /api/v1/services/search?q=detail&category_id={uuid}
```

---

## 4. Vehicle Management

### Register Vehicle
```http
POST /api/v1/vehicles
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "color": "Silver",
  "license_plate": "ABC-1234",
  "is_default": true
}
```

**Response** `201 Created`:
```json
{
  "id": "vehicle-uuid",
  "customer_id": "user-uuid",
  "make": "Toyota",
  "model": "Camry",
  "year": 2023,
  "color": "Silver",
  "license_plate": "ABC-1234",
  "is_default": true,
  "is_active": true,
  "created_at": "2025-10-02T..."
}
```

**Business Rules**:
- Make: 2-50 chars
- Model: 1-50 chars
- Year: 1900 - current+2
- License plate: 2-20 chars, uppercase
- One default vehicle per customer (auto-set if first vehicle)

### List User Vehicles
```http
GET /api/v1/vehicles?include_inactive=false
Authorization: Bearer {access_token}
```

### Get Vehicle Details
```http
GET /api/v1/vehicles/{vehicle_id}
Authorization: Bearer {access_token}
```

### Update Vehicle
```http
PUT /api/v1/vehicles/{vehicle_id}
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "color": "Blue",
  "license_plate": "XYZ-5678"
}
```

### Set Default Vehicle
```http
PUT /api/v1/vehicles/{vehicle_id}/default
Authorization: Bearer {access_token}
```

### Delete Vehicle
```http
DELETE /api/v1/vehicles/{vehicle_id}
Authorization: Bearer {access_token}
```

**Note**: Soft delete - vehicle history preserved

---

## 5. Pricing Engine

### Calculate Quote
```http
POST /api/v1/pricing/calculate
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "service_ids": ["service-uuid-1", "service-uuid-2", "service-uuid-3"],
  "vehicle_type": "sedan",
  "booking_type": "in_home"
}
```

**Response**:
```json
{
  "subtotal": 180.00,
  "tax": 18.00,
  "total": 198.00,
  "estimated_duration_minutes": 150,
  "services": [
    {
      "id": "service-uuid-1",
      "name": "Exterior Wash",
      "price": 50.00,
      "duration_minutes": 45
    },
    {
      "id": "service-uuid-2",
      "name": "Interior Detailing",
      "price": 80.00,
      "duration_minutes": 60
    },
    {
      "id": "service-uuid-3",
      "name": "Wax & Polish",
      "price": 50.00,
      "duration_minutes": 45
    }
  ],
  "discounts": [],
  "breakdown": {
    "base_price": 180.00,
    "tax_rate": 0.10,
    "tax_amount": 18.00
  }
}
```

### Validate Quote
```http
POST /api/v1/pricing/validate
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "service_ids": ["uuid1", "uuid2"],
  "expected_total": 150.00
}
```

**Response**:
```json
{
  "is_valid": true,
  "calculated_total": 150.00,
  "expected_total": 150.00,
  "difference": 0.00
}
```

---

## 6. Facility Management

### Wash Bays

#### Create Wash Bay (Admin/Manager)
```http
POST /api/v1/facilities/wash-bays
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "bay_number": "Bay-1",
  "max_vehicle_size": "large",
  "status": "available"
}
```

#### List Wash Bays
```http
GET /api/v1/facilities/wash-bays?status=available&max_vehicle_size=sedan
```

#### Update Wash Bay
```http
PUT /api/v1/facilities/wash-bays/{bay_id}
Authorization: Bearer {access_token}
```

#### Delete Wash Bay (Admin)
```http
DELETE /api/v1/facilities/wash-bays/{bay_id}
Authorization: Bearer {access_token}
```

### Mobile Teams

#### Create Mobile Team (Admin/Manager)
```http
POST /api/v1/facilities/mobile-teams
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "team_name": "Mobile Unit Alpha",
  "service_radius_km": 30.0,
  "current_location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

#### List Mobile Teams
```http
GET /api/v1/facilities/mobile-teams?status=available
```

#### Update Mobile Team Location
```http
PUT /api/v1/facilities/mobile-teams/{team_id}/location
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "latitude": 40.7589,
  "longitude": -73.9851
}
```

---

## 7. Staff Management

### Create Staff Member (Admin/Manager)
```http
POST /api/v1/staff
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "user_id": "user-uuid",
  "role": "washer",
  "hire_date": "2025-01-01",
  "hourly_rate": 20.00,
  "shift": "morning"
}
```

### List Staff
```http
GET /api/v1/staff?role=washer&is_active=true&page=1&limit=20
Authorization: Bearer {access_token}
```

### Get Staff Details
```http
GET /api/v1/staff/{staff_id}
Authorization: Bearer {access_token}
```

### Update Staff
```http
PUT /api/v1/staff/{staff_id}
Authorization: Bearer {access_token}
```

### Deactivate Staff
```http
DELETE /api/v1/staff/{staff_id}
Authorization: Bearer {access_token}
```

### Staff Attendance

#### Check In
```http
POST /api/v1/staff/{staff_id}/check-in
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  }
}
```

#### Check Out
```http
POST /api/v1/staff/{staff_id}/check-out
Authorization: Bearer {access_token}
```

#### Get Attendance Report
```http
GET /api/v1/staff/{staff_id}/attendance?start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

### Staff Documents

#### Upload Document
```http
POST /api/v1/staff/{staff_id}/documents
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Form Data**:
- `document_type`: certification | license | contract | other
- `file`: Document file
- `description`: Optional description
- `expiry_date`: Optional expiry date

#### List Documents
```http
GET /api/v1/staff/{staff_id}/documents
Authorization: Bearer {access_token}
```

#### Delete Document
```http
DELETE /api/v1/staff/documents/{document_id}
Authorization: Bearer {access_token}
```

### Work Schedules

#### Create Schedule
```http
POST /api/v1/staff/{staff_id}/schedule
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "day_of_week": "monday",
  "shift": "morning",
  "start_time": "08:00:00",
  "end_time": "16:00:00"
}
```

#### Get Staff Schedule
```http
GET /api/v1/staff/{staff_id}/schedule?start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

---

## 8. Walk-in Services

### Create Walk-in
```http
POST /api/v1/walkins
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "customer_email": "john@example.com",
  "vehicle_info": {
    "make": "Honda",
    "model": "Civic",
    "year": 2022,
    "color": "Blue",
    "license_plate": "DEF-5678"
  },
  "service_ids": ["service-uuid-1"],
  "payment_method": "cash"
}
```

### List Walk-ins
```http
GET /api/v1/walkins?status=pending&date=2025-10-02&page=1&limit=20
Authorization: Bearer {access_token}
```

### Complete Walk-in
```http
POST /api/v1/walkins/{walkin_id}/complete
Authorization: Bearer {access_token}
```

---

## 9. Inventory Management

### Products

#### Create Product (Admin/Manager)
```http
POST /api/v1/inventory/products
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "sku": "SOAP-001",
  "name": "Premium Car Soap",
  "category": "cleaning_supplies",
  "unit": "bottle",
  "current_quantity": 50,
  "minimum_quantity": 10,
  "reorder_point": 15,
  "unit_cost": 15.99,
  "description": "Eco-friendly car washing soap"
}
```

#### List Products
```http
GET /api/v1/inventory/products?category=cleaning_supplies&low_stock=true
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `category`: Filter by category
- `low_stock`: Show only products below reorder point
- `search`: Search in name/SKU

#### Get Product
```http
GET /api/v1/inventory/products/{product_id}
Authorization: Bearer {access_token}
```

#### Update Product
```http
PUT /api/v1/inventory/products/{product_id}
Authorization: Bearer {access_token}
```

### Stock Movements

#### Record Stock Movement
```http
POST /api/v1/inventory/stock-movements
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "product_id": "product-uuid",
  "movement_type": "in",
  "quantity": 20,
  "reason": "Supplier delivery",
  "reference_number": "PO-2025-001"
}
```

**Movement Types**:
- `in`: Incoming stock (purchase, return)
- `out`: Outgoing stock (sale, usage)
- `adjustment`: Inventory correction
- `transfer`: Location transfer

#### List Stock Movements
```http
GET /api/v1/inventory/stock-movements?product_id={uuid}&start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

### Suppliers

#### Create Supplier
```http
POST /api/v1/inventory/suppliers
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "name": "Auto Supplies Co.",
  "contact_name": "Jane Smith",
  "email": "jane@autosupplies.com",
  "phone": "+1234567890",
  "address": "123 Supply St, City, State 12345"
}
```

#### List Suppliers
```http
GET /api/v1/inventory/suppliers?is_active=true
Authorization: Bearer {access_token}
```

---

## 10. Expense Management

### Expenses

#### Create Expense (Admin/Manager)
```http
POST /api/v1/expenses
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "category": "operational",
  "amount": 500.00,
  "description": "Monthly water bill",
  "expense_date": "2025-10-01",
  "payment_method": "bank_transfer",
  "due_date": "2025-10-15"
}
```

**Categories**: operational, salary, maintenance, utilities, supplies, marketing, other

#### List Expenses
```http
GET /api/v1/expenses?category=operational&status=pending&start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

#### Get Expense
```http
GET /api/v1/expenses/{expense_id}
Authorization: Bearer {access_token}
```

#### Approve Expense (Admin)
```http
POST /api/v1/expenses/{expense_id}/approve
Authorization: Bearer {access_token}
```

#### Mark as Paid (Admin)
```http
POST /api/v1/expenses/{expense_id}/pay
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "payment_date": "2025-10-15",
  "payment_reference": "TXN-123456"
}
```

#### Cancel Expense
```http
POST /api/v1/expenses/{expense_id}/cancel
Authorization: Bearer {access_token}
```

### Budgets

#### Create Budget (Admin)
```http
POST /api/v1/expenses/budgets
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "category": "marketing",
  "amount": 5000.00,
  "period": "monthly",
  "start_date": "2025-10-01",
  "end_date": "2025-10-31"
}
```

#### List Budgets
```http
GET /api/v1/expenses/budgets?category=marketing&is_active=true
Authorization: Bearer {access_token}
```

#### Get Budget
```http
GET /api/v1/expenses/budgets/{budget_id}
Authorization: Bearer {access_token}
```

### Reports

#### Get Monthly Summary
```http
GET /api/v1/expenses/summary/monthly?year=2025&month=10
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "period": "2025-10",
  "total_expenses": 15000.00,
  "by_category": {
    "operational": 5000.00,
    "salary": 8000.00,
    "utilities": 2000.00
  },
  "paid_count": 12,
  "pending_count": 3,
  "budget_utilization": 75.0
}
```

---

## 11. Analytics & Reporting

### Revenue Analytics

#### Get Revenue Report
```http
GET /api/v1/analytics/revenue?start_date=2025-10-01&end_date=2025-10-31&group_by=day
Authorization: Bearer {access_token}
```

**Roles**: Admin, Manager

**Query Parameters**:
- `start_date`: Start date (required)
- `end_date`: End date (required)
- `group_by`: day | week | month

**Response**:
```json
{
  "total_revenue": 25000.00,
  "booking_count": 150,
  "average_booking_value": 166.67,
  "by_period": [
    {
      "period": "2025-10-01",
      "revenue": 1200.00,
      "bookings": 8
    }
  ]
}
```

### Booking Analytics

#### Get Booking Statistics
```http
GET /api/v1/analytics/bookings?start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "total_bookings": 150,
  "completed_bookings": 120,
  "cancelled_bookings": 15,
  "no_show_bookings": 5,
  "completion_rate": 80.0,
  "cancellation_rate": 10.0,
  "average_rating": 4.5,
  "by_status": {
    "pending": 10,
    "confirmed": 20,
    "in_progress": 5,
    "completed": 120,
    "cancelled": 15,
    "no_show": 5
  }
}
```

### Service Analytics

#### Get Popular Services Report
```http
GET /api/v1/analytics/services/popular?start_date=2025-10-01&end_date=2025-10-31&limit=10
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "services": [
    {
      "service_id": "uuid",
      "service_name": "Premium Wash",
      "booking_count": 85,
      "total_revenue": 8500.00,
      "average_rating": 4.7
    }
  ]
}
```

### Staff Analytics

#### Get Staff Performance
```http
GET /api/v1/analytics/staff/{staff_id}/performance?start_date=2025-10-01&end_date=2025-10-31
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "staff_id": "uuid",
  "staff_name": "John Washer",
  "completed_bookings": 45,
  "total_hours_worked": 160,
  "average_rating": 4.8,
  "attendance_rate": 95.0
}
```

### Inventory Analytics

#### Get Inventory Report
```http
GET /api/v1/analytics/inventory?low_stock=true
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "total_products": 50,
  "low_stock_products": 5,
  "total_value": 15000.00,
  "products": [
    {
      "product_id": "uuid",
      "name": "Car Soap",
      "current_quantity": 8,
      "reorder_point": 15,
      "status": "low_stock"
    }
  ]
}
```

---

## 12. Health Checks

### API Health
```http
GET /health
```

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-02T12:00:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Database Health
```http
GET /health/db
```

### Redis Health
```http
GET /health/redis
```

---

## Error Responses

All errors follow a consistent format:

### 400 Bad Request
```json
{
  "detail": "Validation error message",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Business rule violation: Cannot cancel booking less than 24 hours before scheduled time"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "request_id": "uuid"
}
```

---

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Token Lifecycle

1. **Login** → Receive `access_token` (15 min expiry) and `refresh_token` (7 day expiry)
2. **Use access_token** for API requests
3. **Token expires** → Use `refresh_token` to get new tokens
4. **Refresh token expires** → Login again

### Role-Based Access

| Endpoint | Admin | Manager | Washer | Client |
|----------|-------|---------|--------|--------|
| User Management | ✓ | ✓ (limited) | ✗ | ✗ |
| Bookings (All) | ✓ | ✓ | ✓ | ✗ |
| Bookings (Own) | ✓ | ✓ | ✓ | ✓ |
| Services | ✓ | ✓ | ✗ | Read-only |
| Staff | ✓ | ✓ | ✗ | ✗ |
| Inventory | ✓ | ✓ | ✗ | ✗ |
| Expenses | ✓ | ✓ (limited) | ✗ | ✗ |
| Analytics | ✓ | ✓ | ✗ | ✗ |

---

## Rate Limiting

- **Default**: 60 requests per minute per IP
- **Authentication endpoints**: 10 requests per minute per IP
- **Response Header**: `X-RateLimit-Remaining`

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

**Last Updated**: 2025-10-02
**API Version**: 1.0.0
**Interactive Docs**: http://localhost:8000/docs
