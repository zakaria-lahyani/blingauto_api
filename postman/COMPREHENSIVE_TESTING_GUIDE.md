# BlingAuto API - Comprehensive Testing Guide

## 📋 Test Collection Structure

### Collection Execution Order

Run collections in this sequence for optimal test coverage:

1. **00 - Master Configuration** - Initial setup and authentication
2. **01 - Walk-ins Complete Flow** - Walk-in service lifecycle
3. **02 - Complete Authentication & Profile** - Auth flows and RBAC
4. **03 - Services & Categories** - Service management
5. **04 - Staff Management** (to be created)
6. **05 - Inventory Management** (to be created)
7. **06 - Bookings Management** (to be created)

---

## 🎯 Test Coverage Summary

### ✅ Completed Collections

#### 00 - Master Configuration & Setup
**Purpose**: Initialize environment and authenticate as admin

- **Health Check**: Verify API availability, database, and Redis
- **Admin Authentication**: Login and store admin token
- **User Discovery**: Find manager, washer, and client users
- **Service Discovery**: Load categories and services into environment
- **Endpoint Discovery**: List all available API routes

**Variables Set**:
- `admin_token`, `admin_user_id`, `admin_email`
- `manager_user_id`, `washer_user_id`, `client_user_id`
- `category_id`, `service_basic_wash_id`, `service_premium_id`

---

#### 01 - Walk-ins Complete Flow
**Purpose**: Test complete walk-in service lifecycle

**Scenarios**:
1. Create walk-in service
2. Get walk-in by ID
3. Add services (Basic Wash + Wax & Polish)
4. Apply discount (10%)
5. Record payment (cash)
6. Complete walk-in
7. List all walk-ins
8. Generate daily report

**Key Validations**:
- Service number format: `WI-YYYYMMDD-XXX`
- Payment status transitions
- Discount calculations
- Final amount accuracy

---

#### 02 - Complete Authentication & Profile Management
**Purpose**: Comprehensive auth testing and RBAC validation

**Authentication Flow** (16 tests):
- ✅ Valid registration
- ✅ Duplicate email rejection
- ✅ Invalid email/password validation
- ✅ Login with valid/invalid credentials
- ✅ Get current user profile
- ✅ Token validation (no token, invalid token)
- ✅ Refresh token (valid/invalid)
- ✅ Forgot password flow
- ✅ Logout session

**Profile Management** (7 tests):
- ✅ Update profile (full/partial)
- ✅ Change password (valid/invalid)
- ✅ Verify new password works

**RBAC Testing** (12 tests):
- ✅ Admin: List users ✓, Get user ✓, Update role ✓
- ✅ Manager: List users ✓, Get user ✗, Update role ✗
- ✅ Washer: List users ✗, forbidden operations
- ✅ Client: List users ✗, forbidden operations

---

#### 03 - Services & Categories Complete Testing
**Purpose**: Full service and category management testing

**Category Management** (4 tests):
- ✅ Create category (Admin ✓, Manager ✗)
- ✅ List categories (all users)
- ✅ Include inactive categories filter

**Service Management** (11 tests):
- ✅ Create service (Admin ✓, Manager ✓, Client ✗)
- ✅ Get service by ID (success/not found)
- ✅ List services (all, by category, popular only)
- ✅ Filter by price range
- ✅ Search services
- ✅ Get popular services

**Service Updates** (6 tests):
- ✅ Update price (Manager ✓, Washer ✗)
- ✅ Set popular flag (Admin)
- ✅ Deactivate service (Admin ✓, Manager ✗)

---

## 🔄 Test Scenarios by Module

### Authentication & Authorization
| Scenario | Expected Result | Status Code |
|----------|----------------|-------------|
| Register with valid data | User created | 201 |
| Register with duplicate email | Rejected | 400 |
| Login with valid credentials | Access + Refresh tokens | 200 |
| Login with invalid password | Rejected | 401 |
| Access protected route without token | Rejected | 401 |
| Refresh with valid token | New access token | 200 |
| Logout with valid session | Success | 200 |

### Role-Based Access Control (RBAC)
| Endpoint | Admin | Manager | Washer | Client |
|----------|-------|---------|--------|--------|
| List Users | ✓ | ✓ | ✗ | ✗ |
| Get User by ID | ✓ | ✗ | ✗ | ✗ |
| Update User Role | ✓ | ✗ | ✗ | ✗ |
| Create Category | ✓ | ✗ | ✗ | ✗ |
| Create Service | ✓ | ✓ | ✗ | ✗ |
| Update Price | ✓ | ✓ | ✗ | ✗ |
| Deactivate Service | ✓ | ✗ | ✗ | ✗ |

### Services & Categories
| Test Case | Expected Behavior |
|-----------|-------------------|
| Create category as admin | Success (201) |
| Create category as manager | Forbidden (403) |
| List categories | All active categories |
| Include inactive filter | All categories including inactive |
| Create service with valid data | Service created (201) |
| Get service by ID | Service details (200) |
| Get non-existent service | Not found (404) |
| List services by category | Filtered results |
| Filter by price range | Services within range |
| Search services | Matching results |
| Update service price | Price updated, change % calculated |
| Set service as popular | Popular flag updated |
| Deactivate service | Service deactivated (admin only) |

---

## 🚀 Recommended Test Collections to Create

### 04 - Staff Management
**Scenarios to cover**:

**Staff CRUD**:
- Create staff (Admin/Manager ✓, others ✗)
- List staff (paginated, filtered by status/bay/team)
- Get staff by ID
- Update staff details
- Deactivate staff (Admin only)

**Document Management**:
- Upload document (ID, certificate, contract)
- List staff documents
- Verify document (Admin/Manager)
- Delete document (Admin/Manager)
- Check expired documents

**Attendance**:
- Check-in staff
- Check-out staff
- Record manual attendance
- Get attendance report (daily/weekly/monthly)
- Calculate hours worked

**Schedule Management**:
- Create work schedule
- Update schedule
- Get staff schedule
- Check schedule conflicts

---

### 05 - Inventory Management
**Scenarios to cover**:

**Product Management**:
- Create product (auto-generate SKU)
- Get product by ID
- List products (filter by category, active status)
- Update product
- Delete/deactivate product

**Stock Movement**:
- Record stock in (purchase, receiving)
- Record stock out (usage, consumption)
- Stock adjustment (manual correction)
- List stock movements (filter by type, date range)

**Supplier Management**:
- Create supplier
- List suppliers
- Update supplier
- Delete supplier

**Inventory Alerts**:
- Low stock alerts (at/below reorder point)
- Stock status (in stock, low stock, out of stock)
- Calculate stock value

---

### 06 - Bookings Management
**Scenarios to cover**:

**Booking Lifecycle**:
- Create booking (customer/admin)
- Get booking by ID
- List bookings (filter by customer, status, date)
- Update booking details
- Cancel booking

**Booking State Transitions**:
- Confirm booking (staff only)
- Start booking (in progress)
- Complete booking (calculate overtime)
- Mark as no-show (charge fee)

**Booking Modifications**:
- Reschedule booking (minimum notice)
- Add services to booking
- Remove services from booking

**Rating & Feedback**:
- Rate completed booking (1-5 stars)
- Submit feedback
- View booking history

---

## 📊 Environment Variables

### Required Variables
```javascript
{
  // Base Configuration
  "base_url": "http://localhost:8000",

  // Admin Credentials
  "admin_email": "admin@blingauto.com",
  "admin_password": "AdminPass123!",

  // Role Credentials
  "manager_email": "manager@blingauto.com",
  "manager_password": "ManagerPass123!",
  "washer_email": "washer@blingauto.com",
  "washer_password": "WasherPass123!",
  "client_email": "client@blingauto.com",
  "client_password": "ClientPass123!",

  // Dynamic Variables (set by tests)
  "admin_token": "",
  "manager_token": "",
  "washer_token": "",
  "client_token": "",
  "test_email": "",
  "test_password": "",
  "test_access_token": "",
  "test_refresh_token": ""
}
```

---

## 🧪 Test Execution

### Running All Tests

#### Using Postman UI:
1. Import all collections
2. Set up environment variables
3. Run collections in order using Collection Runner

#### Using Newman (CLI):
```bash
# Install Newman
npm install -g newman

# Run all collections in sequence
newman run 00-Master-Configuration.postman_collection.json -e BlingAuto-Local.postman_environment.json
newman run 01-Walkins-Complete-Flow.postman_collection.json -e BlingAuto-Local.postman_environment.json
newman run 02-Complete-Authentication-Profile.postman_collection.json -e BlingAuto-Local.postman_environment.json
newman run 03-Services-Categories.postman_collection.json -e BlingAuto-Local.postman_environment.json
```

#### Using the test script:
```bash
chmod +x postman/run-all-tests.sh
./postman/run-all-tests.sh
```

---

## ✅ Test Validation Checklist

### Authentication & Security
- [ ] User registration with valid/invalid data
- [ ] Login with correct/incorrect credentials
- [ ] Token expiration and refresh
- [ ] Logout and session invalidation
- [ ] Password reset flow
- [ ] Email verification flow

### Authorization (RBAC)
- [ ] Admin can access all endpoints
- [ ] Manager has limited administrative access
- [ ] Washer can only access operational endpoints
- [ ] Client can only access their own data
- [ ] Proper 403 responses for unauthorized access

### Data Validation
- [ ] Required fields validation
- [ ] Email format validation
- [ ] Password strength validation
- [ ] Numeric range validation
- [ ] Date/time format validation

### Business Logic
- [ ] Walk-in service calculations (total, discount, final)
- [ ] Service pricing updates
- [ ] Stock movement calculations
- [ ] Booking time slot validation
- [ ] Staff schedule conflict detection

### Error Handling
- [ ] 400 - Bad Request (invalid input)
- [ ] 401 - Unauthorized (no/invalid token)
- [ ] 403 - Forbidden (insufficient permissions)
- [ ] 404 - Not Found (resource doesn't exist)
- [ ] 409 - Conflict (duplicate/constraint violation)
- [ ] 422 - Unprocessable Entity (validation error)

---

## 📈 Success Metrics

### Coverage Goals
- **Endpoint Coverage**: 100% of all API endpoints
- **RBAC Coverage**: All role combinations tested
- **Error Scenarios**: All error codes validated
- **Business Flows**: All critical paths tested

### Current Status
- ✅ Master Configuration: 6/6 tests
- ✅ Walk-ins Flow: 10/10 tests
- ✅ Authentication: 16/16 tests
- ✅ Profile Management: 7/7 tests
- ✅ RBAC Testing: 12/12 tests
- ✅ Services & Categories: 21/21 tests
- ⏳ Staff Management: 0/20 tests (pending)
- ⏳ Inventory: 0/18 tests (pending)
- ⏳ Bookings: 0/15 tests (pending)

**Total**: 72/120 tests (60% complete)

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: Tests fail with 401 Unauthorized
- **Solution**: Run "00 - Master Configuration" first to set up auth tokens

**Issue**: Environment variables not set
- **Solution**: Ensure you're using the correct environment and tokens are being saved

**Issue**: Duplicate email errors
- **Solution**: Registration tests use timestamp-based emails to avoid conflicts

**Issue**: Foreign key constraint errors
- **Solution**: Ensure seed data exists (run database migrations/seeds)

---

## 📝 Notes

- All timestamps in tests use ISO 8601 format
- Monetary values use 2 decimal precision
- Service numbers follow format: `WI-YYYYMMDD-XXX`
- All dates are in UTC timezone
- Pagination uses offset/limit pattern
- All responses include proper status codes and error messages
