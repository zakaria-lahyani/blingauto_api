# Facilities & Scheduling Management - Gap Analysis

**Date**: 2025-10-01
**Status**: Implementation Required
**Priority**: High (Required for Manager/Admin CRUD operations)

---

## Executive Summary

Analysis of requirements documents reveals **missing CRUD management features** for RG-FAC (Facilities) and RG-SCH (Scheduling) that are essential for Manager/Admin users to configure and manage the car wash operations.

### Current State ✅
- ✅ Domain entities exist in `app/features/scheduling/domain/entities.py`
- ✅ Business rules RG-FAC-001 to RG-FAC-004 implemented in entities
- ✅ Business rules RG-SCH-001 to RG-SCH-002 implemented in entities
- ✅ Basic availability checking endpoints exist (client-facing)

### Missing Features ❌
- ❌ **Facilities Management CRUD** (RG-FAC) - No admin endpoints to create/manage wash bays and mobile teams
- ❌ **Scheduling Configuration CRUD** (RG-SCH) - No admin endpoints to configure business hours
- ❌ **Management Dashboard** - No overview endpoints for managers/admins
- ❌ **Resource Utilization Tracking** - No capacity monitoring
- ❌ **Scheduling router dependencies** - Mock implementations, not wired up

---

## Requirements Analysis

###  RG-FAC: Facilities Management

According to `REGLES_DE_GESTION.md`:

#### RG-FAC-001: Configuration des baies (Wash Bays)
**Requirements**:
- Numérotation unique pour chaque baie
- Taille de véhicule maximale définie (compact à oversized)
- Liste des types d'équipements disponibles
- État: Actif/Inactif pour maintenance

**Current Status**: ✅ Entity exists, ❌ No CRUD endpoints

**Missing**:
```
POST   /api/v1/facilities/wash-bays          # Create wash bay (Admin/Manager)
GET    /api/v1/facilities/wash-bays          # List all wash bays
GET    /api/v1/facilities/wash-bays/{id}     # Get wash bay details
PATCH  /api/v1/facilities/wash-bays/{id}     # Update wash bay
DELETE /api/v1/facilities/wash-bays/{id}     # Deactivate wash bay
PUT    /api/v1/facilities/wash-bays/{id}/activate    # Activate wash bay
PUT    /api/v1/facilities/wash-bays/{id}/maintenance # Set maintenance mode
```

#### RG-FAC-002: Compatibilité des véhicules
**Requirements**:
- Hiérarchie des tailles: compact < standard < large < oversized
- Règle: Une baie peut accueillir sa taille maximale et toutes les tailles inférieures

**Current Status**: ✅ Implemented in `WashBay.can_accommodate_vehicle()`

#### RG-FAC-003: Configuration des équipes mobiles
**Requirements**:
- Rayon de service défini (défaut: 50km)
- Capacité journalière: Maximum 8 véhicules par jour par équipe
- Équipements transportés
- Localisation de base pour calculs de distance

**Current Status**: ✅ Entity exists, ❌ No CRUD endpoints

**Missing**:
```
POST   /api/v1/facilities/mobile-teams       # Create mobile team (Admin/Manager)
GET    /api/v1/facilities/mobile-teams       # List all mobile teams
GET    /api/v1/facilities/mobile-teams/{id}  # Get mobile team details
PATCH  /api/v1/facilities/mobile-teams/{id}  # Update mobile team
DELETE /api/v1/facilities/mobile-teams/{id}  # Deactivate mobile team
PUT    /api/v1/facilities/mobile-teams/{id}/activate  # Activate mobile team
```

#### RG-FAC-004: Calcul de distance de service
**Requirements**:
- Méthode: Calcul approximatif basé sur coordonnées GPS
- Limitation: Service uniquement dans le rayon défini
- Optimisation: Priorité aux équipes les plus proches

**Current Status**: ✅ Implemented in `MobileTeam.can_service_location()`

### RG-SCH: Scheduling Configuration

According to `REGLES_DE_GESTION.md`:

#### RG-SCH-001: Configuration des horaires
**Requirements**:
- Horaires spécifiques pour chaque jour de la semaine
- Définition des créneaux indisponibles (pauses)
- Jours de fermeture complète
- Créneaux: Durée par défaut de 30 minutes

**Current Status**: ✅ Entity exists (`BusinessHours`), ❌ No CRUD endpoints

**Missing**:
```
POST   /api/v1/scheduling/business-hours     # Create/update business hours (Admin/Manager)
GET    /api/v1/scheduling/business-hours     # Get business hours configuration
GET    /api/v1/scheduling/business-hours/{day}  # Get hours for specific day
PATCH  /api/v1/scheduling/business-hours/{day} # Update hours for specific day
POST   /api/v1/scheduling/business-hours/{day}/breaks # Add break period
DELETE /api/v1/scheduling/business-hours/{day}/breaks/{id} # Remove break period
POST   /api/v1/scheduling/blackout-dates     # Add blackout date (closure)
DELETE /api/v1/scheduling/blackout-dates/{date} # Remove blackout date
```

#### RG-SCH-002: Contraintes de planification
**Requirements**:
- Tampon: 15 minutes entre les réservations
- Réservation anticipée: Minimum 2 heures à l'avance
- Réservation le jour même: Autorisée selon configuration
- Maximum à l'avance: 90 jours maximum

**Current Status**: ✅ Implemented in `SchedulingConstraints`

---

## Functional Requirements from FUNCTIONAL_REQUIREMENTS.md

### 4.1 Facility Management

#### 4.1.1 Wash Bay Management
**Functional Requirements**:
- Configure wash bays with capacity and equipment
- Bay activation/deactivation
- Vehicle size accommodation
- Equipment type tracking

**Business Rules**:
- Each bay has maximum vehicle size capacity
- Bays can be temporarily deactivated for maintenance
- Equipment requirements matched to service needs

**Status**: ❌ Missing API endpoints

#### 4.1.2 Mobile Team Management
**Functional Requirements**:
- Mobile team configuration with service radius
- Team capacity and equipment tracking
- Location-based service assignment
- Daily capacity limits (default: 8 vehicles/day)

**Business Rules**:
- Service radius limits mobile team assignments
- Teams can be deactivated for scheduling
- Distance calculation for service feasibility

**Status**: ❌ Missing API endpoints

### 4.2 Scheduling System

#### 4.2.1 Availability Management
**Functional Requirements**:
- Real-time availability checking ✅ (exists)
- Business hours configuration per day ❌ (missing CRUD)
- Break period management ❌ (missing)
- Resource conflict detection ✅ (exists)

**Business Rules**:
- Business hours vary by day of week
- Minimum 30-minute time slots
- 15-minute buffer between bookings
- Break periods block availability

**Status**: Partial - need configuration endpoints

#### 4.2.2 Smart Scheduling
**Functional Requirements**:
- Automatic resource assignment ✅
- Conflict resolution ✅
- Alternative time suggestions ❌ (mock implementation)
- Preference-based scheduling ❌ (not implemented)

**Status**: Partial - need full implementation

---

## API Endpoints Summary from FUNCTIONAL_REQUIREMENTS.md

### 9.6 Scheduling Endpoints (Current)
```
✅ GET  /api/scheduling/availability        # Check availability
❌ GET  /api/scheduling/slots              # Get available time slots (mock)
❌ POST /api/scheduling/book               # Book time slot (mock)
❌ GET  /api/facilities/wash-bays          # List wash bays (MISSING)
❌ GET  /api/facilities/mobile-teams       # List mobile teams (MISSING)
```

---

## Implementation Plan

### Phase 1: Facilities CRUD (Priority: High)

**Endpoints to Implement**:

#### Wash Bays Management
```python
# app/features/facilities/api/wash_bays_router.py

@router.post("/wash-bays")  # Admin/Manager only
async def create_wash_bay(request: CreateWashBayRequest)

@router.get("/wash-bays")  # Admin/Manager/Washer
async def list_wash_bays(status: Optional[str] = None)

@router.get("/wash-bays/{id}")  # Admin/Manager/Washer
async def get_wash_bay(id: str)

@router.patch("/wash-bays/{id}")  # Admin/Manager only
async def update_wash_bay(id: str, request: UpdateWashBayRequest)

@router.put("/wash-bays/{id}/status")  # Admin/Manager only
async def update_wash_bay_status(id: str, status: ResourceStatus)

@router.delete("/wash-bays/{id}")  # Admin only (soft delete)
async def delete_wash_bay(id: str)
```

#### Mobile Teams Management
```python
# app/features/facilities/api/mobile_teams_router.py

@router.post("/mobile-teams")  # Admin/Manager only
async def create_mobile_team(request: CreateMobileTeamRequest)

@router.get("/mobile-teams")  # Admin/Manager/Washer
async def list_mobile_teams(status: Optional[str] = None)

@router.get("/mobile-teams/{id}")  # Admin/Manager/Washer
async def get_mobile_team(id: str)

@router.patch("/mobile-teams/{id}")  # Admin/Manager only
async def update_mobile_team(id: str, request: UpdateMobileTeamRequest)

@router.put("/mobile-teams/{id}/status")  # Admin/Manager only
async def update_mobile_team_status(id: str, status: ResourceStatus)

@router.delete("/mobile-teams/{id}")  # Admin only (soft delete)
async def delete_mobile_team(id: str)
```

### Phase 2: Scheduling Configuration CRUD (Priority: High)

**Endpoints to Implement**:

```python
# app/features/scheduling/api/configuration_router.py

@router.post("/business-hours")  # Admin/Manager only
async def configure_business_hours(request: ConfigureBusinessHoursRequest)

@router.get("/business-hours")  # Public or authenticated
async def get_business_hours()

@router.get("/business-hours/{day}")  # Public or authenticated
async def get_business_hours_for_day(day: str)

@router.patch("/business-hours/{day}")  # Admin/Manager only
async def update_business_hours_for_day(day: str, request: UpdateBusinessHoursRequest)

@router.post("/business-hours/{day}/breaks")  # Admin/Manager only
async def add_break_period(day: str, request: AddBreakPeriodRequest)

@router.delete("/business-hours/{day}/breaks/{break_id}")  # Admin/Manager only
async def remove_break_period(day: str, break_id: str)

@router.post("/blackout-dates")  # Admin/Manager only
async def add_blackout_date(request: AddBlackoutDateRequest)

@router.get("/blackout-dates")  # Public or authenticated
async def list_blackout_dates(start_date: date, end_date: date)

@router.delete("/blackout-dates/{date}")  # Admin/Manager only
async def remove_blackout_date(date: str)
```

### Phase 3: Management Dashboard (Priority: Medium)

**Endpoints to Implement**:

```python
# app/features/facilities/api/dashboard_router.py

@router.get("/dashboard/overview")  # Admin/Manager only
async def get_facilities_overview()
# Returns: total bays, active bays, utilization%, total teams, active teams

@router.get("/dashboard/utilization")  # Admin/Manager only
async def get_resource_utilization(date_range: str)
# Returns: utilization by resource, peak hours, bottlenecks

@router.get("/dashboard/capacity")  # Admin/Manager only
async def get_capacity_forecast(date_range: str)
# Returns: capacity forecast, booking trends
```

### Phase 4: Wire Up Dependencies (Priority: High)

**Tasks**:
1. Remove mock implementations from `app/features/scheduling/api/router.py`
2. Implement proper repository adapters
3. Wire up dependency injection in `app/interfaces/http_api.py`
4. Connect to database models
5. Add proper error handling

---

## Database Schema Required

### Wash Bays Table
```sql
CREATE TABLE wash_bays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bay_number VARCHAR(50) NOT NULL UNIQUE,
    max_vehicle_size VARCHAR(20) NOT NULL,
    equipment_types JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    location_latitude DECIMAL(10, 8),
    location_longitude DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

### Mobile Teams Table
```sql
CREATE TABLE mobile_teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name VARCHAR(100) NOT NULL,
    base_latitude DECIMAL(10, 8) NOT NULL,
    base_longitude DECIMAL(11, 8) NOT NULL,
    service_radius_km DECIMAL(6, 2) NOT NULL DEFAULT 50.0,
    daily_capacity INTEGER NOT NULL DEFAULT 8,
    equipment_types JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);
```

### Business Hours Table
```sql
CREATE TABLE business_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    day_of_week VARCHAR(20) NOT NULL UNIQUE,
    open_time TIME,
    close_time TIME,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,
    break_periods JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Blackout Dates Table
```sql
CREATE TABLE blackout_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blackout_date DATE NOT NULL UNIQUE,
    reason VARCHAR(255),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## RBAC Permission Matrix

| Action | Admin | Manager | Washer | Client |
|--------|-------|---------|--------|--------|
| Create wash bay | ✓ | ✓ | ✗ | ✗ |
| List wash bays | ✓ | ✓ | ✓ | ✗ |
| Update wash bay | ✓ | ✓ | ✗ | ✗ |
| Delete wash bay | ✓ | ✗ | ✗ | ✗ |
| Create mobile team | ✓ | ✓ | ✗ | ✗ |
| List mobile teams | ✓ | ✓ | ✓ | ✗ |
| Update mobile team | ✓ | ✓ | ✗ | ✗ |
| Delete mobile team | ✓ | ✗ | ✗ | ✗ |
| Configure business hours | ✓ | ✓ | ✗ | ✗ |
| View business hours | ✓ | ✓ | ✓ | ✓ (public) |
| Add blackout dates | ✓ | ✓ | ✗ | ✗ |
| View dashboard | ✓ | ✓ | ✗ | ✗ |

---

## Architecture Compliance

### Clean Architecture Layers

**Per feature (facilities, scheduling)**:
```
facilities/
├── domain/
│   ├── entities.py       # WashBay, MobileTeam, Location
│   └── exceptions.py     # Domain-specific errors
├── ports/
│   └── repositories.py   # IWashBayRepository, IMobileTeamRepository
├── use_cases/
│   ├── create_wash_bay.py
│   ├── list_wash_bays.py
│   ├── update_wash_bay.py
│   ├── create_mobile_team.py
│   ├── list_mobile_teams.py
│   └── update_mobile_team.py
├── adapters/
│   ├── models.py         # SQLAlchemy models
│   └── repositories.py   # Repository implementations
└── api/
    ├── router.py         # FastAPI routes
    ├── schemas.py        # Pydantic schemas
    └── dependencies.py   # DI wiring
```

### Import Rules

**MUST FOLLOW**:
- ✅ Domain has zero framework dependencies
- ✅ API → use_cases → domain
- ✅ Adapters → ports (implements interfaces)
- ✅ Use cases → ports (depends on interfaces)
- ✅ No cross-feature imports (use consumer-owned ports if needed)

---

## Testing Requirements

### Unit Tests (Domain)
```python
tests/unit/facilities/
├── test_wash_bay_entity.py
│   ├── test_create_wash_bay
│   ├── test_vehicle_size_compatibility
│   ├── test_activate_deactivate
│   └── test_validation_rules
└── test_mobile_team_entity.py
    ├── test_create_mobile_team
    ├── test_service_radius
    ├── test_distance_calculation
    └── test_validation_rules
```

### Integration Tests (Use Cases)
```python
tests/integration/facilities/
├── test_wash_bay_use_cases.py
│   ├── test_create_wash_bay_use_case
│   ├── test_list_wash_bays_use_case
│   └── test_update_wash_bay_use_case
└── test_mobile_team_use_cases.py
    ├── test_create_mobile_team_use_case
    ├── test_list_mobile_teams_use_case
    └── test_update_mobile_team_use_case
```

### E2E Tests (API)
```python
tests/e2e/facilities/
├── test_wash_bays_api.py
│   ├── test_create_wash_bay_as_admin
│   ├── test_list_wash_bays_as_manager
│   ├── test_update_wash_bay_as_manager
│   └── test_unauthorized_access_as_client
└── test_mobile_teams_api.py
    ├── test_create_mobile_team_as_admin
    ├── test_list_mobile_teams_as_washer
    └── test_forbidden_access_as_client
```

---

## Documentation Updates Required

### 1. Features Documentation
Update [docs/features/README.md](docs/features/README.md) to add:
- **Facilities Management** feature section
- Business rules RG-FAC-001 to RG-FAC-004
- Use cases and endpoints

### 2. API Documentation
Update [docs/api/README.md](docs/api/README.md) to add:
- Facilities management endpoints
- Scheduling configuration endpoints
- Management dashboard endpoints
- Request/response examples

### 3. Development Guide
Update [docs/development/README.md](docs/development/README.md):
- Add facilities/scheduling to common tasks
- Include examples for manager role

---

## Implementation Timeline

### Week 1: Facilities CRUD
- Day 1-2: Domain, ports, use cases
- Day 3-4: Adapters (models, repositories)
- Day 5: API layer and schemas

### Week 2: Scheduling Configuration
- Day 1-2: Business hours CRUD
- Day 3: Blackout dates
- Day 4-5: Wire up scheduling router

### Week 3: Dashboard & Testing
- Day 1-2: Management dashboard
- Day 3-4: Unit and integration tests
- Day 5: E2E tests and documentation

---

## Success Criteria

- ✅ All RG-FAC business rules implemented with CRUD endpoints
- ✅ All RG-SCH business rules implemented with configuration endpoints
- ✅ RBAC properly enforced (Manager/Admin only)
- ✅ Clean architecture compliance (import-linter passing)
- ✅ 90%+ test coverage for new features
- ✅ Documentation updated
- ✅ No mock implementations remaining
- ✅ Database migrations created and tested
- ✅ API versioning maintained (/api/v1/)

---

## References

- [REGLES_DE_GESTION.md](project_requirement/REGLES_DE_GESTION.md) - Business rules RG-FAC-001 to RG-FAC-004, RG-SCH-001 to RG-SCH-002
- [FUNCTIONAL_REQUIREMENTS.md](project_requirement/FUNCTIONAL_REQUIREMENTS.md) - Section 4: Scheduling & Resource Management
- [checklist.md](project_requirement/checklist.md) - Scheduling and Facilities requirements
- [Architecture Guide](docs/architecture/README.md) - Clean Architecture patterns
- [API Documentation](docs/api/README.md) - API standards

---

**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: 3 weeks (with testing and documentation)
**Assigned To**: Development Team
**Next Step**: Begin Phase 1 - Facilities CRUD Implementation
