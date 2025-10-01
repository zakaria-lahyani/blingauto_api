# Vehicles Feature Rules

## Business Rules

### RG-VEH-001: Vehicle Make Validation
- Make must be at least 2 characters
- Maximum 50 characters
- Auto-capitalize first letter of each word

### RG-VEH-002: Vehicle Model Validation
- Model cannot be empty
- Maximum 50 characters
- Auto-capitalize first letter of each word

### RG-VEH-003: Vehicle Year Validation
- Year cannot be before 1900
- Year cannot be more than 2 years in the future
- Must be a valid integer

### RG-VEH-004: Vehicle Color Validation
- Color must be at least 2 characters
- Maximum 30 characters
- Auto-capitalize first letter of each word

### RG-VEH-005: License Plate Management
- License plate must be at least 2 characters
- Maximum 20 characters
- Auto-convert to uppercase
- Must be unique per customer

### RG-VEH-006: Default Vehicle Rules
- Each customer can have only one default vehicle
- Must unset current default before setting new one
- Auto-set first vehicle as default
- Cannot delete default vehicle without setting another

### RG-VEH-007: Vehicle Deletion
- Cannot delete vehicle with active bookings
- Cannot delete default vehicle (must set another as default first)
- Soft delete only (set is_deleted flag)
- Maintain audit trail with deleted_at timestamp

## Technical Rules

### RG-VEH-008: Data Normalization
- Make, model, color: Title case
- License plate: Upper case
- Trim whitespace from all fields

### RG-VEH-009: Business Intelligence
- Track vehicle age distribution
- Monitor popular makes and colors
- Calculate usage statistics per vehicle