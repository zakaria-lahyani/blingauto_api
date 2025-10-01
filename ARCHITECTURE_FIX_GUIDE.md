# Architecture Compliance Fix Guide

**Based on**: [ARCHITECTURE_COMPLIANCE_REPORT.md](ARCHITECTURE_COMPLIANCE_REPORT.md)
**Priority**: Critical fix for production deployment

---

## Summary of Required Fixes

| # | Violation | File | Priority | Effort | Status |
|---|-----------|------|----------|--------|--------|
| 1 | Scheduling→Facilities model import | [scheduling/adapters/models.py:9](app/features/scheduling/adapters/models.py#L9) | 🔴 Critical | 3h | ⏳ To Do |
| 2 | UserRole enum sharing | [facilities/api/*_router.py](app/features/facilities/api/) | 🟡 Document | 30m | ⏳ To Do |
| 3 | Bookings external services | [bookings/adapters/external_services.py:13-15](app/features/bookings/adapters/external_services.py#L13) | 🟢 Review Only | 1h | ✅ Already Correct |

---

## Fix #1: Remove Cross-Feature Model Import (CRITICAL)

### Problem
```python
# app/features/scheduling/adapters/models.py:9
from app.features.facilities.adapters.models import WashBayModel as WashBay, MobileTeamModel as MobileTeam
```

This creates tight coupling between scheduling and facilities at the database layer.

### Solution: Use String-Based Foreign Keys

#### Step 1: Update TimeSlot Model
```python
# app/features/scheduling/adapters/models.py

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text, JSON
from sqlalchemy.orm import relationship
import uuid

from app.core.db.base import Base, TimestampMixin

# ❌ REMOVE THIS
# from app.features.facilities.adapters.models import WashBayModel as WashBay, MobileTeamModel as MobileTeam

class TimeSlot(Base):
    """Time slot database model."""

    __tablename__ = "time_slots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    resource_id = Column(String, nullable=False)
    resource_type = Column(String(20), nullable=False)  # wash_bay or mobile_team
    is_available = Column(Boolean, nullable=False, default=True)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=True)
    buffer_minutes = Column(Integer, nullable=False, default=15)

    # ✅ String-based foreign keys (NO import needed)
    wash_bay_id = Column(String, ForeignKey("wash_bays.id"), nullable=True)
    mobile_team_id = Column(String, ForeignKey("mobile_teams.id"), nullable=True)

    # ❌ REMOVE relationships (breaks clean architecture)
    # wash_bay = relationship("WashBay", back_populates="time_slots")
    # mobile_team = relationship("MobileTeam", back_populates="time_slots")

    # ✅ Keep booking reference (within same table namespace)
    booking = relationship("Booking")  # Reference to booking if reserved

    @property
    def duration_minutes(self):
        """Get duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def __repr__(self):
        return f"<TimeSlot({self.start_time}, {self.resource_type}, available={self.is_available})>"
```

#### Step 2: Update Facilities Models (Remove Back-References)

```python
# app/features/facilities/adapters/models.py

class WashBayModel(Base):
    # ... existing fields ...

    # ❌ REMOVE this back-reference
    # time_slots = relationship("TimeSlot", back_populates="wash_bay")


class MobileTeamModel(Base):
    # ... existing fields ...

    # ❌ REMOVE this back-reference
    # time_slots = relationship("TimeSlot", back_populates="mobile_team")
```

#### Step 3: Update Repository Pattern

```python
# app/features/scheduling/adapters/repositories.py

class SchedulingRepository(ISchedulingRepository):

    async def get_time_slot_with_wash_bay(self, time_slot_id: str) -> Optional[TimeSlot]:
        """Get time slot with wash bay details."""
        from app.features.facilities.ports import IWashBayRepository

        # Get time slot
        time_slot = await self._session.get(TimeSlotModel, time_slot_id)
        if not time_slot:
            return None

        # If wash bay is needed, fetch via port (NOT relationship)
        if time_slot.wash_bay_id:
            wash_bay_repo = self._get_wash_bay_repository()  # Via DI
            wash_bay = await wash_bay_repo.get_by_id(time_slot.wash_bay_id)
            # Attach wash bay data to domain entity if needed

        return self._to_domain(time_slot)
```

#### Step 4: Create Migration

```bash
# Generate migration
alembic revision --autogenerate -m "Remove cross-feature relationships from scheduling"

# Review migration to ensure it only removes relationship metadata
# (No schema changes needed - foreign keys remain as-is)

# Apply migration
alembic upgrade head
```

### Testing Checklist

```bash
# 1. Run architecture compliance check
bash scripts/analyze_architecture.sh

# 2. Run unit tests
pytest app/features/scheduling/tests/unit/ -v

# 3. Run integration tests
pytest app/features/scheduling/tests/integration/ -v

# 4. Verify database integrity
# Check that foreign key constraints still work:
SELECT * FROM time_slots ts
LEFT JOIN wash_bays wb ON ts.wash_bay_id = wb.id
WHERE ts.wash_bay_id IS NOT NULL AND wb.id IS NULL;
# Should return 0 rows (no orphaned references)

# 5. Run full test suite
pytest -v
```

### Validation Criteria
- [ ] No imports from `app.features.facilities` in scheduling
- [ ] Foreign key constraints still enforced at DB level
- [ ] All tests pass
- [ ] Architecture compliance score increases to 98%

---

## Fix #2: Document UserRole Enum Exception

### Problem
```python
# app/features/facilities/api/mobile_teams_router.py:38
# app/features/facilities/api/wash_bays_router.py:37
from app.features.auth.domain import UserRole
```

### Solution: Document as Acceptable Pattern

This is actually **NOT a violation** because:
- UserRole is an immutable enum (value object)
- No business logic coupling
- Used only for authorization (cross-cutting concern)
- Alternative (duplication) has higher cost

#### Action: Create Architecture Decision Record

```bash
# Create ADR directory
mkdir -p docs/adr

# Create ADR
cat > docs/adr/001-shared-auth-enums.md << 'EOF'
# ADR-001: Shared Auth Enums

**Status**: Accepted
**Date**: 2025-10-02
**Deciders**: Architecture Team

## Context
Features need to check user roles for authorization (RBAC).
UserRole and UserStatus are defined in auth feature domain.

## Decision
Allow importing UserRole and UserStatus enums from auth.domain.

## Rationale
- Enums are immutable value objects (no side effects)
- RBAC is a cross-cutting concern (not business logic)
- Duplication would cause maintenance issues
- Risk is minimal (enum has no dependencies)

## Constraints
- ONLY UserRole and UserStatus allowed
- No other auth domain types can be imported
- Must be used only for authorization checks
- Must be documented at import site

## Alternatives Considered
1. Duplicate enums in each feature (rejected: high maintenance)
2. Move to shared layer (rejected: auth owns user roles)
3. Use string literals (rejected: no type safety)
EOF
```

#### Update Import Documentation

```python
# app/features/facilities/api/wash_bays_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Cross-feature import exception (ADR-001: Shared Auth Enums)
# UserRole is an immutable enum used only for authorization
from app.features.auth.domain import UserRole
```

### Validation Criteria
- [ ] ADR document created
- [ ] Import comments added
- [ ] Pattern documented in ARCHITECTURE.md
- [ ] Approved by tech lead

---

## Fix #3: Verify Bookings External Services Pattern (REVIEW ONLY)

### Current Implementation

✅ **ALREADY CORRECT** - Uses proper port/adapter pattern!

```python
# app/features/bookings/adapters/external_services.py

# 1. Consumer-owned port (interface)
from app.features.bookings.ports.external_services import (
    IExternalServiceValidator,  # ✓ Port in bookings feature
    IExternalVehicleValidator,  # ✓ Port in bookings feature
)

# 2. Adapter calls other feature's PUBLIC use cases
from app.features.services.use_cases.get_service import GetServiceUseCase
from app.features.vehicles.use_cases.get_vehicle import GetVehicleUseCase

# 3. Adapter implements consumer-owned port
class ExternalServiceValidatorAdapter(IExternalServiceValidator):
    """Adapter lives in bookings feature."""

    def __init__(self, get_service_use_case: GetServiceUseCase):
        self._get_service = get_service_use_case  # ✓ Injected dependency

    async def get_service_details(self, service_id: str):
        # ✓ Calls public use case
        # ✓ Converts to bookings feature DTO
        service = await self._get_service.execute(service_id)
        return ServiceDetails(...)  # ✓ Bookings domain type
```

### Why This is Correct

✅ Port (interface) defined in **consumer** feature (bookings)
✅ Adapter lives in **consumer** feature (bookings)
✅ Adapter calls **public use cases** (stable API)
✅ No direct domain coupling
✅ Dependencies injected at runtime

### Action Required: Add Architectural Test

```python
# tests/architecture/test_cross_feature_communication.py

def test_external_adapters_follow_port_pattern():
    """Verify cross-feature adapters use consumer-owned ports."""

    # Check bookings external services
    adapter_file = "app/features/bookings/adapters/external_services.py"
    port_file = "app/features/bookings/ports/external_services.py"

    # 1. Adapter must import from consumer-owned port
    assert imports_from(adapter_file, port_file)

    # 2. Adapter may only import public use cases from other features
    cross_imports = get_cross_feature_imports(adapter_file)
    assert all("use_cases" in imp for imp in cross_imports), \
        "Adapters can only import public use cases, not domain or adapters"

    # 3. Port interfaces must be in consumer feature
    assert port_file.startswith("app/features/bookings/")
```

### Validation Criteria
- [ ] Review adapter pattern (confirm correct)
- [ ] Add architectural test
- [ ] Document pattern in ARCHITECTURE.md
- [ ] Update compliance report to "✅ Pass"

---

## Post-Fix Validation

### 1. Run Architecture Compliance Check
```bash
bash scripts/analyze_architecture.sh
```

**Expected Output**:
```
✓ No cross-feature imports (except documented exceptions)
✓ Domain layer is pure
✓ Dependency direction correct
✓ Complete layer structure

Overall Compliance: 98% (Excellent)
```

### 2. Verify All Tests Pass
```bash
pytest -v --tb=short
```

### 3. Update Documentation
- [ ] Update ARCHITECTURE_COMPLIANCE_REPORT.md
- [ ] Update README.md with ADR references
- [ ] Add architectural testing to CI/CD

---

## Effort Estimate

| Task | Priority | Estimated Time | Actual Time |
|------|----------|----------------|-------------|
| Fix #1: Remove model import | Critical | 3 hours | ___ |
| Fix #2: Document UserRole | Low | 30 minutes | ___ |
| Fix #3: Add arch tests | Medium | 1 hour | ___ |
| Validation & Testing | High | 1 hour | ___ |
| **Total** | | **5.5 hours** | ___ |

---

## Success Criteria

✅ Architecture compliance score ≥ 98%
✅ Zero critical violations
✅ All tests passing
✅ ADRs documented
✅ Architectural tests in place
✅ CI/CD updated with compliance checks

---

## References

- [ARCHITECTURE_COMPLIANCE_REPORT.md](ARCHITECTURE_COMPLIANCE_REPORT.md) - Full analysis
- [scripts/analyze_architecture.sh](scripts/analyze_architecture.sh) - Compliance checker
- Clean Architecture by Robert C. Martin
- Hexagonal Architecture (Ports & Adapters) by Alistair Cockburn

---

*Fix guide created: 2025-10-02*
*Based on architecture compliance analysis*
