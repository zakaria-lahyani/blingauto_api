# Architecture Violations Report

## Date: 2025-10-02

## Critical Violations Found

### 1. ❌ Cross-Feature Model Imports in Analytics Feature

**Location:** `app/features/analytics/adapters/repositories.py`

**Violation:** Analytics adapters are directly importing database models from other features:
- Lines 45-46: `from app.features.bookings.infrastructure.models import BookingModel`
- Lines 45-46: `from app.features.walkins.adapters.models import WalkInServiceModel`
- Lines 206-210: `from app.features.staff.adapters.models import StaffMemberModel, AttendanceRecordModel`
- Line 360: `from app.features.auth.infrastructure.models import UserModel`
- Lines 498-499: `from app.features.expenses.adapters.models import ExpenseModel`
- Line 634: `from app.features.services.infrastructure.models import ServiceModel`

**Rule Violated:**
> No feature imports another feature's internals; cross-feature sync calls go via a consumer-owned port + local adapter that invokes the public use case of the other feature.

**Impact:** HIGH - Analytics feature is tightly coupled to internal implementation details of 6+ other features.

**Required Fix:**
1. Analytics should define its own **ports/repositories.py** interfaces
2. Each analytics query should be implemented via:
   - Analytics owns a port interface (e.g., `IBookingDataPort`)
   - Analytics owns a local adapter that calls booking feature's public use case
   - NO direct database access to other features' tables

### 2. ✅ Auth Enums Usage (ACCEPTABLE)

**Location:** Multiple features importing `app.features.auth.domain.enums.UserRole`
- `app/features/analytics/api/router.py:9`
- `app/features/expenses/api/router.py:9`
- `app/features/inventory/api/router.py:8`
- `app/features/walkins/api/router.py:8`
- `app/features/staff/api/router.py:11`

**Status:** This is **ACCEPTABLE per ADR-001** which explicitly allows cross-feature imports of auth enums for RBAC.

### 3. ⚠️ Missing Import Linter Configuration

**Violation:** Project lacks automated enforcement of architecture rules.

**Required:**
- Install and configure import-linter
- Enforce:
  - api → use_cases → domain
  - use_cases → ports
  - adapters → ports
  - No feature-to-feature imports (except auth.domain.enums per ADR-001)

---

## Analysis by Feature

### Operational Features Review

#### ✅ Staff Management
- **Domain:** Pure - no external dependencies ✓
- **Use Cases:** Only depend on ports ✓
- **Adapters:** Only depend on ports + core ✓
- **API:** Only depends on use_cases + auth enums ✓
- **Cross-feature imports:** None ✓

#### ✅ Walk-in Services
- **Domain:** Pure - no external dependencies ✓
- **Use Cases:** Only depend on ports ✓
- **Adapters:** Only depend on ports + core ✓
- **API:** Only depends on use_cases + auth enums ✓
- **Cross-feature imports:** None ✓

#### ✅ Inventory Management
- **Domain:** Pure - no external dependencies ✓
- **Use Cases:** Only depend on ports ✓
- **Adapters:** Only depend on ports + core ✓
- **API:** Only depends on use_cases + auth enums ✓
- **Cross-feature imports:** None ✓

#### ✅ Expense Management
- **Domain:** Pure - no external dependencies ✓
- **Use Cases:** Only depend on ports ✓
- **Adapters:** Only depend on ports + core ✓
- **API:** Only depends on use_cases + auth enums ✓
- **Cross-feature imports:** None ✓

#### ❌ Analytics Dashboard
- **Domain:** Pure - no external dependencies ✓
- **Use Cases:** Only depend on ports ✓
- **Adapters:** **VIOLATES** - imports 6+ other features' models ✗
- **API:** Only depends on use_cases + auth enums ✓
- **Cross-feature imports:** **CRITICAL VIOLATION** ✗

---

## Recommended Fixes

### Priority 1: Fix Analytics Cross-Feature Dependencies

**Current (WRONG):**
```python
# analytics/adapters/repositories.py
from app.features.bookings.infrastructure.models import BookingModel
from app.features.walkins.adapters.models import WalkInServiceModel

class RevenueAnalyticsRepository:
    async def get_revenue_metrics(self):
        # Direct SQL queries to other features' tables
        stmt = select(BookingModel).where(...)
```

**Correct Approach:**
```python
# analytics/ports/data_providers.py
class IBookingDataProvider(ABC):
    @abstractmethod
    async def get_revenue_for_period(
        self, start: date, end: date
    ) -> List[BookingRevenueDTO]:
        pass

# analytics/adapters/booking_data_adapter.py
class BookingDataAdapter(IBookingDataProvider):
    def __init__(self, get_booking_revenue_use_case: GetBookingRevenueUseCase):
        self._use_case = get_booking_revenue_use_case

    async def get_revenue_for_period(self, start: date, end: date):
        # Calls bookings feature's public use case
        result = await self._use_case.execute(...)
        return result

# analytics/adapters/repositories.py
class RevenueAnalyticsRepository:
    def __init__(
        self,
        booking_provider: IBookingDataProvider,
        walkin_provider: IWalkInDataProvider
    ):
        self._booking_provider = booking_provider
        self._walkin_provider = walkin_provider
```

### Priority 2: Add Import Linter

Create `.import-linter` config to enforce rules automatically.

### Priority 3: Document Data Provider Pattern

Create ADR (Architecture Decision Record) for how analytics aggregates cross-feature data.

---

## Summary

**Total Violations:** 1 critical
**Features Affected:** 1 (Analytics)
**Compliant Features:** 4 (Staff, Walk-in, Inventory, Expense)
**Auth Enum Usage:** Acceptable per ADR-001

**Action Required:** Refactor Analytics adapters to use data provider pattern instead of direct cross-feature model imports.
