# ADR-001: Shared Auth Enums

**Status**: Accepted
**Date**: 2025-10-02
**Deciders**: Architecture Team
**Related**: [ARCHITECTURE_COMPLIANCE_REPORT.md](../../ARCHITECTURE_COMPLIANCE_REPORT.md)

---

## Context

The BlingAuto API follows strict clean architecture principles where features must not import from other features' internals. However, role-based access control (RBAC) requires user role checking across multiple features.

**The Problem**:
- UserRole and UserStatus enums are defined in `app.features.auth.domain`
- Other features (facilities, bookings, scheduling, etc.) need to check user roles for authorization
- Importing from another feature's domain violates the "no cross-feature imports" rule

**Current Usage**:
```python
# app/features/facilities/api/wash_bays_router.py
from app.features.auth.domain import UserRole

@router.get("/")
async def list_wash_bays(
    current_user: User = Depends(get_current_active_user),
):
    # Check if user has admin/manager role
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403)
```

**Alternatives Considered**:

### Option 1: Duplicate Enums in Each Feature (Rejected)
```python
# app/features/facilities/domain/enums.py
class FacilityUserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    WASHER = "washer"
    CUSTOMER = "customer"
```

**Pros**:
- No cross-feature imports
- Full feature independence

**Cons**:
- High maintenance burden (update in 7 places)
- Risk of divergence between features
- Duplicate code violates DRY principle
- Semantic confusion (same concept, different types)

### Option 2: Move to Shared Layer (Rejected)
```python
# app/shared/auth/enums.py
class UserRole(Enum):
    ADMIN = "admin"
    ...
```

**Pros**:
- Available to all features
- Single source of truth

**Cons**:
- Auth feature loses ownership of its domain concepts
- Shared layer should be for infrastructure, not domain
- Violates domain-driven design (bounded contexts)
- Makes auth feature incomplete

### Option 3: Use String Literals (Rejected)
```python
if current_user.role not in ["admin", "manager"]:
    raise HTTPException(status_code=403)
```

**Pros**:
- No imports needed
- Simple

**Cons**:
- No type safety
- Magic strings (hard to refactor)
- No IDE autocomplete
- Error-prone (typos not caught)

### Option 4: Allow Auth Enum Imports (Accepted)
```python
# Cross-feature import exception (ADR-001: Shared Auth Enums)
# UserRole is an immutable enum used only for authorization
from app.features.auth.domain import UserRole
```

**Pros**:
- Single source of truth (auth owns roles)
- Type-safe role checking
- IDE autocomplete and refactoring support
- Minimal maintenance burden
- Clear semantics

**Cons**:
- Technical violation of "no cross-feature imports"
- Creates slight coupling to auth feature

---

## Decision

**We will allow importing `UserRole` and `UserStatus` enums from `app.features.auth.domain` in other features.**

This is the **only exception** to the "no cross-feature imports" rule.

---

## Rationale

### 1. Enums are Value Objects (No Side Effects)
UserRole is an **immutable value object** with:
- No dependencies
- No business logic
- No side effects
- Pure data representation

```python
class UserRole(str, Enum):
    """User roles (immutable value object)."""
    ADMIN = "admin"
    MANAGER = "manager"
    WASHER = "washer"
    CUSTOMER = "customer"
```

### 2. RBAC is a Cross-Cutting Concern
Authorization is not business logic—it's an **infrastructure concern** that spans all features:
- Every feature needs role-based access control
- Roles are system-wide, not feature-specific
- Auth feature is the authoritative source

### 3. Risk is Minimal
The coupling is **minimal and one-directional**:
- Features depend on auth enums (read-only)
- Auth feature has no dependencies on other features
- No circular dependencies possible
- Enum changes are infrequent and coordinated

### 4. Practical Trade-Off
The alternative (duplication) has **higher cost**:
- 7 features × 2 enums = 14 copies to maintain
- Risk of divergence increases over time
- Refactoring becomes error-prone
- Developer cognitive load increases

---

## Constraints

### Allowed Imports
**ONLY** these two enums may be imported across features:
```python
from app.features.auth.domain import UserRole
from app.features.auth.domain import UserStatus
```

### Not Allowed
**NO** other auth domain types may be imported:
```python
# ❌ FORBIDDEN
from app.features.auth.domain import User
from app.features.auth.domain import PasswordPolicy
from app.features.auth.domain import Session
```

### Usage Requirements
1. **Must be documented** at each import site:
```python
# Cross-feature import exception (ADR-001: Shared Auth Enums)
# UserRole is an immutable enum used only for authorization
from app.features.auth.domain import UserRole
```

2. **Must be used only for authorization**, not business logic:
```python
# ✅ ALLOWED (authorization check)
if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
    raise HTTPException(status_code=403)

# ❌ FORBIDDEN (business logic)
if current_user.role == UserRole.CUSTOMER:
    discount = calculate_customer_discount()  # Business logic!
```

3. **Must be in API layer or use cases**, not domain:
```python
# ✅ ALLOWED (API layer)
# app/features/facilities/api/wash_bays_router.py
from app.features.auth.domain import UserRole

# ✅ ALLOWED (use case for authorization)
# app/features/facilities/use_cases/delete_wash_bay.py
from app.features.auth.domain import UserRole

# ❌ FORBIDDEN (domain layer)
# app/features/facilities/domain/wash_bay.py
from app.features.auth.domain import UserRole
```

---

## Consequences

### Positive
- ✅ Type-safe role checking across all features
- ✅ Single source of truth (auth owns roles)
- ✅ Low maintenance burden
- ✅ IDE support (autocomplete, refactoring)
- ✅ Clear semantics and ownership

### Negative
- ⚠️ Minor coupling between features and auth
- ⚠️ Requires documentation at import sites
- ⚠️ Exception to architecture rules (can be confusing)

### Mitigations
- Document this ADR and reference it at all import sites
- Add architectural tests to enforce constraints
- Regular code reviews to prevent misuse
- Clear guidelines in ARCHITECTURE.md

---

## Compliance

### Architectural Tests
```python
# tests/architecture/test_auth_enum_exception.py

def test_only_auth_enums_imported_from_auth():
    """Verify only UserRole and UserStatus are imported from auth.domain."""
    violations = []

    for feature in get_features():
        if feature == "auth":
            continue

        imports = get_cross_feature_imports(feature, "auth.domain")
        for imp in imports:
            if imp not in ["UserRole", "UserStatus"]:
                violations.append((feature, imp))

    assert violations == [], \
        f"Only UserRole/UserStatus allowed from auth.domain: {violations}"

def test_auth_enums_not_used_in_domain_layer():
    """Verify auth enums not imported in other features' domain layers."""
    violations = []

    for feature in get_features():
        if feature == "auth":
            continue

        domain_files = glob(f"app/features/{feature}/domain/**/*.py")
        for file in domain_files:
            if "from app.features.auth.domain import" in read(file):
                violations.append(file)

    assert violations == [], \
        f"Auth enums must not be used in domain layers: {violations}"
```

### Current Usage (Verified Compliant)
- ✅ `app/features/facilities/api/wash_bays_router.py:37` - API layer authorization
- ✅ `app/features/facilities/api/mobile_teams_router.py:38` - API layer authorization

---

## Review Schedule

**Review Date**: Every 6 months or when adding new features

**Review Questions**:
1. Is this exception still necessary?
2. Has it caused any issues or confusion?
3. Are there new alternatives available?
4. Is the usage still constrained correctly?

---

## References

- Clean Architecture by Robert C. Martin (Chapter 22: The Clean Architecture)
- Domain-Driven Design by Eric Evans (Chapter 14: Maintaining Model Integrity)
- [ARCHITECTURE_COMPLIANCE_REPORT.md](../../ARCHITECTURE_COMPLIANCE_REPORT.md)
- [ARCHITECTURE_FIX_GUIDE.md](../../ARCHITECTURE_FIX_GUIDE.md)

---

## Appendix: Related Discussions

### Why Not Create a Separate Auth Service?
In a microservices architecture, auth would be a separate service with its own API. However, BlingAuto uses a modular monolith where:
- Features share a single database
- No network boundaries between features
- Auth is tightly integrated (sessions, tokens)
- System roles are global, not per-feature

A separate auth service would be over-engineering for the current scale.

### Why Not Use Protocols/Interfaces?
Python protocols could theoretically abstract the enum, but:
- Enums are already data (no behavior to abstract)
- Protocol overhead provides no benefit
- Would make code more complex, not simpler
- Type checkers would still see the coupling

### Future Evolution
If BlingAuto evolves to microservices:
- Create separate Auth Service
- Roles become JWT claims
- Features validate claims, not enums
- This ADR becomes obsolete

---

*Last Updated: 2025-10-02*
*Next Review: 2025-04-02*
