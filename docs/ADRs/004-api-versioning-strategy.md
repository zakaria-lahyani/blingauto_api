# ADR-004: API Versioning Strategy

**Status**: Accepted

**Date**: 2025-09-22

**Authors**: Development Team

**Stakeholders**: All developers, Frontend team, API consumers

---

## Context

### Background

APIs evolve over time with new features, changes, and deprecations. Without a versioning strategy:

- Breaking changes affect existing clients
- Cannot iterate on API design
- Difficult to maintain backward compatibility
- Unclear which version client is using

### Problem Statement

How do we version our API to:
1. Allow API evolution without breaking existing clients
2. Support multiple API versions simultaneously
3. Provide clear migration paths
4. Make versioning obvious to API consumers
5. Keep implementation complexity manageable

---

## Decision

We will use **URL Path Versioning** with the prefix `/api/v{major}/` for all API endpoints.

### Implementation

```python
# app/interfaces/http_api.py
API_V1_PREFIX = "/api/v1"

app.include_router(
    auth_router,
    prefix=f"{API_V1_PREFIX}/auth",
    tags=["Authentication"]
)

app.include_router(
    bookings_router,
    prefix=f"{API_V1_PREFIX}/bookings",
    tags=["Bookings"]
)
```

### URL Structure

```
# Current Version (v1)
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/bookings
POST   /api/v1/bookings
GET    /api/v1/bookings/{id}

# Future Version (v2) - when needed
POST   /api/v2/auth/register
GET    /api/v2/bookings
```

### Versioning Rules

1. **Major Version**: Increment for breaking changes
   - Changed response structure
   - Removed fields
   - Changed authentication
   - Different business logic

2. **No Minor Versions in URL**: Use feature flags/content negotiation
   - Additive changes don't require new version
   - New optional fields
   - New endpoints
   - New query parameters

3. **Version Support Policy**:
   - Support current version (v1) indefinitely
   - Support previous version (v0) for 6 months after new version
   - Provide migration guide for breaking changes
   - Deprecation warnings in headers

4. **Backward Compatibility**:
   - Always additive within major version
   - New optional fields OK
   - Never remove fields in same version
   - Never change field types in same version

---

## Consequences

### Positive Consequences

- **Clear Versioning**: Version immediately visible in URL
  ```
  GET /api/v1/bookings  # Clearly version 1
  ```

- **Easy Routing**: Simple to route different versions
  ```python
  # v1 routes
  app.include_router(v1_router, prefix="/api/v1")

  # v2 routes (when needed)
  app.include_router(v2_router, prefix="/api/v2")
  ```

- **Client Flexibility**: Clients choose when to upgrade
  - Can continue using v1 while testing v2
  - No forced upgrades
  - Clear migration path

- **Cache-Friendly**: Different URLs = different cache entries
  - CDN can cache both versions
  - No cache invalidation issues

- **Documentation**: Easy to document versions
  ```
  Swagger: /docs     → v1 documentation
  Swagger: /docs/v2  → v2 documentation (future)
  ```

### Negative Consequences

- **URL Verbosity**: Extra `/v1/` in every URL
  - **Mitigation**: Acceptable trade-off for clarity

- **Multiple Codebases**: Supporting multiple versions = more code
  - **Mitigation**: Share domain/use_cases, only duplicate API layer
  - **Mitigation**: Deprecate old versions after migration period

- **Documentation Duplication**: Need docs for each version
  - **Mitigation**: Generate docs automatically
  - **Mitigation**: Clear migration guides

### Neutral Consequences

- **Testing**: Need to test all supported versions
- **Deployment**: All versions deployed together (monolith)

---

## Alternatives Considered

### Alternative 1: Header-Based Versioning

**Description**: Use `Accept` or custom header for version
```http
GET /api/bookings
Accept: application/vnd.blingauto.v1+json
```

**Pros**:
- Cleaner URLs
- RESTful purist approach
- Can use content negotiation

**Cons**:
- Less visible to developers
- Harder to test (need to set headers)
- Cache complications
- Not as intuitive

**Why Not Chosen**: URL versioning is more explicit and developer-friendly.

### Alternative 2: Query Parameter Versioning

**Description**: Use query parameter for version
```
GET /api/bookings?version=1
```

**Pros**:
- Optional (can have default)
- Flexible

**Cons**:
- Easy to forget
- Not RESTful
- Harder to route
- Caching issues

**Why Not Chosen**: Less explicit, harder to enforce.

### Alternative 3: Subdomain Versioning

**Description**: Use subdomain for version
```
https://api-v1.blingauto.com/bookings
https://api-v2.blingauto.com/bookings
```

**Pros**:
- Very clear separation
- Can deploy versions independently
- Good for microservices

**Cons**:
- DNS configuration needed
- SSL certificates for each subdomain
- More complex deployment
- Over-engineering for monolith

**Why Not Chosen**: Too complex for current needs.

### Alternative 4: No Versioning

**Description**: Never make breaking changes, only additive

**Pros**:
- Simplest
- No versioning overhead
- No migration needed

**Cons**:
- Cannot fix design mistakes
- API becomes bloated over time
- Unclear how to evolve
- Tech debt accumulates

**Why Not Chosen**: Unrealistic long-term, limits evolution.

---

## Implementation

### Version 1 (Current)

All existing endpoints under `/api/v1/`:

```python
# app/interfaces/http_api.py
from fastapi import FastAPI

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="BlingAuto API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register all v1 routers
app.include_router(auth_router, prefix=f"{API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(bookings_router, prefix=f"{API_V1_PREFIX}/bookings", tags=["Bookings"])
app.include_router(services_router, prefix=f"{API_V1_PREFIX}/services", tags=["Services"])
app.include_router(vehicles_router, prefix=f"{API_V1_PREFIX}/vehicles", tags=["Vehicles"])
```

### Version 2 (Future)

When breaking changes needed:

```python
# app/interfaces/http_api.py
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"

# v1 (maintained)
from app.features.bookings.api import router as bookings_v1_router
app.include_router(bookings_v1_router, prefix=f"{API_V1_PREFIX}/bookings")

# v2 (new)
from app.features.bookings.api_v2 import router as bookings_v2_router
app.include_router(bookings_v2_router, prefix=f"{API_V2_PREFIX}/bookings")
```

### Shared Logic

Reuse domain and use cases:

```
app/features/bookings/
├── domain/              # Shared across versions
├── use_cases/           # Shared across versions
├── api/                 # v1 routes
│   ├── router.py
│   └── schemas.py
└── api_v2/              # v2 routes (when needed)
    ├── router.py
    └── schemas.py
```

### Deprecation Strategy

**Add Deprecation Header**:
```python
@router.get("/old-endpoint", deprecated=True)
async def old_endpoint():
    response = {...}
    response.headers["X-API-Deprecation"] = "This endpoint is deprecated. Use /api/v2/new-endpoint"
    response.headers["X-API-Sunset"] = "2026-01-01"  # Removal date
    return response
```

**Deprecation Timeline**:
1. Announce new version (v2) - 3 months notice
2. Release v2 with migration guide
3. Add deprecation warnings to v1 - 3 months
4. Announce sunset date for v1 - 6 months notice
5. Remove v1 support

### Migration Guide Template

When releasing v2, provide:

```markdown
# Migration Guide: v1 → v2

## Breaking Changes

### 1. Booking Status Changed
- v1: `status: "pending" | "confirmed" | "completed"`
- v2: `status: { code: "PENDING", label: "Pending" }`

**Migration**:
```javascript
// v1
if (booking.status === "pending") { ... }

// v2
if (booking.status.code === "PENDING") { ... }
```

### 2. Date Format Changed
- v1: Unix timestamps (1234567890)
- v2: ISO 8601 strings ("2025-10-01T14:30:00Z")

**Migration**: Use date parsing library
```

### Timeline

- Phase 1 (v1 Implementation): 2025-09-22 ✅
- Phase 2 (Documentation): 2025-09-23 ✅
- Phase 3 (v2 Planning): When breaking changes needed
- Phase 4 (v2 Implementation): TBD
- Phase 5 (v1 Deprecation): TBD + 6 months

### Success Criteria

- ✅ All endpoints under `/api/v1/` prefix
- ✅ Version visible in OpenAPI docs
- ✅ Clear routing separation
- ✅ Can add v2 without affecting v1
- ✅ Documentation reflects versioning
- 🔄 Migration guide template ready (for future use)

---

## Related Decisions

- [ADR-001: Clean Architecture Adoption](./001-clean-architecture-adoption.md)
- Related to API design and client contracts

---

## References

- [REST API Versioning Best Practices](https://www.freecodecamp.org/news/rest-api-best-practices-rest-endpoint-design-examples/)
- [Stripe API Versioning](https://stripe.com/docs/api/versioning)
- [AWS API Versioning](https://docs.aws.amazon.com/general/latest/gr/api-versioning.html)
- [API Documentation](../api/README.md)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-09-22 | Team | Initial draft and acceptance |
| 2025-09-23 | Team | Added implementation details |
| 2025-10-01 | Team | Added deprecation strategy |
