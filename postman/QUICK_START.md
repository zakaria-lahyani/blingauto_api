# BlingAuto API Testing - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Prerequisites
- ✅ API running at `http://localhost:8000`
- ✅ Database seeded with test users
- ✅ Postman installed (or Newman for CLI)

---

## 📥 Step 1: Import Collections

### Option A: Postman UI
1. Open Postman
2. Click **Import** button
3. Select all `.json` files from `postman/collections/`
4. Import the environment: `postman/environments/BlingAuto-Local.postman_environment.json`

### Option B: Newman CLI
```bash
# Install Newman globally
npm install -g newman

# Verify installation
newman --version
```

---

## ⚙️ Step 2: Configure Environment

### Set Base Variables
In Postman, select **BlingAuto-Local** environment and set:

```javascript
{
  "base_url": "http://localhost:8000",
  "admin_email": "admin@blingauto.com",
  "admin_password": "AdminPass123!",
  "manager_email": "manager@blingauto.com",
  "manager_password": "ManagerPass123!",
  "washer_email": "washer@blingauto.com",
  "washer_password": "WasherPass123!",
  "client_email": "client@blingauto.com",
  "client_password": "ClientPass123!"
}
```

**Note**: Other variables will be automatically set by test scripts.

---

## ▶️ Step 3: Run Tests

### Individual Collections (Postman UI)

1. **Start with Master Config** (Required First!)
   - Open collection: `00 - Master Configuration`
   - Click **Run** → **Run Collection**
   - ✅ All 6 tests should pass

2. **Run Other Collections in Order**
   ```
   01 - Walk-ins Complete Flow      (10 tests)
   02 - Complete Auth & Profile     (23 tests)
   03 - Services & Categories       (21 tests)
   ```

### All Collections (Newman CLI)

```bash
# Navigate to postman directory
cd postman/collections

# Run all tests in sequence
newman run 00-Master-Configuration.postman_collection.json \
  -e ../environments/BlingAuto-Local.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results-master.json

newman run 01-Walkins-Complete-Flow.postman_collection.json \
  -e ../environments/BlingAuto-Local.postman_environment.json

newman run 02-Complete-Authentication-Profile.postman_collection.json \
  -e ../environments/BlingAuto-Local.postman_environment.json

newman run 03-Services-Categories.postman_collection.json \
  -e ../environments/BlingAuto-Local.postman_environment.json
```

### Automated Script

```bash
# Make script executable
chmod +x ../run-all-tests.sh

# Run all tests
../run-all-tests.sh
```

---

## ✅ Step 4: Verify Results

### Expected Output (Postman)
```
✓ API is healthy
✓ Admin login successful
✓ Users listed
✓ Categories retrieved
✓ Services retrieved
✓ Routes discovered
```

### Expected Output (Newman)
```
┌─────────────────────────┬───────────────────┐
│                         │          executed │
├─────────────────────────┼───────────────────┤
│              iterations │                 1 │
├─────────────────────────┼───────────────────┤
│                requests │                 6 │
├─────────────────────────┼───────────────────┤
│            test-scripts │                12 │
├─────────────────────────┼───────────────────┤
│      prerequest-scripts │                 2 │
├─────────────────────────┼───────────────────┤
│              assertions │                18 │
├─────────────────────────┼───────────────────┤
│         total run duration: 1.2s             │
│         total data received: 4.52kB          │
│         average response time: 127ms         │
└──────────────────────────────────────────────┘

  #  failure         detail
  ─────────────────────────────────────────────
  (All tests passed!)
```

---

## 🧪 Test Collection Overview

### 00 - Master Configuration (MUST RUN FIRST)
**Purpose**: Initialize authentication tokens and load test data

**What it does**:
- ✓ Checks API health
- ✓ Authenticates as admin
- ✓ Discovers test users (manager, washer, client)
- ✓ Loads services and categories
- ✓ Sets environment variables for other tests

**Variables Set**:
```javascript
{
  "admin_token": "eyJhbGc...",
  "admin_user_id": "uuid-here",
  "manager_user_id": "uuid-here",
  "washer_user_id": "uuid-here",
  "client_user_id": "uuid-here",
  "category_id": "uuid-here",
  "service_basic_wash_id": "uuid-here",
  "service_premium_id": "uuid-here"
}
```

---

### 01 - Walk-ins Complete Flow
**Purpose**: Test complete walk-in service lifecycle

**Scenarios**:
1. Create walk-in → `walkin_id` stored
2. Get walk-in details
3. Add service (Basic Wash)
4. Add service (Wax & Polish)
5. Apply 10% discount
6. Record cash payment
7. Complete service
8. List all walk-ins
9. Generate daily report

---

### 02 - Complete Authentication & Profile
**Purpose**: Comprehensive auth testing and RBAC

**Test Groups**:

**Authentication Flow** (16 tests):
- Register (valid, duplicate, invalid email, weak password)
- Login (valid, invalid password, non-existent user)
- Get profile (success, no token, invalid token)
- Token refresh (valid, invalid)
- Forgot password
- Logout

**Profile Management** (7 tests):
- Update profile (full, partial)
- Change password (valid, wrong current, weak new)
- Verify new password

**RBAC Testing** (12 tests):
- Admin: Full access ✓
- Manager: Limited admin access ✓
- Washer: Cannot list users ✗
- Client: Cannot list users ✗

---

### 03 - Services & Categories
**Purpose**: Service and category management

**Test Groups**:

**Category Management** (4 tests):
- Create (Admin ✓, Manager ✗)
- List all categories
- Include inactive filter

**Service Management** (11 tests):
- Create (Admin ✓, Manager ✓, Client ✗)
- Get by ID (success, not found)
- List (all, by category, popular, price range)
- Search services

**Service Updates** (6 tests):
- Update price (Manager ✓, Washer ✗)
- Set popular (Admin)
- Deactivate (Admin ✓, Manager ✗)

---

## 🔍 Troubleshooting

### Issue: All tests fail with 401

**Problem**: No authentication token

**Solution**:
```bash
# Must run Master Config first!
newman run 00-Master-Configuration.postman_collection.json \
  -e BlingAuto-Local.postman_environment.json
```

---

### Issue: Cannot find users/services

**Problem**: Database not seeded

**Solution**:
```bash
# In API directory
python scripts/seed_test_users.py

# Or use Docker
docker-compose exec api python scripts/seed_test_users.py
```

---

### Issue: Environment variables not persisting

**Problem**: Not saving to environment

**Solution** (Postman):
1. Ensure correct environment is **selected** (not just imported)
2. Check test scripts use `pm.environment.set()` not `pm.variables.set()`
3. Save environment after each collection run

---

### Issue: Duplicate email errors

**Problem**: Test user already exists

**Solution**:
- Registration tests use timestamp-based emails to avoid conflicts
- If needed, clear test data:
  ```sql
  DELETE FROM users WHERE email LIKE 'testuser%';
  ```

---

## 📊 Test Results Interpretation

### Pass/Fail Indicators

✅ **All Green** (100% pass)
- API is working correctly
- All business logic valid
- RBAC properly configured

⚠️ **Some Yellow** (90-99% pass)
- Minor issues detected
- Check failed assertions
- May need data cleanup

🔴 **Any Red** (< 90% pass)
- Critical failures
- Check API logs
- Verify database state
- Review recent code changes

---

## 📈 Next Steps

### After Basic Tests Pass:

1. **Create Additional Collections**:
   - Staff Management (25 tests)
   - Inventory Management (22 tests)
   - Bookings Management (20 tests)

2. **Implement E2E Scenarios**:
   - Complete customer journey
   - Staff daily operations
   - Manager reporting workflows

3. **Add Performance Tests**:
   - Load testing with Newman
   - Concurrent user simulation
   - Response time benchmarks

4. **Security Testing**:
   - OWASP ZAP scan
   - Input validation tests
   - SQL injection prevention

---

## 🛠️ Useful Commands

### Newman Examples

```bash
# Run with detailed output
newman run collection.json -e environment.json --verbose

# Run with HTML report
newman run collection.json -e environment.json \
  --reporters cli,html \
  --reporter-html-export report.html

# Run with specific delay between requests
newman run collection.json -e environment.json --delay-request 500

# Run specific folder
newman run collection.json -e environment.json \
  --folder "Authentication Flow"

# Stop on first failure
newman run collection.json -e environment.json --bail

# Export environment after run
newman run collection.json -e environment.json \
  --export-environment updated-environment.json
```

### Postman Tips

```javascript
// In test scripts:

// Set variable for next request
pm.environment.set('variable_name', value);

// Get variable
const value = pm.environment.get('variable_name');

// Remove variable
pm.environment.unset('variable_name');

// Log to console
console.log('Debug:', response);

// Skip request conditionally
if (condition) {
  pm.execution.skipRequest();
}
```

---

## 📚 Additional Resources

- **Full Test Plan**: `COMPLETE_TEST_PLAN.md`
- **Detailed Guide**: `COMPREHENSIVE_TESTING_GUIDE.md`
- **API Docs**: `http://localhost:8000/docs`
- **Architecture**: `ARCHITECTURE_AUDIT_REPORT.md`

---

## 🎯 Quick Checklist

Before running tests:
- [ ] API is running (`http://localhost:8000/health` returns 200)
- [ ] Database is migrated and seeded
- [ ] Environment file is configured
- [ ] Postman/Newman is installed

When tests fail:
- [ ] Check API logs for errors
- [ ] Verify environment variables are set
- [ ] Ensure Master Config ran successfully
- [ ] Check database has seed data
- [ ] Review failed assertion details

---

## 💡 Pro Tips

1. **Always run Master Config first** - It sets up all tokens and IDs
2. **Use Collection Runner** - Easier than manual execution
3. **Check Console Output** - Helpful debug messages included
4. **Save Environment** - After each run to persist variables
5. **Use Newman for CI/CD** - Integrate with GitHub Actions
6. **Create Test Data Scripts** - Automate seed data creation
7. **Monitor Response Times** - Flag slow endpoints early
8. **Keep Collections Updated** - As API evolves

---

Happy Testing! 🚀
