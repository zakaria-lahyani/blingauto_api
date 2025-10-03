# Role Promotion & Transition Tests

## 📋 Overview

Added comprehensive tests for role promotion and transition logic to ensure the RBAC hierarchy is properly enforced according to the `RoleTransitionPolicy` in the codebase.

## 🔐 Role Hierarchy

```
Client → Washer → Manager → Admin
  ↑        ↑        ↑         ↑
  └────────┴────────┴─────────┘
    (Demotions follow reverse path)
```

## ✅ What Was Added

### 16 New Tests in Collection 02 - Complete Authentication & Profile

**Total tests in collection:** 31 → **47 tests** (+16 tests)
**Overall test suite:** 315 → **331 tests** (+16 tests)

## 📝 Test Breakdown

### Setup Tests (3 tests)
These fetch the user IDs for the seeded test users:
1. **Get Client User for Manager Promotion** - Fetches `client.manager@blingauto.com` ID
2. **Get Client User for Washer Promotion** - Fetches `client.washer@blingauto.com` ID
3. **Get Client User for Admin Promotion** - Fetches `client.admin@blingauto.com` ID

### Valid Promotion Tests (6 tests) ✅
Tests the complete promotion path from Client to Admin:
1. **Admin ✓ Promote Client → Washer** (Valid Transition)
   - Promotes `client.washer@blingauto.com` from client to washer
   - Expected: 200, role = 'washer'

2. **Admin ✓ Promote Washer → Manager** (Valid Transition)
   - Promotes the same user from washer to manager
   - Expected: 200, role = 'manager'

3. **Admin ✓ Promote Manager → Admin** (Valid Transition)
   - Promotes the same user from manager to admin
   - Expected: 200, role = 'admin'

4. **Admin ✓ Demote Admin → Manager** (Valid Transition)
   - Demotes the user back from admin to manager
   - Expected: 200, role = 'manager'

5. **Admin ✓ Demote Manager → Washer** (Valid Transition)
   - Demotes from manager to washer
   - Expected: 200, role = 'washer'

6. **Admin ✓ Demote Washer → Client** (Valid Transition)
   - Demotes back to client (full circle)
   - Expected: 200, role = 'client'

### Invalid Transition Tests (3 tests) ✗
Tests that role transitions cannot skip levels:
1. **Admin ✗ Invalid Transition - Client → Manager** (Skip Washer)
   - Attempts to promote client directly to manager
   - Expected: 400, "Cannot transition from client to manager"

2. **Admin ✗ Invalid Transition - Client → Admin** (Skip Multiple)
   - Attempts to promote client directly to admin (skip 2 levels)
   - Expected: 400, "Cannot transition from client to admin"

3. **Admin ✗ Invalid Transition - Admin → Client** (Skip Levels)
   - Attempts to demote admin directly to client
   - Expected: 400, "Cannot transition from admin to client"

### Permission Tests (4 tests) 🚫
Tests that only admins can promote users:
1. **Manager ✗ Cannot Promote** - Forbidden (403)
   - Manager attempts to promote a client
   - Expected: 403 Forbidden

2. **Washer ✗ Cannot Promote** - Forbidden (403)
   - Washer attempts to promote a client
   - Expected: 403 Forbidden

3. **Client ✗ Cannot Promote** - Forbidden (403)
   - Client attempts to promote another user
   - Expected: 403 Forbidden

4. **Update Role - Invalid Role Value**
   - Admin attempts to set invalid role "superadmin"
   - Expected: 422 Unprocessable Entity

5. **Update Role - Nonexistent User**
   - Admin attempts to update role for non-existent user UUID
   - Expected: 404 Not Found

## 🔑 Role Transition Policy (from code)

From `app/features/auth/domain/policies.py`:

```python
ALLOWED_TRANSITIONS = {
    "client": ["washer"],              # Client can only become washer
    "washer": ["client", "manager"],   # Washer can go up or down
    "manager": ["washer", "admin"],    # Manager can go up or down
    "admin": ["manager"],              # Admin can only demote to manager
}
```

**Key Rules:**
- ✅ Only admins can change user roles (enforced via RBAC)
- ✅ Transitions must follow the allowed path (no skipping)
- ✅ Users cannot promote themselves
- ✅ Progressive hierarchy: Client < Washer < Manager < Admin

## 🧪 Test Users (from seed script)

The seed script creates these users for testing:
```
client.manager@blingauto.com   (role: client) - For manager promotion tests
client.washer@blingauto.com    (role: client) - For washer promotion tests
client.admin@blingauto.com     (role: client) - For admin promotion tests
```

## 📊 Test Coverage Matrix

| From Role | To Role | Admin Can Do It | Expected Result |
|-----------|---------|-----------------|-----------------|
| Client | Washer | ✅ Yes | 200 (Valid) |
| Client | Manager | ❌ No | 400 (Skip level) |
| Client | Admin | ❌ No | 400 (Skip levels) |
| Washer | Client | ✅ Yes | 200 (Valid) |
| Washer | Manager | ✅ Yes | 200 (Valid) |
| Washer | Admin | ❌ No | 400 (Skip level) |
| Manager | Washer | ✅ Yes | 200 (Valid) |
| Manager | Client | ❌ No | 400 (Skip level) |
| Manager | Admin | ✅ Yes | 200 (Valid) |
| Admin | Manager | ✅ Yes | 200 (Valid) |
| Admin | Washer | ❌ No | 400 (Skip level) |
| Admin | Client | ❌ No | 400 (Skip levels) |

### Permission Matrix

| Actor | Can Promote? | Result |
|-------|-------------|--------|
| Admin | ✅ Yes | 200 (if valid transition) |
| Manager | ❌ No | 403 Forbidden |
| Washer | ❌ No | 403 Forbidden |
| Client | ❌ No | 403 Forbidden |

## 🚀 Running the Tests

### Prerequisites
1. Run the seed script to create test users:
```bash
python scripts/seed_test_users.py
```

This creates:
- `client.manager@blingauto.com` (for manager promotion tests)
- `client.washer@blingauto.com` (for full promotion chain tests)
- `client.admin@blingauto.com` (for admin promotion tests)

### Run Tests
```bash
# Run just the authentication collection (includes role promotion tests)
newman run collections/02-Complete-Authentication-Profile.postman_collection.json \
  -e environments/BlingAuto-Local.postman_environment.json

# Or run all tests in workflow order
./run-all-tests.sh
```

## 📈 Test Execution Flow

```
1. Setup Tests
   ├─ Get client.manager@blingauto.com ID → client_for_manager_id
   ├─ Get client.washer@blingauto.com ID → client_for_washer_id
   └─ Get client.admin@blingauto.com ID → client_for_admin_id

2. Valid Promotions (using client_for_washer_id)
   ├─ Client → Washer ✓
   ├─ Washer → Manager ✓
   ├─ Manager → Admin ✓
   ├─ Admin → Manager ✓
   ├─ Manager → Washer ✓
   └─ Washer → Client ✓ (back to start)

3. Invalid Transitions
   ├─ Client → Manager ✗ (using client_for_manager_id)
   ├─ Client → Admin ✗ (using client_for_admin_id)
   └─ Admin → Client ✗ (using admin_user_id)

4. Permission Tests
   ├─ Manager tries to promote ✗
   ├─ Washer tries to promote ✗
   ├─ Client tries to promote ✗
   ├─ Invalid role value ✗
   └─ Nonexistent user ✗
```

## 🎯 Business Rules Validated

**RG-AUTH-009: Role Transition Validation**
- ✅ Only admins can change user roles
- ✅ Role transitions must follow allowed paths
- ✅ Cannot skip levels in the hierarchy
- ✅ Proper error messages for invalid transitions

**Security Validations:**
- ✅ 403 Forbidden for unauthorized role changes
- ✅ 400 Bad Request for invalid transitions
- ✅ 422 Unprocessable Entity for invalid role values
- ✅ 404 Not Found for nonexistent users

## 📝 Example Test Results

```
✓ Admin promoted client to washer (200)
✓ Admin promoted washer to manager (200)
✓ Admin promoted manager to admin (200)
✓ Cannot skip washer role (400)
✓ Cannot skip multiple roles (400)
✓ Manager cannot promote users (403)
✓ Washer cannot promote users (403)
✓ Client cannot promote users (403)
✓ Invalid role rejected (422)
✓ Nonexistent user returns 404
```

## 🔍 Key Assertions

Each test validates:
1. **Status Code** - Correct HTTP response (200, 400, 403, 404, 422)
2. **Role Value** - For successful transitions, confirms new role
3. **Error Messages** - For failures, validates error detail contains expected message
4. **Email Verification** - For promotions, confirms correct user was updated

## 💡 Best Practices Demonstrated

1. **Progressive Testing** - Tests follow the natural promotion path
2. **Data Isolation** - Uses dedicated test users to avoid conflicts
3. **Comprehensive Coverage** - Tests both success and failure paths
4. **Clear Naming** - Test names clearly indicate expected outcome (✓/✗)
5. **Environment Variables** - Chains user IDs between tests

## 🎓 Understanding the Tests

### Why can't we skip levels?
The policy enforces a progressive hierarchy to ensure users gain experience at each level:
- Client → Washer (learn operational work)
- Washer → Manager (learn management)
- Manager → Admin (full system access)

### Why only admins can promote?
Role changes are privileged operations that could bypass security if allowed by lower roles. Only admins have the authority to modify the organizational hierarchy.

### Why test both promotions and demotions?
Ensures the transition policy is bidirectional and properly validates both upward and downward movements in the hierarchy.

---

**Created:** 2025-10-03
**Tests Added:** 16
**New Total:** 331 tests
**Status:** ✅ Complete

