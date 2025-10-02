
ARCHITECTURE PATTERN (MUST FOLLOW)

Layers per feature: domain (entities, policies), ports (interfaces), use_cases (application), adapters (DB/cache/local-call), api (HTTP I/O).
Core for infra only: config, db, redis, errors, middleware, observability.
Interfaces for composition: create FastAPI app, mount routers, health/openapi.
Dependency direction (hard rule):
api → use_cases → domain
use_cases → ports
adapters → ports (+ core)

No feature-to-feature imports. Cross-feature calls happen only via a consumer-owned port and an adapter local that invokes the other feature’s public use case.
No business logic in api or adapters. Policies live in domain.
One DB schema (monolith) but tables are owned by features. No cross-feature SQL.

NON-NEGOTIABLE ARCHITECTURE RULES (ENFORCE)

No feature imports another feature’s internals; cross-feature sync calls go via a consumer-owned port + local adapter that invokes the public use case of the other feature.
No business logic outside domain/use_cases.
One transaction per initiating use case; no cross-feature shared DB transaction.
Domain code has zero FastAPI/Pydantic dependencies.
Add an import-linter (or equivalent) config to enforce api→use_cases→domain and forbid inter-feature imports.