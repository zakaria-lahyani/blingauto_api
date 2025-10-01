# Services Feature Rules

## Business Rules

### RG-SVC-001: Category Management
- Category names must be unique (case-insensitive)
- Reserved names: 'admin', 'system', 'internal'
- Category name: 1-100 characters
- Description: max 500 characters

### RG-SVC-002: Category Deletion
- Cannot delete categories with active services
- Must deactivate all services first
- Soft delete only (set status to INACTIVE)

### RG-SVC-003: Service Management
- Service names must be unique within category
- Service name: 1-100 characters
- Description: max 1000 characters

### RG-SVC-004: Pricing Rules
- Service price must be positive
- Maximum prices by type:
  - Standard: $500.00
  - Premium: $1,000.00
  - Luxury: $2,000.00
- Price precision: max 2 decimal places

### RG-SVC-005: Duration Rules
- Duration must be positive
- Must be in 15-minute increments
- Minimum: 15 minutes
- Maximum: 480 minutes (8 hours)

### RG-SVC-006: Popular Services
- Maximum 3 popular services per category
- Only active services can be popular
- Automatically remove popular status when deactivating

## Technical Rules

### RG-SVC-007: Data Integrity
- All services must belong to an active category
- Display order must be non-negative
- Status transitions: ACTIVE ↔ INACTIVE ↔ ARCHIVED

### RG-SVC-008: Business Analytics
- Track service usage statistics
- Calculate category performance metrics
- Pricing recommendations based on similar services