# ADR-001: Clean Architecture Adoption

**Status**: Accepted

**Date**: 2025-09-15

**Authors**: Development Team

**Stakeholders**: All developers, Technical leadership

---

## Context

### Background

The BlingAuto API started as a monolithic application with mixed concerns. As the codebase grew, we encountered several challenges:

- Business logic scattered across FastAPI routes, database models, and service layers
- Tight coupling to FastAPI and SQLAlchemy frameworks
- Difficulty testing business logic in isolation
- Hard to understand data flow and dependencies
- Challenge adding new features without breaking existing code

### Problem Statement

How do we structure the application to:
1. Separate business logic from infrastructure concerns
2. Make the codebase testable and maintainable
3. Allow independent evolution of features
4. Enable easy replacement of frameworks/libraries
5. Enforce clear dependency rules

---

## Decision

We will adopt **Clean Architecture** as our primary architectural pattern, implementing it with these specific layers per feature:

```
feature/
├── domain/          # Pure business logic (entities, value objects, policies)
├── ports/           # Interfaces (repository, external service contracts)
├── use_cases/       # Application business rules (orchestration)
├── adapters/        # Framework implementations (DB, external services)
└── api/            # HTTP interface (FastAPI routes, schemas)
```

### Key Principles

1. **Dependency Rule**: Dependencies point inward only
   - `api` → `use_cases` → `domain`
   - `adapters` → `ports` (implements interfaces)
   - `use_cases` → `ports` (depends on interfaces)

2. **Domain Purity**: Domain layer has ZERO framework dependencies
   - No FastAPI, Pydantic, SQLAlchemy, Redis
   - Only Python stdlib and domain code
   - 100% framework-agnostic

3. **Ports & Adapters**: All external dependencies abstracted via interfaces
   - Repository interfaces in `ports/`
   - SQLAlchemy implementations in `adapters/`
   - Easy to swap implementations

4. **Use Cases as Entry Points**: All application logic flows through use cases
   - One use case = one transaction
   - Use case receives Request DTO
   - Use case returns Response DTO
   - No business logic in API layer

---

## Consequences

### Positive Consequences

- **Testability**: Business logic can be tested without any framework
  - Unit tests run in milliseconds
  - No database required for domain tests
  - Mock repositories via interfaces

- **Maintainability**: Clear separation of concerns
  - Easy to locate business rules (always in `domain/`)
  - Changes to infrastructure don't affect business logic
  - Each layer has single responsibility

- **Framework Independence**: Can swap FastAPI for Flask/Django
  - Domain layer unchanged
  - Only API layer needs rewriting
  - SQLAlchemy can be replaced with different ORM

- **Feature Isolation**: Features are self-contained modules
  - Minimal coupling between features
  - Can extract feature to microservice easily
  - Teams can work independently

- **Onboarding**: New developers understand structure quickly
  - Consistent pattern across all features
  - Clear where to add new code
  - Architecture enforced by import-linter

### Negative Consequences

- **More Boilerplate**: More files and abstractions
  - Each entity needs repository interface + implementation
  - Request/Response DTOs for each use case
  - Conversion between domain entities and DB models
  - **Mitigation**: Code generators, clear templates

- **Learning Curve**: Team needs to understand Clean Architecture
  - Not as intuitive as MVC or simple layered architecture
  - Requires discipline to follow rules
  - **Mitigation**: Documentation, pair programming, code reviews

- **Initial Slowdown**: More upfront design work
  - Need to think about layer boundaries
  - Define interfaces before implementation
  - **Mitigation**: Benefits compound over time

### Neutral Consequences

- **More Files**: More granular file structure
- **Explicit Dependencies**: All dependencies passed via constructors

---

## Alternatives Considered

### Alternative 1: Traditional Layered Architecture

**Description**: Simple 3-layer architecture (Presentation → Business → Data)

**Pros**:
- Simpler, less boilerplate
- Faster initial development
- Team already familiar

**Cons**:
- Business logic often leaks into presentation/data layers
- Tight coupling to frameworks
- Hard to test in isolation
- Dependencies flow in both directions

**Why Not Chosen**: Doesn't solve our framework coupling and testability issues.

### Alternative 2: Feature-Based Modules (Without Clean Architecture)

**Description**: Organize by features but without strict layer separation

**Pros**:
- Feature isolation achieved
- Simpler than Clean Architecture
- Less boilerplate

**Cons**:
- No enforcement of dependency rules
- Business logic still mixed with infrastructure
- Framework coupling remains

**Why Not Chosen**: Solves organization but not architecture quality issues.

### Alternative 3: Hexagonal Architecture (Ports & Adapters Only)

**Description**: Only use ports/adapters without explicit use_cases layer

**Pros**:
- Simpler than Clean Architecture
- Still achieves framework independence
- Clear port boundaries

**Cons**:
- Application logic scattered across domain or adapters
- No clear orchestration layer
- Transaction boundaries unclear

**Why Not Chosen**: Use cases layer provides valuable orchestration and transaction control.

---

## Implementation

### Migration Path

1. **Phase 1**: Create new structure alongside old code
   - Set up directory structure
   - Implement one feature (bookings) in new architecture
   - Prove pattern works

2. **Phase 2**: Migrate remaining features
   - Auth feature
   - Services feature
   - Vehicles feature
   - Scheduling feature

3. **Phase 3**: Remove old code
   - Delete legacy files
   - Update all imports
   - Run full test suite

4. **Phase 4**: Enforce architecture
   - Add import-linter configuration
   - CI/CD checks for violations
   - Documentation complete

### Timeline

- Phase 1: 2025-09-15 to 2025-09-22 ✅
- Phase 2: 2025-09-23 to 2025-09-28 ✅
- Phase 3: 2025-09-29 to 2025-09-30 ✅
- Phase 4: 2025-10-01 ✅
- Complete: 2025-10-01

### Success Criteria

- ✅ All features follow consistent structure
- ✅ Domain layer has zero framework imports
- ✅ Unit tests run without database (<100ms per test)
- ✅ Import-linter enforces all rules
- ✅ 90%+ test coverage maintained
- ✅ New features follow pattern automatically

---

## Related Decisions

- [ADR-002: Consumer-Owned Ports Pattern](./002-consumer-owned-ports-pattern.md)
- [ADR-003: No Shared Transactions](./003-no-shared-transactions.md)
- [ADR-005: Event-Driven Side Effects](./005-event-driven-side-effects.md)

---

## References

- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Architecture Guide](../architecture/README.md)

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-09-15 | Team | Initial draft and acceptance |
| 2025-10-01 | Team | Updated with implementation results |
