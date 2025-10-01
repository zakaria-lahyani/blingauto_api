# Operational Features Implementation Plan

**Project**: BlingAuto Car Wash API - Operational Management
**Date**: 2025-10-02
**Status**: Planning Phase

---

## Overview

This plan details the implementation of operational features for day-to-day car wash business management, including staff management, walk-in services, inventory, expenses, and analytics.

---

## Feature Requirements Summary

### 1. Washer Management (Staff Module)
**Actors**: Admin, Manager
**Purpose**: Complete staff lifecycle management

**Requirements**:
- ✅ CRUD operations for washer profiles
- ✅ Document storage (ID, certificates, contracts)
- ✅ Attendance/presence tracking
- ✅ Working hours management (schedules, shifts)
- ✅ Performance metrics
- ✅ Assignment to wash bays/mobile teams

### 2. Walk-in Service Management
**Actors**: Washer
**Purpose**: Handle non-booked vehicles (walk-ins)

**Requirements**:
- ✅ Quick vehicle registration (without full profile)
- ✅ Service selection and pricing
- ✅ Automatic profit calculation
- ✅ Payment processing
- ✅ Receipt generation
- ✅ Daily walk-in reports

### 3. Inventory Management (Products/Stock)
**Actors**: Manager, Admin
**Purpose**: Track cleaning products and supplies

**Requirements**:
- ✅ Product CRUD (name, SKU, category, unit)
- ✅ Stock level tracking
- ✅ Low stock alerts
- ✅ Stock movements (in/out)
- ✅ Supplier management
- ✅ Usage tracking per service
- ✅ Inventory valuation

### 4. Expense Management
**Actors**: Manager, Admin
**Purpose**: Track operational expenses

**Requirements**:
- ✅ Expense CRUD (amount, category, date, description)
- ✅ Expense categories (utilities, supplies, maintenance, salaries)
- ✅ Receipt/invoice attachment
- ✅ Approval workflow
- ✅ Monthly expense reports
- ✅ Budget tracking

### 5. Analytics Dashboard
**Actors**: Manager, Admin
**Purpose**: Business intelligence and performance tracking

**Requirements**:
- ✅ Revenue analytics (daily/weekly/monthly)
- ✅ Service performance (most popular, profitable)
- ✅ Staff performance (services completed, revenue generated)
- ✅ Customer analytics (retention, frequency)
- ✅ Operational efficiency (bay utilization, wait times)
- ✅ Financial KPIs (profit margins, expenses ratio)
- ✅ Trend analysis and forecasting

---

## Architecture Design

### New Features to Add

```
app/features/
├── staff/              # NEW - Washer management
├── walkins/            # NEW - Walk-in service tracking
├── inventory/          # NEW - Product/stock management
├── expenses/           # NEW - Expense tracking
└── analytics/          # NEW - Dashboard and reports
```

### Each Feature Structure (Clean Architecture)

```
app/features/{feature}/
├── domain/
│   ├── entities.py         # Business entities
│   ├── value_objects.py    # Value objects
│   ├── policies.py         # Business rules
│   └── enums.py            # Enumerations
├── ports/
│   ├── repositories.py     # Repository interfaces
│   └── services.py         # Service interfaces
├── use_cases/
│   ├── create_*.py         # Create use cases
│   ├── update_*.py         # Update use cases
│   ├── list_*.py           # List/query use cases
│   └── delete_*.py         # Delete use cases
├── adapters/
│   ├── models.py           # SQLAlchemy models
│   ├── repositories.py     # Repository implementations
│   └── services.py         # Service implementations
└── api/
    ├── router.py           # FastAPI routes
    ├── schemas.py          # Pydantic DTOs
    └── dependencies.py     # Dependency injection
```

---

## Feature 1: Staff Management (Washer Module)

### Domain Entities

```python
# app/features/staff/domain/entities.py

class StaffMember:
    """Washer/staff member entity."""
    id: str
    user_id: str  # Link to auth.User
    employee_code: str
    first_name: str
    last_name: str
    phone: str
    email: str
    hire_date: date
    employment_type: EmploymentType  # full_time, part_time, contractor
    status: StaffStatus  # active, on_leave, suspended, terminated
    hourly_rate: Decimal
    assigned_bay_id: Optional[str]
    assigned_team_id: Optional[str]
    skills: List[ServiceType]  # What services they can perform
    documents: List[StaffDocument]

    # Performance tracking
    total_services_completed: int
    total_revenue_generated: Decimal
    average_rating: Decimal

    # Business rules
    def can_perform_service(self, service_type: ServiceType) -> bool
    def calculate_earnings(self, start_date: date, end_date: date) -> Decimal
    def is_available(self, datetime: datetime) -> bool


class StaffDocument:
    """Staff document (ID, certificate, contract)."""
    id: str
    staff_id: str
    document_type: DocumentType  # id_card, certificate, contract, other
    document_name: str
    file_path: str  # S3 or local storage path
    uploaded_at: datetime
    expires_at: Optional[datetime]
    verified: bool


class Attendance:
    """Attendance/presence record."""
    id: str
    staff_id: str
    date: date
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    status: AttendanceStatus  # present, absent, late, half_day, on_leave
    hours_worked: Decimal
    notes: Optional[str]

    # Business rules
    def calculate_hours_worked(self) -> Decimal
    def is_late(self, shift_start: time) -> bool


class WorkSchedule:
    """Staff work schedule/shift."""
    id: str
    staff_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    shift_start: time
    shift_end: time
    break_duration_minutes: int
    is_active: bool
    effective_from: date
    effective_until: Optional[date]
```

### Key Use Cases

```python
# Staff CRUD
- CreateStaffMemberUseCase
- UpdateStaffMemberUseCase
- GetStaffMemberUseCase
- ListStaffMembersUseCase
- DeactivateStaffMemberUseCase

# Document Management
- UploadStaffDocumentUseCase
- DeleteStaffDocumentUseCase
- VerifyStaffDocumentUseCase
- ListStaffDocumentsUseCase

# Attendance
- CheckInStaffUseCase
- CheckOutStaffUseCase
- RecordAttendanceUseCase
- GetAttendanceReportUseCase
- UpdateAttendanceUseCase

# Schedule Management
- CreateWorkScheduleUseCase
- UpdateWorkScheduleUseCase
- GetStaffScheduleUseCase
- AssignStaffToBayUseCase
- GetAvailableStaffUseCase
```

### API Endpoints

```
POST   /api/v1/staff                    # Create staff member
GET    /api/v1/staff                    # List staff members
GET    /api/v1/staff/{id}               # Get staff details
PATCH  /api/v1/staff/{id}               # Update staff member
DELETE /api/v1/staff/{id}               # Deactivate staff

POST   /api/v1/staff/{id}/documents     # Upload document
GET    /api/v1/staff/{id}/documents     # List documents
DELETE /api/v1/staff/{id}/documents/{doc_id}  # Delete document
PATCH  /api/v1/staff/{id}/documents/{doc_id}/verify  # Verify document

POST   /api/v1/staff/{id}/attendance/check-in   # Check in
POST   /api/v1/staff/{id}/attendance/check-out  # Check out
GET    /api/v1/staff/{id}/attendance    # Get attendance history
POST   /api/v1/staff/attendance         # Record attendance (manager)

POST   /api/v1/staff/{id}/schedule      # Create schedule
GET    /api/v1/staff/{id}/schedule      # Get schedule
PATCH  /api/v1/staff/{id}/schedule/{schedule_id}  # Update schedule

GET    /api/v1/staff/available          # Get available staff
```

---

## Feature 2: Walk-in Service Management

### Domain Entities

```python
# app/features/walkins/domain/entities.py

class WalkInService:
    """Walk-in (non-booked) service record."""
    id: str
    service_number: str  # WI-20251002-001

    # Vehicle info (simplified - no full registration)
    vehicle_make: str
    vehicle_model: str
    vehicle_color: str
    license_plate: str
    vehicle_size: VehicleSize

    # Service details
    services: List[WalkInServiceItem]
    total_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal

    # Staff and facility
    performed_by_staff_id: str
    wash_bay_id: Optional[str]

    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_minutes: int

    # Payment
    payment_status: PaymentStatus  # pending, paid, refunded
    payment_method: PaymentMethod  # cash, card, mobile
    payment_date: Optional[datetime]

    # Customer (optional)
    customer_name: Optional[str]
    customer_phone: Optional[str]

    status: WalkInStatus  # in_progress, completed, cancelled
    notes: Optional[str]

    # Business rules
    def calculate_total(self) -> Decimal
    def apply_discount(self, discount_percent: Decimal) -> None
    def calculate_profit(self) -> Decimal  # Revenue - product costs
    def mark_as_paid(self, payment_method: PaymentMethod) -> None


class WalkInServiceItem:
    """Individual service in a walk-in."""
    service_id: str
    service_name: str
    price: Decimal
    quantity: int  # Usually 1
    subtotal: Decimal

    # Cost tracking for profit calculation
    product_costs: Decimal  # Cost of products used


class DailyWalkInReport:
    """Daily walk-in summary."""
    date: date
    total_services: int
    total_revenue: Decimal
    total_profit: Decimal
    average_service_value: Decimal
    services_by_type: Dict[str, int]
    revenue_by_payment_method: Dict[PaymentMethod, Decimal]
    services_by_staff: Dict[str, int]
```

### Key Use Cases

```python
# Walk-in Service Management
- CreateWalkInServiceUseCase
- AddServiceToWalkInUseCase
- RemoveServiceFromWalkInUseCase
- CompleteWalkInServiceUseCase
- CancelWalkInServiceUseCase
- RecordPaymentUseCase

# Reporting
- GetDailyWalkInReportUseCase
- GetWalkInHistoryUseCase
- GetStaffWalkInPerformanceUseCase
- GenerateWalkInReceiptUseCase
```

### API Endpoints

```
POST   /api/v1/walkins                  # Create walk-in service
GET    /api/v1/walkins                  # List walk-in services
GET    /api/v1/walkins/{id}             # Get walk-in details
PATCH  /api/v1/walkins/{id}             # Update walk-in
POST   /api/v1/walkins/{id}/services    # Add service
DELETE /api/v1/walkins/{id}/services/{service_id}  # Remove service
POST   /api/v1/walkins/{id}/complete    # Complete service
POST   /api/v1/walkins/{id}/payment     # Record payment
POST   /api/v1/walkins/{id}/cancel      # Cancel walk-in

GET    /api/v1/walkins/reports/daily    # Daily report
GET    /api/v1/walkins/receipt/{id}     # Generate receipt
```

---

## Feature 3: Inventory Management

### Domain Entities

```python
# app/features/inventory/domain/entities.py

class Product:
    """Inventory product/supply."""
    id: str
    sku: str
    name: str
    description: str
    category: ProductCategory  # cleaning_solution, wax, detergent, tools, supplies
    unit_of_measure: UnitOfMeasure  # liter, kg, piece, bottle

    # Stock tracking
    current_stock: Decimal
    min_stock_level: Decimal
    reorder_point: Decimal
    max_stock_level: Decimal

    # Pricing
    cost_per_unit: Decimal
    last_purchase_price: Decimal
    average_cost: Decimal  # Moving average

    # Supplier
    primary_supplier_id: Optional[str]
    supplier_sku: Optional[str]

    # Status
    is_active: bool
    is_tracked: bool  # Some items may not be tracked (e.g., water)

    created_at: datetime
    updated_at: datetime

    # Business rules
    def needs_reorder(self) -> bool
    def calculate_value(self) -> Decimal  # current_stock * average_cost


class StockMovement:
    """Stock in/out transaction."""
    id: str
    product_id: str
    movement_type: MovementType  # purchase, usage, adjustment, return, waste
    quantity: Decimal
    unit_cost: Optional[Decimal]
    total_cost: Optional[Decimal]

    # Context
    reference_type: Optional[str]  # booking, walkin, maintenance
    reference_id: Optional[str]

    # Details
    reason: str
    notes: Optional[str]
    performed_by_user_id: str

    # Balance tracking
    stock_before: Decimal
    stock_after: Decimal

    created_at: datetime


class Supplier:
    """Product supplier."""
    id: str
    name: str
    contact_person: str
    phone: str
    email: str
    address: str
    payment_terms: str
    is_active: bool

    # Performance
    total_orders: int
    total_value: Decimal
    average_delivery_days: int


class StockAlert:
    """Low stock alert."""
    id: str
    product_id: str
    alert_type: AlertType  # low_stock, out_of_stock, overstock, expiring
    severity: AlertSeverity  # info, warning, critical
    message: str
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]
```

### Key Use Cases

```python
# Product Management
- CreateProductUseCase
- UpdateProductUseCase
- GetProductUseCase
- ListProductsUseCase
- DeactivateProductUseCase

# Stock Management
- RecordStockPurchaseUseCase
- RecordStockUsageUseCase
- AdjustStockUseCase
- RecordStockWasteUseCase
- GetStockLevelsUseCase
- GetStockMovementHistoryUseCase

# Supplier Management
- CreateSupplierUseCase
- UpdateSupplierUseCase
- ListSuppliersUseCase

# Alerts & Reporting
- CheckStockAlertsUseCase
- GetLowStockProductsUseCase
- GenerateInventoryReportUseCase
- CalculateInventoryValueUseCase
```

### API Endpoints

```
POST   /api/v1/inventory/products       # Create product
GET    /api/v1/inventory/products       # List products
GET    /api/v1/inventory/products/{id}  # Get product
PATCH  /api/v1/inventory/products/{id}  # Update product
DELETE /api/v1/inventory/products/{id}  # Deactivate product

POST   /api/v1/inventory/stock/purchase # Record purchase
POST   /api/v1/inventory/stock/usage    # Record usage
POST   /api/v1/inventory/stock/adjust   # Adjust stock
GET    /api/v1/inventory/stock/movements # Stock movement history
GET    /api/v1/inventory/stock/levels   # Current stock levels

POST   /api/v1/inventory/suppliers      # Create supplier
GET    /api/v1/inventory/suppliers      # List suppliers
PATCH  /api/v1/inventory/suppliers/{id} # Update supplier

GET    /api/v1/inventory/alerts         # Get stock alerts
GET    /api/v1/inventory/low-stock      # Low stock products
GET    /api/v1/inventory/reports/valuation  # Inventory value report
```

---

## Feature 4: Expense Management

### Domain Entities

```python
# app/features/expenses/domain/entities.py

class Expense:
    """Business expense record."""
    id: str
    expense_number: str  # EXP-20251002-001

    # Basic info
    amount: Decimal
    currency: str  # USD, EUR, etc.
    category: ExpenseCategory
    subcategory: Optional[str]
    description: str

    # Date tracking
    expense_date: date  # When expense occurred
    recorded_date: date  # When recorded in system

    # Payment
    payment_method: PaymentMethod
    paid_to: str  # Vendor/payee name
    reference_number: Optional[str]  # Invoice/receipt number

    # Approval workflow
    status: ExpenseStatus  # draft, pending_approval, approved, rejected, paid
    submitted_by_user_id: str
    approved_by_user_id: Optional[str]
    approval_date: Optional[datetime]
    rejection_reason: Optional[str]

    # Attachments
    attachments: List[ExpenseAttachment]

    # Categorization
    is_recurring: bool
    recurrence_pattern: Optional[str]

    # Tax
    is_tax_deductible: bool
    tax_amount: Optional[Decimal]

    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Business rules
    def can_be_approved(self, user_role: UserRole) -> bool
    def approve(self, approved_by: str) -> None
    def reject(self, rejected_by: str, reason: str) -> None


class ExpenseCategory(Enum):
    """Expense categories."""
    UTILITIES = "utilities"  # Water, electricity
    SUPPLIES = "supplies"  # Cleaning products
    MAINTENANCE = "maintenance"  # Equipment repair
    SALARIES = "salaries"  # Staff wages
    RENT = "rent"  # Facility rent
    INSURANCE = "insurance"
    MARKETING = "marketing"
    EQUIPMENT = "equipment"  # New equipment purchase
    TAXES = "taxes"
    OTHER = "other"


class ExpenseAttachment:
    """Expense receipt/invoice attachment."""
    id: str
    expense_id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_at: datetime


class ExpenseBudget:
    """Monthly expense budget."""
    id: str
    year: int
    month: int
    category: ExpenseCategory
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    variance_percent: Decimal

    # Business rules
    def calculate_variance(self) -> Decimal
    def is_over_budget(self) -> bool
```

### Key Use Cases

```python
# Expense Management
- CreateExpenseUseCase
- UpdateExpenseUseCase
- GetExpenseUseCase
- ListExpensesUseCase
- DeleteExpenseUseCase

# Workflow
- SubmitExpenseForApprovalUseCase
- ApproveExpenseUseCase
- RejectExpenseUseCase
- MarkExpenseAsPaidUseCase

# Attachments
- UploadExpenseAttachmentUseCase
- DeleteExpenseAttachmentUseCase

# Budget Management
- CreateExpenseBudgetUseCase
- UpdateExpenseBudgetUseCase
- GetBudgetVsActualUseCase

# Reporting
- GetMonthlyExpenseReportUseCase
- GetExpensesByCategoryUseCase
- GetExpenseTrendsUseCase
```

### API Endpoints

```
POST   /api/v1/expenses                 # Create expense
GET    /api/v1/expenses                 # List expenses
GET    /api/v1/expenses/{id}            # Get expense
PATCH  /api/v1/expenses/{id}            # Update expense
DELETE /api/v1/expenses/{id}            # Delete expense

POST   /api/v1/expenses/{id}/submit     # Submit for approval
POST   /api/v1/expenses/{id}/approve    # Approve expense
POST   /api/v1/expenses/{id}/reject     # Reject expense
POST   /api/v1/expenses/{id}/pay        # Mark as paid

POST   /api/v1/expenses/{id}/attachments  # Upload attachment
DELETE /api/v1/expenses/{id}/attachments/{attachment_id}

POST   /api/v1/expenses/budgets         # Create budget
GET    /api/v1/expenses/budgets         # List budgets
GET    /api/v1/expenses/budgets/variance  # Budget vs actual

GET    /api/v1/expenses/reports/monthly # Monthly report
GET    /api/v1/expenses/reports/category # By category
GET    /api/v1/expenses/reports/trends  # Expense trends
```

---

## Feature 5: Analytics Dashboard

### Domain Entities & DTOs

```python
# app/features/analytics/domain/entities.py

class RevenueMetrics:
    """Revenue analytics."""
    period_start: date
    period_end: date

    # Revenue breakdown
    total_revenue: Decimal
    booking_revenue: Decimal
    walkin_revenue: Decimal

    # Trends
    revenue_by_day: List[DailyRevenue]
    revenue_by_service: Dict[str, Decimal]
    revenue_by_payment_method: Dict[PaymentMethod, Decimal]

    # Comparisons
    previous_period_revenue: Decimal
    revenue_growth_percent: Decimal

    # Targets
    revenue_target: Optional[Decimal]
    target_achievement_percent: Optional[Decimal]


class ServicePerformanceMetrics:
    """Service performance analytics."""
    service_id: str
    service_name: str

    # Volume
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    completion_rate: Decimal

    # Revenue
    total_revenue: Decimal
    average_price: Decimal

    # Profitability
    total_cost: Decimal
    total_profit: Decimal
    profit_margin_percent: Decimal

    # Timing
    average_duration_minutes: int


class StaffPerformanceMetrics:
    """Staff performance analytics."""
    staff_id: str
    staff_name: str

    # Productivity
    services_completed: int
    hours_worked: Decimal
    services_per_hour: Decimal

    # Revenue
    revenue_generated: Decimal
    average_service_value: Decimal

    # Quality
    average_rating: Decimal
    customer_complaints: int

    # Attendance
    days_present: int
    days_absent: int
    attendance_rate: Decimal


class CustomerAnalytics:
    """Customer behavior analytics."""
    # Acquisition
    new_customers: int
    returning_customers: int

    # Retention
    retention_rate: Decimal
    churn_rate: Decimal
    customer_lifetime_value: Decimal

    # Behavior
    average_visits_per_customer: Decimal
    average_spend_per_customer: Decimal
    most_popular_services: List[Tuple[str, int]]

    # Loyalty
    customers_by_tier: Dict[str, int]  # bronze, silver, gold


class OperationalMetrics:
    """Operational efficiency metrics."""
    # Facility utilization
    total_bays: int
    average_bay_utilization: Decimal
    peak_usage_hours: List[int]

    # Timing
    average_wait_time_minutes: int
    average_service_duration_minutes: int
    on_time_completion_rate: Decimal

    # Capacity
    total_capacity: int
    bookings_count: int
    capacity_utilization: Decimal

    # Quality
    average_customer_rating: Decimal
    complaint_rate: Decimal


class FinancialKPIs:
    """Financial key performance indicators."""
    period_start: date
    period_end: date

    # Revenue
    total_revenue: Decimal
    revenue_growth: Decimal

    # Costs
    total_expenses: Decimal
    cost_of_goods_sold: Decimal
    operating_expenses: Decimal

    # Profitability
    gross_profit: Decimal
    gross_profit_margin: Decimal
    net_profit: Decimal
    net_profit_margin: Decimal

    # Efficiency
    revenue_per_employee: Decimal
    revenue_per_bay: Decimal
    expense_to_revenue_ratio: Decimal

    # Cash flow
    cash_inflow: Decimal
    cash_outflow: Decimal
    cash_balance: Decimal
```

### Key Use Cases

```python
# Revenue Analytics
- GetRevenueMetricsUseCase
- GetRevenueTrendsUseCase
- CompareRevenuePeriodsUseCase

# Service Analytics
- GetServicePerformanceUseCase
- GetTopServicesUseCase
- GetServiceProfitabilityUseCase

# Staff Analytics
- GetStaffPerformanceUseCase
- GetTopPerformingStaffUseCase
- GetStaffProductivityReportUseCase

# Customer Analytics
- GetCustomerAnalyticsUseCase
- GetCustomerRetentionUseCase
- GetCustomerSegmentationUseCase

# Operational Analytics
- GetOperationalMetricsUseCase
- GetBayUtilizationUseCase
- GetPeakHoursAnalysisUseCase

# Financial Analytics
- GetFinancialKPIsUseCase
- GetProfitabilityAnalysisUseCase
- GetExpenseAnalysisUseCase
- GetCashFlowAnalysisUseCase

# Forecasting
- ForecastRevenueUseCase
- PredictCustomerChurnUseCase
```

### API Endpoints

```
# Revenue
GET /api/v1/analytics/revenue?start_date=2025-01-01&end_date=2025-01-31
GET /api/v1/analytics/revenue/trends?period=daily|weekly|monthly
GET /api/v1/analytics/revenue/compare?period1=...&period2=...

# Services
GET /api/v1/analytics/services/performance
GET /api/v1/analytics/services/top?limit=10
GET /api/v1/analytics/services/{id}/profitability

# Staff
GET /api/v1/analytics/staff/performance
GET /api/v1/analytics/staff/top-performers?metric=revenue|services|rating
GET /api/v1/analytics/staff/{id}/report

# Customers
GET /api/v1/analytics/customers/overview
GET /api/v1/analytics/customers/retention
GET /api/v1/analytics/customers/segmentation

# Operations
GET /api/v1/analytics/operations/overview
GET /api/v1/analytics/operations/bay-utilization
GET /api/v1/analytics/operations/peak-hours

# Financial
GET /api/v1/analytics/financial/kpis
GET /api/v1/analytics/financial/profitability
GET /api/v1/analytics/financial/expenses
GET /api/v1/analytics/financial/cashflow

# Dashboard (Combined)
GET /api/v1/analytics/dashboard/overview  # Key metrics
GET /api/v1/analytics/dashboard/manager   # Manager dashboard
GET /api/v1/analytics/dashboard/admin     # Admin dashboard
```

---

## Database Schema Design

### Staff Tables

```sql
-- Staff members
CREATE TABLE staff_members (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR REFERENCES users(id),
    employee_code VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    phone VARCHAR,
    email VARCHAR,
    hire_date DATE NOT NULL,
    employment_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    hourly_rate DECIMAL(10,2),
    assigned_bay_id VARCHAR REFERENCES wash_bays(id),
    assigned_team_id VARCHAR REFERENCES mobile_teams(id),
    skills JSONB,
    total_services_completed INT DEFAULT 0,
    total_revenue_generated DECIMAL(12,2) DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Staff documents
CREATE TABLE staff_documents (
    id VARCHAR PRIMARY KEY,
    staff_id VARCHAR REFERENCES staff_members(id),
    document_type VARCHAR(50) NOT NULL,
    document_name VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE
);

-- Attendance records
CREATE TABLE attendance_records (
    id VARCHAR PRIMARY KEY,
    staff_id VARCHAR REFERENCES staff_members(id),
    date DATE NOT NULL,
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    hours_worked DECIMAL(5,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Work schedules
CREATE TABLE work_schedules (
    id VARCHAR PRIMARY KEY,
    staff_id VARCHAR REFERENCES staff_members(id),
    day_of_week INT NOT NULL, -- 0-6
    shift_start TIME NOT NULL,
    shift_end TIME NOT NULL,
    break_duration_minutes INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    effective_from DATE NOT NULL,
    effective_until DATE
);
```

### Walk-in Tables

```sql
-- Walk-in services
CREATE TABLE walkin_services (
    id VARCHAR PRIMARY KEY,
    service_number VARCHAR UNIQUE NOT NULL,

    -- Vehicle (simplified)
    vehicle_make VARCHAR,
    vehicle_model VARCHAR,
    vehicle_color VARCHAR,
    license_plate VARCHAR,
    vehicle_size VARCHAR(20),

    -- Pricing
    total_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) NOT NULL,

    -- Staff & facility
    performed_by_staff_id VARCHAR REFERENCES staff_members(id),
    wash_bay_id VARCHAR REFERENCES wash_bays(id),

    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_minutes INT,

    -- Payment
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    payment_method VARCHAR(20),
    payment_date TIMESTAMP,

    -- Customer (optional)
    customer_name VARCHAR,
    customer_phone VARCHAR,

    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Walk-in service items
CREATE TABLE walkin_service_items (
    id VARCHAR PRIMARY KEY,
    walkin_service_id VARCHAR REFERENCES walkin_services(id),
    service_id VARCHAR REFERENCES services(id),
    service_name VARCHAR NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT DEFAULT 1,
    subtotal DECIMAL(10,2) NOT NULL,
    product_costs DECIMAL(10,2) DEFAULT 0
);
```

### Inventory Tables

```sql
-- Products
CREATE TABLE inventory_products (
    id VARCHAR PRIMARY KEY,
    sku VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,

    -- Stock
    current_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    min_stock_level DECIMAL(10,2) NOT NULL,
    reorder_point DECIMAL(10,2) NOT NULL,
    max_stock_level DECIMAL(10,2),

    -- Pricing
    cost_per_unit DECIMAL(10,2) NOT NULL,
    last_purchase_price DECIMAL(10,2),
    average_cost DECIMAL(10,2),

    -- Supplier
    primary_supplier_id VARCHAR REFERENCES suppliers(id),
    supplier_sku VARCHAR,

    is_active BOOLEAN DEFAULT TRUE,
    is_tracked BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Stock movements
CREATE TABLE stock_movements (
    id VARCHAR PRIMARY KEY,
    product_id VARCHAR REFERENCES inventory_products(id),
    movement_type VARCHAR(20) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),

    reference_type VARCHAR(50),
    reference_id VARCHAR,

    reason VARCHAR NOT NULL,
    notes TEXT,
    performed_by_user_id VARCHAR REFERENCES users(id),

    stock_before DECIMAL(10,2) NOT NULL,
    stock_after DECIMAL(10,2) NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Suppliers
CREATE TABLE suppliers (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    contact_person VARCHAR,
    phone VARCHAR,
    email VARCHAR,
    address TEXT,
    payment_terms VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,

    total_orders INT DEFAULT 0,
    total_value DECIMAL(12,2) DEFAULT 0,
    average_delivery_days INT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Stock alerts
CREATE TABLE stock_alerts (
    id VARCHAR PRIMARY KEY,
    product_id VARCHAR REFERENCES inventory_products(id),
    alert_type VARCHAR(30) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);
```

### Expense Tables

```sql
-- Expenses
CREATE TABLE expenses (
    id VARCHAR PRIMARY KEY,
    expense_number VARCHAR UNIQUE NOT NULL,

    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    description TEXT NOT NULL,

    expense_date DATE NOT NULL,
    recorded_date DATE NOT NULL,

    payment_method VARCHAR(20) NOT NULL,
    paid_to VARCHAR NOT NULL,
    reference_number VARCHAR,

    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    submitted_by_user_id VARCHAR REFERENCES users(id),
    approved_by_user_id VARCHAR REFERENCES users(id),
    approval_date TIMESTAMP,
    rejection_reason TEXT,

    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR,

    is_tax_deductible BOOLEAN DEFAULT FALSE,
    tax_amount DECIMAL(10,2),

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Expense attachments
CREATE TABLE expense_attachments (
    id VARCHAR PRIMARY KEY,
    expense_id VARCHAR REFERENCES expenses(id),
    file_name VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    file_type VARCHAR(50),
    file_size INT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Expense budgets
CREATE TABLE expense_budgets (
    id VARCHAR PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    budgeted_amount DECIMAL(10,2) NOT NULL,
    actual_amount DECIMAL(10,2) DEFAULT 0,
    variance DECIMAL(10,2),
    variance_percent DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(year, month, category)
);
```

---

## Implementation Roadmap

### Phase 1: Staff Management (Week 1-2)
**Priority**: High
**Dependencies**: Auth module (completed)

**Tasks**:
1. Domain entities & business rules (2 days)
2. Database models & migrations (1 day)
3. Repositories & use cases (3 days)
4. API endpoints & schemas (2 days)
5. Testing (2 days)

**Deliverables**:
- Staff CRUD operations
- Document management
- Basic attendance tracking
- Work schedule management

---

### Phase 2: Walk-in Service Management (Week 3)
**Priority**: High
**Dependencies**: Services module, Staff module

**Tasks**:
1. Domain entities & business rules (1 day)
2. Database models & migrations (1 day)
3. Repositories & use cases (2 days)
4. API endpoints (2 days)
5. Profit calculation logic (1 day)
6. Testing (1 day)

**Deliverables**:
- Quick walk-in service registration
- Service selection & pricing
- Payment recording
- Daily reports
- Receipt generation

---

### Phase 3: Inventory Management (Week 4-5)
**Priority**: Medium
**Dependencies**: None (standalone)

**Tasks**:
1. Domain entities & business rules (2 days)
2. Database models & migrations (1 day)
3. Product & supplier management (2 days)
4. Stock movement tracking (2 days)
5. Alert system (1 day)
6. API endpoints (2 days)
7. Testing (2 days)

**Deliverables**:
- Product/stock CRUD
- Stock movement tracking
- Low stock alerts
- Supplier management
- Inventory valuation reports

---

### Phase 4: Expense Management (Week 6)
**Priority**: Medium
**Dependencies**: Auth module

**Tasks**:
1. Domain entities & business rules (1 day)
2. Database models & migrations (1 day)
3. Expense CRUD & workflow (2 days)
4. Approval system (1 day)
5. File upload/attachment (1 day)
6. Budget tracking (1 day)
7. Testing (1 day)

**Deliverables**:
- Expense CRUD with attachments
- Approval workflow
- Budget vs actual tracking
- Monthly expense reports

---

### Phase 5: Analytics Dashboard (Week 7-8)
**Priority**: High (Business Intelligence)
**Dependencies**: All previous modules

**Tasks**:
1. Domain entities & DTOs (1 day)
2. Revenue analytics (2 days)
3. Service performance analytics (1 day)
4. Staff performance analytics (1 day)
5. Customer analytics (2 days)
6. Operational metrics (1 day)
7. Financial KPIs (2 days)
8. Dashboard endpoints (2 days)
9. Testing (2 days)

**Deliverables**:
- Comprehensive analytics endpoints
- Manager dashboard
- Admin dashboard
- Performance reports
- Trend analysis

---

### Phase 6: Integration & Polish (Week 9)
**Priority**: High
**Dependencies**: All modules

**Tasks**:
1. Cross-feature integration testing (2 days)
2. Performance optimization (1 day)
3. API documentation (1 day)
4. User acceptance testing (2 days)

---

## Total Estimated Timeline

**9 weeks (45 working days)** for complete implementation

**Breakdown**:
- Staff Management: 10 days
- Walk-in Services: 8 days
- Inventory Management: 12 days
- Expense Management: 8 days
- Analytics Dashboard: 14 days
- Integration & Testing: 5 days

---

## Technical Considerations

### File Storage
**Document & Receipt Storage**:
- Option 1: Local filesystem (simple, for MVP)
- Option 2: AWS S3 / Azure Blob Storage (scalable, production)
- Recommendation: Start with local, migrate to S3 later

**Implementation**:
```python
# app/core/storage/file_storage.py
class FileStorageService:
    async def upload_file(self, file: UploadFile, path: str) -> str
    async def delete_file(self, path: str) -> bool
    async def get_file_url(self, path: str) -> str
```

### Background Jobs
**Scheduled Tasks**:
- Daily walk-in reports (end of day)
- Stock alert checks (every hour)
- Attendance auto-checkout (end of shift)
- Monthly expense summaries (start of month)

**Implementation**: Use Celery or APScheduler
```python
# app/core/tasks/scheduled_tasks.py
@scheduler.scheduled_job('cron', hour=23, minute=0)
async def generate_daily_walkin_report():
    # Generate report for today
    pass

@scheduler.scheduled_job('cron', hour='*')
async def check_stock_alerts():
    # Check low stock levels
    pass
```

### Performance Optimization
**Analytics Queries**:
- Use database views for complex aggregations
- Implement caching for dashboard data (Redis)
- Consider materialized views for historical data

```sql
-- Example: Daily revenue view
CREATE MATERIALIZED VIEW daily_revenue_summary AS
SELECT
    DATE(created_at) as date,
    SUM(final_amount) as total_revenue,
    COUNT(*) as total_services,
    AVG(final_amount) as avg_service_value
FROM bookings
WHERE status = 'completed'
GROUP BY DATE(created_at);
```

### RBAC (Role-Based Access Control)
**Permission Matrix**:

| Feature | Admin | Manager | Washer | Customer |
|---------|-------|---------|--------|----------|
| Staff Management | Full | Full | View Self | No |
| Walk-in Services | View All | View All | Create/Update | No |
| Inventory | Full | Full | View | No |
| Expenses | Full | Full | No | No |
| Analytics | Full | Manager View | No | No |

---

## API Design Principles

### Consistent Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "meta": {
    "timestamp": "2025-10-02T10:30:00Z",
    "request_id": "req-123"
  }
}
```

### Pagination
```
GET /api/v1/staff?page=1&page_size=20&sort=-created_at
```

### Filtering
```
GET /api/v1/expenses?category=utilities&status=approved&start_date=2025-01-01
```

### Error Handling
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient stock for product XYZ",
    "details": {
      "product_id": "prod-123",
      "required": 10,
      "available": 5
    }
  }
}
```

---

## Next Steps

1. **Review & Approval**: Review this plan with stakeholders
2. **Prioritization**: Confirm priority order of features
3. **Team Assignment**: Assign developers to each feature
4. **Sprint Planning**: Break down into 2-week sprints
5. **Design Review**: Review domain models and API designs
6. **Start Implementation**: Begin with Phase 1 (Staff Management)

---

## Questions to Address

1. **File Storage**: Where should we store documents/receipts? (Local vs Cloud)
2. **Payment Gateway**: Do we need payment gateway integration for walk-ins?
3. **Reporting Format**: PDF reports needed or JSON only?
4. **Mobile App**: Will there be a mobile app accessing these APIs?
5. **Multi-Location**: Support multiple wash locations initially?
6. **Currency**: Multi-currency support needed?
7. **Barcode/QR**: Need barcode/QR scanning for products or walk-ins?

---

*Plan created: 2025-10-02*
*Ready for implementation: Pending stakeholder approval*
