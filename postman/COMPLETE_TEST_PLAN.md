# BlingAuto API - Complete Test Plan

## 📊 Executive Summary

This document outlines the complete test coverage plan for the BlingAuto API, including all implemented and pending test scenarios.

---

## ✅ Implemented Test Collections (72 tests)

### 1. Master Configuration (6 tests)
- Health check validation
- Admin authentication
- User discovery and setup
- Service/category data loading
- Environment variable initialization

### 2. Authentication & Profile (23 tests)
- **Registration**: Valid, duplicate email, invalid email, weak password
- **Login**: Valid credentials, invalid password, non-existent user
- **Profile**: Get profile, no token, invalid token
- **Token Management**: Refresh valid/invalid tokens
- **Password**: Forgot password, change password scenarios
- **Logout**: Session termination

### 3. RBAC Testing (12 tests)
- Admin: Full access validation
- Manager: Limited admin access
- Washer: Operational access only
- Client: Customer access only
- Permission matrix validation

### 4. Walk-ins Flow (10 tests)
- Create walk-in service
- Add/remove services
- Apply discounts
- Payment processing
- Service completion
- Reporting

### 5. Services & Categories (21 tests)
- Category CRUD operations
- Service CRUD operations
- Pricing updates
- Popular service management
- Search and filtering
- Service deactivation

---

## 🔄 Test Collections to Implement

### 04 - Staff Management (Est. 25 tests)

#### Staff CRUD (8 tests)
```json
{
  "scenarios": [
    {
      "name": "Create Staff - Admin Success",
      "method": "POST",
      "endpoint": "/api/v1/staff",
      "auth": "admin_token",
      "expected_status": 201,
      "validates": ["employee_code auto-generated", "hire_date set", "status=active"]
    },
    {
      "name": "Create Staff - Manager Success",
      "method": "POST",
      "endpoint": "/api/v1/staff",
      "auth": "manager_token",
      "expected_status": 201
    },
    {
      "name": "Create Staff - Washer Forbidden",
      "method": "POST",
      "endpoint": "/api/v1/staff",
      "auth": "washer_token",
      "expected_status": 403
    },
    {
      "name": "List Staff - Paginated",
      "method": "GET",
      "endpoint": "/api/v1/staff?skip=0&limit=20",
      "auth": "manager_token",
      "expected_status": 200,
      "validates": ["pagination", "total count"]
    },
    {
      "name": "List Staff - Filter by Status",
      "method": "GET",
      "endpoint": "/api/v1/staff?status=active",
      "expected_status": 200
    },
    {
      "name": "Get Staff by ID",
      "method": "GET",
      "endpoint": "/api/v1/staff/{staff_id}",
      "expected_status": 200,
      "validates": ["full_name", "performance metrics"]
    },
    {
      "name": "Update Staff - Valid",
      "method": "PATCH",
      "endpoint": "/api/v1/staff/{staff_id}",
      "auth": "manager_token",
      "expected_status": 200
    },
    {
      "name": "Deactivate Staff - Admin Only",
      "method": "DELETE",
      "endpoint": "/api/v1/staff/{staff_id}",
      "auth": "admin_token",
      "expected_status": 204
    }
  ]
}
```

#### Document Management (6 tests)
- Upload document (ID, certificate, contract)
- List staff documents
- Verify document (Admin/Manager only)
- Delete document
- Check expiry status
- Filter expired documents

#### Attendance Tracking (7 tests)
- Check-in staff
- Check-out staff
- Record manual attendance
- Get attendance report
- Filter by date range
- Calculate hours worked
- Late arrival detection

#### Schedule Management (4 tests)
- Create work schedule
- Update schedule
- Get staff schedule
- Detect schedule conflicts

---

### 05 - Inventory Management (Est. 22 tests)

#### Product Management (8 tests)
```json
{
  "test_flow": [
    {
      "name": "Create Product - Auto SKU",
      "validates": ["SKU format PRD-00001", "initial stock set", "stock status calculated"]
    },
    {
      "name": "Get Product by ID",
      "validates": ["stock_value", "needs_reorder flag", "stock_status"]
    },
    {
      "name": "List Products - All",
      "validates": ["pagination", "category filter"]
    },
    {
      "name": "List Products - By Category",
      "endpoint": "/api/v1/inventory/products?category=cleaning_supplies"
    },
    {
      "name": "List Products - Active Only",
      "endpoint": "/api/v1/inventory/products?is_active=true"
    },
    {
      "name": "Update Product",
      "validates": ["price update", "reorder point change"]
    },
    {
      "name": "Delete Product - Admin",
      "expected_status": 204
    },
    {
      "name": "Delete Product - Manager Forbidden",
      "expected_status": 403
    }
  ]
}
```

#### Stock Movement (8 tests)
- **Stock In**: Record purchase, verify quantity increase
- **Stock Out**: Record usage, verify quantity decrease
- **Stock Adjustment**: Manual correction with reason
- **List Movements**: Filter by type (in/out/adjustment)
- **Date Range Filter**: Movement history
- **Calculate Stock Value**: Current inventory value
- **Low Stock Detection**: Products at reorder point
- **Out of Stock Alert**: Zero quantity products

#### Supplier Management (6 tests)
- Create supplier with contact details
- List suppliers (active/all)
- Update supplier information
- Deactivate supplier
- Get supplier by ID
- Filter products by supplier

---

### 06 - Bookings Management (Est. 20 tests)

#### Booking Lifecycle (10 tests)
```json
{
  "booking_states": [
    {
      "state": "pending",
      "transitions": ["confirmed", "cancelled"],
      "allowed_by": ["customer", "admin", "manager"]
    },
    {
      "state": "confirmed",
      "transitions": ["in_progress", "no_show", "cancelled"],
      "allowed_by": ["staff", "admin"]
    },
    {
      "state": "in_progress",
      "transitions": ["completed"],
      "allowed_by": ["staff", "admin"]
    },
    {
      "state": "completed",
      "transitions": ["rated"],
      "allowed_by": ["customer"]
    }
  ],
  "test_scenarios": [
    "Create booking - Customer",
    "Create booking - Unauthorized vehicle access",
    "Get booking by ID - Owner only",
    "List bookings - Customer sees only own",
    "List bookings - Admin sees all",
    "Update booking - Before confirmation",
    "Update booking - After confirmation forbidden",
    "Cancel booking - Calculate fee",
    "Confirm booking - Staff only",
    "Start booking - Track start time"
  ]
}
```

#### Advanced Booking Features (10 tests)
- **Reschedule**: Minimum 2 hours notice, availability check
- **Add Services**: Max 10 services, recalculate duration
- **Remove Services**: Minimum 1 service must remain
- **Complete with Overtime**: Calculate overtime fee
- **Mark No-Show**: Charge 100% fee after grace period
- **Rate Booking**: 1-5 stars, one rating per booking
- **Booking Stats**: Admin dashboard metrics
- **Time Slot Validation**: Prevent overlapping bookings
- **Service Duration**: Auto-calculate estimated end time
- **Payment Integration**: Link to payment records

---

## 📋 Comprehensive Test Matrix

### Endpoint Coverage by Role

| Endpoint | Admin | Manager | Washer | Client | Guest |
|----------|-------|---------|--------|--------|-------|
| **Authentication** |
| POST /auth/register | ✓ | ✓ | ✓ | ✓ | ✓ |
| POST /auth/login | ✓ | ✓ | ✓ | ✓ | ✓ |
| GET /auth/me | ✓ | ✓ | ✓ | ✓ | ✗ |
| GET /auth/users | ✓ | ✓ | ✗ | ✗ | ✗ |
| GET /auth/users/{id} | ✓ | ✗ | ✗ | ✗ | ✗ |
| PATCH /auth/users/{id}/role | ✓ | ✗ | ✗ | ✗ | ✗ |
| **Services** |
| POST /services/categories | ✓ | ✗ | ✗ | ✗ | ✗ |
| GET /services/categories | ✓ | ✓ | ✓ | ✓ | ✓ |
| POST /services | ✓ | ✓ | ✗ | ✗ | ✗ |
| PATCH /services/{id}/price | ✓ | ✓ | ✗ | ✗ | ✗ |
| DELETE /services/{id} | ✓ | ✗ | ✗ | ✗ | ✗ |
| **Staff** |
| POST /staff | ✓ | ✓ | ✗ | ✗ | ✗ |
| GET /staff | ✓ | ✓ | ✓ | ✗ | ✗ |
| POST /staff/{id}/attendance/check-in | ✓ | ✓ | ✓ | ✗ | ✗ |
| POST /staff/attendance | ✓ | ✓ | ✗ | ✗ | ✗ |
| **Inventory** |
| POST /inventory/products | ✓ | ✓ | ✗ | ✗ | ✗ |
| POST /inventory/products/{id}/stock/in | ✓ | ✓ | ✗ | ✗ | ✗ |
| POST /inventory/products/{id}/stock/out | ✓ | ✓ | ✓ | ✗ | ✗ |
| GET /inventory/alerts/low-stock | ✓ | ✓ | ✗ | ✗ | ✗ |
| **Bookings** |
| POST /bookings | ✓ | ✓ | ✓ | ✓ | ✗ |
| GET /bookings | ✓ | ✓ | ✓ | ✓ (own) | ✗ |
| POST /bookings/{id}/confirm | ✓ | ✓ | ✓ | ✗ | ✗ |
| POST /bookings/{id}/complete | ✓ | ✓ | ✓ | ✗ | ✗ |
| POST /bookings/{id}/rate | ✓ | ✗ | ✗ | ✓ (own) | ✗ |
| **Walk-ins** |
| POST /walkins | ✓ | ✓ | ✓ | ✗ | ✗ |
| POST /walkins/{id}/services | ✓ | ✓ | ✓ | ✗ | ✗ |
| POST /walkins/{id}/discount | ✓ | ✓ | ✗ | ✗ | ✗ |
| POST /walkins/{id}/complete | ✓ | ✓ | ✓ | ✗ | ✗ |

---

## 🎯 Test Scenarios by Category

### Data Validation Tests
- [ ] Email format validation (RFC 5322)
- [ ] Password strength (min 8 chars, uppercase, lowercase, number, special)
- [ ] Phone number formats (E.164)
- [ ] Date/time validation (ISO 8601)
- [ ] Numeric ranges (price > 0, quantity >= 0)
- [ ] String lengths (max 255 chars)
- [ ] Required fields validation
- [ ] Optional fields handling

### Business Logic Tests
- [ ] Discount calculation (percentage, fixed amount)
- [ ] Tax calculation (if applicable)
- [ ] Overtime fee calculation (per 15 min)
- [ ] Stock value calculation (quantity × unit_cost)
- [ ] Service duration calculation (sum of all services)
- [ ] No-show fee (100% of total)
- [ ] Late cancellation fee (varies by time)
- [ ] Reorder point detection (quantity <= reorder_point)

### Security Tests
- [ ] SQL injection prevention
- [ ] XSS prevention (input sanitization)
- [ ] CSRF token validation
- [ ] Rate limiting enforcement
- [ ] Token expiration handling
- [ ] Password hashing (bcrypt)
- [ ] Sensitive data masking in logs
- [ ] HTTPS enforcement

### Performance Tests
- [ ] Response time < 200ms for simple queries
- [ ] Response time < 500ms for complex queries
- [ ] Pagination efficiency (limit max 100)
- [ ] Concurrent user handling (100+ users)
- [ ] Database connection pooling
- [ ] Redis caching effectiveness

---

## 🚀 Execution Strategy

### Phase 1: Core Functionality (Week 1)
- ✅ Master Configuration
- ✅ Authentication & Profile
- ✅ RBAC Testing
- ✅ Services & Categories

### Phase 2: Operations (Week 2)
- ⏳ Staff Management
- ⏳ Inventory Management
- ⏳ Walk-ins Enhancement

### Phase 3: Customer Features (Week 3)
- ⏳ Bookings Management
- ⏳ Ratings & Reviews
- ⏳ Customer Dashboard

### Phase 4: Integration & E2E (Week 4)
- ⏳ End-to-end workflows
- ⏳ Performance testing
- ⏳ Load testing
- ⏳ Security testing

---

## 📊 Success Criteria

### Coverage Targets
- **Endpoint Coverage**: 100% of all REST endpoints
- **RBAC Coverage**: 100% of role-permission combinations
- **Happy Path**: 100% of primary user flows
- **Error Scenarios**: 80% of error conditions
- **Edge Cases**: 60% of boundary conditions

### Quality Metrics
- **Pass Rate**: ≥ 95% of all tests
- **Response Time**: 95th percentile < 500ms
- **Error Rate**: < 1% in production
- **Code Coverage**: ≥ 80% (backend unit tests)
- **API Documentation**: 100% of endpoints documented

---

## 📝 Test Data Requirements

### Seed Data Needed
```sql
-- Users (one per role)
INSERT INTO users (email, role, password_hash) VALUES
  ('admin@blingauto.com', 'admin', '$2b$...'),
  ('manager@blingauto.com', 'manager', '$2b$...'),
  ('washer@blingauto.com', 'washer', '$2b$...'),
  ('client@blingauto.com', 'client', '$2b$...');

-- Service Categories
INSERT INTO service_categories (name, description) VALUES
  ('Wash', 'Vehicle washing services'),
  ('Detailing', 'Interior and exterior detailing'),
  ('Protection', 'Paint protection and coating');

-- Services
INSERT INTO services (category_id, name, price, duration_minutes) VALUES
  (1, 'Basic Wash', 25.00, 30),
  (1, 'Premium Wash', 45.00, 60),
  (2, 'Interior Detail', 75.00, 90),
  (3, 'Ceramic Coating', 299.00, 180);

-- Inventory Products
INSERT INTO products (sku, name, category, unit_cost, reorder_point) VALUES
  ('PRD-00001', 'Car Shampoo', 'cleaning_supplies', 15.00, 10),
  ('PRD-00002', 'Microfiber Towels', 'tools', 2.50, 50),
  ('PRD-00003', 'Wax Polish', 'finishing', 25.00, 5);
```

---

## 🔍 Monitoring & Reporting

### Test Execution Reports
- **Daily**: Smoke test results (critical paths)
- **Weekly**: Full regression suite results
- **Sprint**: New feature test coverage
- **Release**: Complete test suite + performance

### Metrics Dashboard
- Test execution time trends
- Pass/fail rate over time
- Coverage percentage by module
- Defect density by endpoint
- Performance benchmarks

### Alert Thresholds
- 🔴 Critical: Any core auth/payment test fails
- 🟡 Warning: Pass rate drops below 90%
- 🟢 Info: New tests added to suite

---

## 📚 References

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Related Documents
- `ARCHITECTURE_AUDIT_REPORT.md` - System architecture
- `TESTING_GUIDE.md` - Postman testing guide
- `COMPREHENSIVE_TESTING_GUIDE.md` - Detailed test scenarios
- API Routers - Feature-specific endpoints

### Tools
- **Postman**: API testing and documentation
- **Newman**: CLI test execution
- **pytest**: Backend unit/integration tests
- **Locust**: Load testing
- **OWASP ZAP**: Security testing
