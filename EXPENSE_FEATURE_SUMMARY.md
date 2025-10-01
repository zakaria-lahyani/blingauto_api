# Expense Management Feature - Summary

## Status: Domain Layer Complete (25%)

**Date**: October 2, 2025
**Progress**: Domain layer implemented, remaining layers follow established pattern

---

## What's Been Implemented (Domain Layer)

### ✅ Enums (4 enums)
- **ExpenseCategory**: SUPPLIES, UTILITIES, MAINTENANCE, SALARIES, RENT, EQUIPMENT, MARKETING, INSURANCE, TAXES, FUEL, OTHER
- **ExpenseStatus**: PENDING, APPROVED, REJECTED, PAID, CANCELLED
- **PaymentMethod**: CASH, BANK_TRANSFER, CHECK, CREDIT_CARD, DEBIT_CARD, MOBILE_MONEY
- **RecurrenceType**: ONE_TIME, DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY

### ✅ Entities (3 entities)
- **Expense**: Main expense record with approval workflow
  - Methods: `approve()`, `reject()`, `mark_as_paid()`, `cancel()`, `is_overdue()`
- **Budget**: Monthly budget per category
  - Methods: `get_remaining_amount()`, `get_spent_percentage()`, `is_over_budget()`, `should_alert()`, `add_expense()`, `remove_expense()`
- **ExpenseSummary**: Monthly summary data structure

### ✅ Policies (2 policy classes)
- **ExpenseManagementPolicy**: Expense number generation, amount validation, approval requirements
  - Auto-approve <= $100
  - Manager approval up to $1,000
  - Admin approval > $1,000
- **BudgetManagementPolicy**: Budget validation, alert thresholds, budget recommendations

---

## Remaining Implementation (75%)

Following the exact same clean architecture pattern as Staff, Walk-in, and Inventory features:

### Ports Layer (Planned)
- **IExpenseRepository** (10+ methods)
- **IBudgetRepository** (6+ methods)

### Use Cases Layer (Planned - 14 use cases)
**Expense**:
1. CreateExpense
2. UpdateExpense
3. GetExpense
4. ListExpenses
5. ApproveExpense
6. RejectExpense
7. MarkAsPaid
8. CancelExpense

**Budget**:
9. CreateBudget
10. UpdateBudget
11. GetBudget
12. ListBudgets
13. DeleteBudget

**Reports**:
14. GetMonthlySummary

### Adapters Layer (Planned)
- **models.py**: 2 SQLAlchemy models (ExpenseModel, BudgetModel)
- **repositories.py**: 2 repository implementations

### API Layer (Planned - 12+ endpoints)
- **schemas.py**: 15+ Pydantic DTOs
- **router.py**: 12+ REST endpoints with RBAC
- **dependencies.py**: 14+ DI factories

### Database Migration (Planned)
- **007_add_expense_tables.py**: 2 tables with 12+ indexes

---

## Key Features

### Expense Workflow
1. **Create** → PENDING status
2. **Approve/Reject** → Manager/Admin reviews
3. **Mark as Paid** → Only if approved
4. **Track** → Full audit trail

### Budget Tracking
- Monthly budgets per category
- Automatic spent amount tracking
- Alert when 80% spent (configurable)
- Over-budget detection

### Business Rules
- Auto-approve expenses <= $100
- Manager can approve up to $1,000
- Admin approval required > $1,000
- Cannot pay unapproved expenses
- Cannot cancel paid expenses

### Auto-Generated Numbers
Format: **EXP-20251002-001**, **EXP-20251002-002**, etc.

---

## API Endpoints (Planned)

### Expense Endpoints (8)
1. `POST /expenses` - Create expense
2. `GET /expenses` - List with filters
3. `GET /expenses/{id}` - Get expense
4. `PUT /expenses/{id}` - Update expense
5. `POST /expenses/{id}/approve` - Approve
6. `POST /expenses/{id}/reject` - Reject
7. `POST /expenses/{id}/mark-paid` - Mark as paid
8. `DELETE /expenses/{id}` - Cancel expense

### Budget Endpoints (5)
9. `POST /budgets` - Create budget
10. `GET /budgets` - List budgets
11. `GET /budgets/{id}` - Get budget
12. `PUT /budgets/{id}` - Update budget
13. `DELETE /budgets/{id}` - Delete budget

### Report Endpoints (1)
14. `GET /expenses/reports/monthly/{month}` - Monthly summary by category

---

## RBAC (Planned)

| Endpoint | Admin | Manager | Washer | Customer |
|----------|-------|---------|--------|----------|
| Create Expense | ✅ | ✅ | ✅ | ❌ |
| View Expenses | ✅ | ✅ | Own only | ❌ |
| Update Expense | ✅ | ✅ | Own (if pending) | ❌ |
| Approve (≤$1K) | ✅ | ✅ | ❌ | ❌ |
| Approve (>$1K) | ✅ | ❌ | ❌ | ❌ |
| Reject | ✅ | ✅ | ❌ | ❌ |
| Mark as Paid | ✅ | ✅ | ❌ | ❌ |
| Manage Budgets | ✅ | ✅ | ❌ | ❌ |
| View Reports | ✅ | ✅ | ❌ | ❌ |

---

## Database Schema (Planned)

```sql
CREATE TABLE expenses (
    id VARCHAR PRIMARY KEY,
    expense_number VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    payment_method VARCHAR(30),
    expense_date DATE NOT NULL,
    due_date DATE,
    paid_date DATE,
    created_by_id VARCHAR NOT NULL,
    approved_by_id VARCHAR,
    paid_by_id VARCHAR,
    vendor_name VARCHAR(200),
    vendor_id VARCHAR,
    receipt_url VARCHAR(500),
    notes TEXT,
    approval_notes TEXT,
    rejection_reason TEXT,
    recurrence_type VARCHAR(20) DEFAULT 'ONE_TIME',
    parent_expense_id VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE budgets (
    id VARCHAR PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    month DATE NOT NULL,
    budgeted_amount NUMERIC(10,2) NOT NULL,
    spent_amount NUMERIC(10,2) DEFAULT 0.00,
    alert_threshold_percent NUMERIC(5,2) DEFAULT 80.00,
    created_by_id VARCHAR NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, month)
);
```

---

## Estimated Completion

- **Domain Layer**: ✅ Complete (~600 lines)
- **Ports Layer**: ⏳ ~100 lines
- **Use Cases**: ⏳ ~1,400 lines
- **Adapters**: ⏳ ~700 lines
- **API**: ⏳ ~900 lines
- **Migration**: ⏳ ~200 lines

**Total Estimated**: ~3,900 lines across 24 files
**Time to Complete**: 2-3 hours

---

## Next Steps

1. Implement ports layer (repository interfaces)
2. Implement 14 use cases
3. Implement adapters (models, repositories)
4. Implement API layer (schemas, router, dependencies)
5. Create database migration
6. Register router in main app
7. Testing and documentation

---

## Pattern Consistency

This feature follows **100% identical architecture** to:
- ✅ Staff Management
- ✅ Walk-in Services
- ✅ Inventory Management

All layers use the same clean architecture principles, async/await patterns, RBAC enforcement, and soft delete strategies.

---

*Summary Generated: October 2, 2025*
*Domain Layer: Complete*
*Remaining: Ports, Use Cases, Adapters, API, Migration*
