# BlingAuto API - Test Workflow Guide

## 🔄 Data Flow & Dependencies

This guide explains the logical workflow order for running tests, ensuring proper data dependencies.

## 📊 Visual Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                  PHASE 1: FOUNDATION                         │
│                  Configuration & Auth                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  00 - Master Configuration           │
        │  • Admin/Manager/Washer/Client auth  │
        │  • Initial environment setup         │
        └──────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │  02 - Authentication & Profile       │
        │  • Create test users                 │
        │  • RBAC validation                   │
        └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 PHASE 2: CORE DATA SETUP                     │
│                    Prerequisites                             │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │ 03 - Services        │  │ 11 - Facilities      │
    │ • Categories         │  │ • Wash Bays          │
    │ • Service offerings  │  │ • Mobile Teams       │
    │ • Pricing            │  │ • Equipment          │
    └──────────────────────┘  └──────────────────────┘
                ▼                       ▼
                └───────────┬───────────┘
                            ▼
        ┌──────────────────────────────────────┐
        │  04 - Staff Management               │
        │  • Staff members                     │
        │  • Schedules                         │
        │  • Attendance                        │
        └──────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   PHASE 3: OPERATIONS                        │
│                 Business Workflows                           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│ 01 - Walkins │  │ 06 - Bookings    │  │ 09 - Sched.  │
│ • Services   │  │ • Appointments   │  │ • Resources  │
│ • Payments   │  │ • Scheduling     │  │ • Slots      │
│ • Staff      │  │ • Facilities     │  │ • Available  │
└──────────────┘  └──────────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PHASE 4: SUPPORTING SYSTEMS                     │
│              Financial & Inventory                           │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │ 08 - Expenses        │  │ 05 - Inventory       │
    │ • Expense tracking   │  │ • Products           │
    │ • Approval workflow  │  │ • Suppliers          │
    │ • Budgets            │  │ • Stock movements    │
    └──────────────────────┘  └──────────────────────┘
                ▼                       ▼
                └───────────┬───────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           PHASE 5: ANALYTICS & VALIDATION                    │
│                   Verification                               │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │ 07 - Analytics       │  │ 10 - Validation      │
    │ • Revenue metrics    │  │ • Security tests     │
    │ • Staff performance  │  │ • XSS/SQL injection  │
    │ • KPIs               │  │ • Edge cases         │
    └──────────────────────┘  └──────────────────────┘
```

## 📋 Execution Order Summary

### Phase 1: Foundation (Setup) ⚙️
**Goal:** Authenticate users and prepare environment

| # | Collection | Generates | Required By |
|---|------------|-----------|-------------|
| 1 | Master Configuration | Auth tokens for all roles | All collections |
| 2 | Authentication & Profile | Test user accounts | All collections |

### Phase 2: Core Data Setup (Prerequisites) 🏗️
**Goal:** Create foundational business data

| # | Collection | Generates | Required By |
|---|------------|-----------|-------------|
| 3 | Services & Categories | Service IDs, Category IDs | Walk-ins, Bookings |
| 4 | Facilities Management | Wash Bay IDs, Mobile Team IDs | Bookings, Scheduling |
| 5 | Staff Management | Staff IDs, Schedules | Walk-ins, Bookings, Scheduling |

### Phase 3: Operations (Business) 🚗
**Goal:** Test operational workflows with real data

| # | Collection | Depends On | Generates |
|---|------------|------------|-----------|
| 6 | Walk-ins Complete Flow | Services, Staff | Walk-in records, Payments |
| 7 | Bookings Management | Services, Facilities, Scheduling | Booking records |
| 8 | Scheduling & Resources | Facilities, Staff | Schedule data, Allocations |

### Phase 4: Supporting Systems 💰
**Goal:** Test financial and inventory management

| # | Collection | Depends On | Generates |
|---|------------|------------|-----------|
| 9 | Expenses & Budgets | Auth users | Expense records, Budgets |
| 10 | Inventory Management | - | Inventory records, Stock data |

### Phase 5: Verification ✅
**Goal:** Validate business logic and security

| # | Collection | Depends On | Purpose |
|---|------------|------------|---------|
| 11 | Analytics & Reports | Walk-ins, Bookings, Staff, Expenses | Validate metrics, KPIs |
| 12 | Data Validation & Security | - | Security testing, Edge cases |

## 🔑 Key Dependencies

### Critical Dependencies
- **Everything depends on Phase 1** (auth tokens)
- **Walk-ins depend on:** Services (Phase 2), Staff (Phase 2)
- **Bookings depend on:** Services (Phase 2), Facilities (Phase 2), Scheduling (Phase 3)
- **Analytics depend on:** Walk-ins, Bookings, Staff, Expenses

### Independent Collections
These can theoretically run standalone (after auth):
- ✅ Data Validation & Security
- ✅ Inventory Management
- ✅ Expenses & Budgets (only needs auth users)

## 🎯 Quick Start Commands

### Run All Tests (Logical Order)
```bash
./run-all-tests.sh
```

### Run Specific Phase
```bash
# Phase 1: Foundation
newman run collections/00-Master-Configuration.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/02-Complete-Authentication-Profile.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json

# Phase 2: Core Data
newman run collections/03-Services-Categories.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/11-Facilities-Management.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/04-Staff-Management.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json

# Phase 3: Operations
newman run collections/01-Walkins-Complete-Flow.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/06-Bookings-Management.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/09-Scheduling-Resources.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json

# Phase 4: Supporting
newman run collections/08-Expenses-Budgets.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/05-Inventory-Management.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json

# Phase 5: Verification
newman run collections/07-Analytics-Reports.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
newman run collections/10-Data-Validation-Security.postman_collection.json -e environments/BlingAuto-Local.postman_environment.json
```

## 🔍 Data Flow Example

Let's trace a complete booking workflow:

```
1. Master Config (Phase 1)
   → Creates: admin_token, manager_token, client_token

2. Authentication (Phase 1)
   → Creates: test_client_user_id

3. Services (Phase 2)
   → Creates: service_basic_wash_id ($29.99)

4. Facilities (Phase 2)
   → Creates: wash_bay_001_id (Bay #1, active)

5. Staff (Phase 2)
   → Creates: staff_washer_id (John Doe)

6. Bookings (Phase 3)
   → Uses: client_token, service_basic_wash_id, wash_bay_001_id
   → Creates: booking_123 (scheduled for tomorrow, assigned to Bay #1)

7. Scheduling (Phase 3)
   → Uses: wash_bay_001_id, staff_washer_id
   → Checks: availability, assigns resources

8. Analytics (Phase 5)
   → Reads: booking_123 revenue ($29.99)
   → Calculates: daily_revenue, service_popularity
```

## ⚠️ Common Issues

### Issue: Tests fail with "Service not found"
**Cause:** Skipped Phase 2 (Services & Categories)
**Solution:** Run Phase 2 before Phase 3

### Issue: Tests fail with "No available wash bays"
**Cause:** Skipped Facilities Management
**Solution:** Run collection 11 before Bookings

### Issue: Tests fail with "Unauthorized"
**Cause:** Skipped Master Configuration
**Solution:** Always run Phase 1 first

### Issue: Analytics shows zero revenue
**Cause:** No operations data (Walk-ins/Bookings not run)
**Solution:** Run Phase 3 before Phase 5

## 📊 Test Coverage by Phase

| Phase | Collections | Tests | Coverage |
|-------|-------------|-------|----------|
| 1 - Foundation | 2 | 37 | Auth, RBAC |
| 2 - Core Data | 3 | 79 | Services, Facilities, Staff |
| 3 - Operations | 3 | 73 | Walk-ins, Bookings, Scheduling |
| 4 - Supporting | 2 | 56 | Expenses, Inventory |
| 5 - Verification | 2 | 70 | Analytics, Security |
| **Total** | **12** | **315** | **99.7%+** |

## 🚀 Best Practices

1. **Always run Phase 1 first** - Nothing works without authentication
2. **Complete Phase 2 before Phase 3** - Operations need foundational data
3. **Run Analytics last** - It needs data from previous phases
4. **Save environment after each phase** - Preserve generated IDs
5. **Check API health first** - Ensure backend is running

## 📝 Notes

- Tests use `pm.environment.set()` to chain data between collections
- Timestamp-based naming prevents duplicate conflicts
- Each collection is designed to be idempotent (can run multiple times)
- Security tests (Phase 5) can run independently for quick security audits
- All tests preserve existing data (soft deletes where applicable)

---

**Ready to test?** Start with `./run-all-tests.sh` 🚀
