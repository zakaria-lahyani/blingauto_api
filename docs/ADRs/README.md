# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant architectural decisions made in the BlingAuto API project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision along with its context and consequences.

## ADR Format

Each ADR follows this structure:

- **Title**: Short descriptive title
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Date**: When the decision was made
- **Context**: What is the issue we're addressing?
- **Decision**: What did we decide to do?
- **Consequences**: What are the positive and negative outcomes?
- **Alternatives Considered**: What other options did we evaluate?

## Index of ADRs

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./001-clean-architecture-adoption.md) | Clean Architecture Adoption | Accepted | 2025-09-15 |
| [ADR-002](./002-consumer-owned-ports-pattern.md) | Consumer-Owned Ports for Cross-Feature Communication | Accepted | 2025-09-20 |
| [ADR-003](./003-no-shared-transactions.md) | No Shared Database Transactions Across Features | Accepted | 2025-09-20 |
| [ADR-004](./004-api-versioning-strategy.md) | API Versioning Strategy | Accepted | 2025-09-22 |
| [ADR-005](./005-event-driven-side-effects.md) | Event-Driven Architecture for Side Effects | Accepted | 2025-09-25 |

---

## Creating New ADRs

When making a significant architectural decision:

1. Copy the [ADR template](./template.md)
2. Number it sequentially (e.g., `006-your-decision.md`)
3. Fill in all sections
4. Submit for review via pull request
5. Update this index once accepted

### What Deserves an ADR?

- Changes to system architecture or structure
- Selection of technologies or frameworks
- Design patterns or coding standards
- Cross-cutting concerns (logging, security, etc.)
- Major refactoring decisions
- Performance optimization strategies

### What Doesn't Need an ADR?

- Bug fixes
- Small feature additions
- Code formatting preferences
- Minor refactoring within a single module

---

## Quick Links

- [Architecture Guide](../architecture/README.md)
- [Development Guide](../development/README.md)
- [Features Documentation](../features/README.md)
