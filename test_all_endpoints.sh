#!/bin/bash

# Test all API endpoints systematically
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzMWY5NzliYS03NDlmLTQwZGItOGVhMS1mMzMxOWVkZjJkZjYiLCJyb2xlIjoiYWRtaW4iLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5NDg5MDQ1LCJpYXQiOjE3NTk0ODcyNDV9.7xz4JVZDk54JPVaHV_cPKNPRtXxwTzRQunBIfgaofOo"
BASE_URL="http://localhost:8000/api/v1"

test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}

    echo -n "Testing $name... "
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TOKEN" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method -H "Authorization: Bearer $TOKEN" "$url")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [[ $http_code -eq 200 ]] || [[ $http_code -eq 307 ]]; then
        echo "✓ OK ($http_code)"
        return 0
    else
        echo "✗ FAILED ($http_code)"
        if echo "$body" | grep -q "error"; then
            echo "$body" | grep -o '"message":"[^"]*"'
        fi
        return 1
    fi
}

echo "========================================="
echo "BlingAuto API - Endpoint Testing"
echo "========================================="
echo ""

# Health
echo "=== Health ==="
test_endpoint "Health Check" "http://localhost:8000/health"
echo ""

# Auth
echo "=== Authentication ==="
test_endpoint "Get Profile" "$BASE_URL/auth/me"
test_endpoint "List Users" "$BASE_URL/auth/users?limit=1"
echo ""

# Vehicles
echo "=== Vehicles ==="
test_endpoint "List Vehicles" "$BASE_URL/vehicles?limit=1"
echo ""

# Services
echo "=== Services ==="
test_endpoint "List Categories" "$BASE_URL/services/categories"
test_endpoint "List Services" "$BASE_URL/services?limit=1"
echo ""

# Bookings
echo "=== Bookings ==="
test_endpoint "List Bookings" "$BASE_URL/bookings?limit=1"
echo ""

# Staff
echo "=== Staff ==="
test_endpoint "List Staff" "$BASE_URL/staff?limit=1"
echo ""

# Scheduling
echo "=== Scheduling ==="
test_endpoint "List Resources" "$BASE_URL/scheduling/resources"
echo ""

# Facilities - Wash Bays
echo "=== Facilities - Wash Bays ==="
test_endpoint "List Wash Bays" "$BASE_URL/facilities/wash-bays?limit=1"
echo ""

# Facilities - Mobile Teams
echo "=== Facilities - Mobile Teams ==="
test_endpoint "List Mobile Teams" "$BASE_URL/facilities/mobile-teams?limit=1"
echo ""

# Walk-ins
echo "=== Walk-ins ==="
test_endpoint "List Walk-ins" "$BASE_URL/walkins?limit=1"
echo ""

# Inventory
echo "=== Inventory ==="
test_endpoint "List Products" "$BASE_URL/inventory/products?limit=1"
test_endpoint "List Suppliers" "$BASE_URL/inventory/suppliers?limit=1"
test_endpoint "List Stock Movements" "$BASE_URL/inventory/stock-movements?limit=1"
echo ""

# Expenses
echo "=== Expenses ==="
test_endpoint "List Expenses" "$BASE_URL/expenses?limit=1"
test_endpoint "List Budgets" "$BASE_URL/expenses/budgets?limit=1"
echo ""

# Analytics
echo "=== Analytics ==="
test_endpoint "Get Dashboard" "$BASE_URL/analytics/dashboard?start_date=2025-01-01&end_date=2025-10-03"
test_endpoint "Revenue Metrics" "$BASE_URL/analytics/revenue/metrics?start_date=2025-01-01&end_date=2025-10-03"
test_endpoint "Daily Revenue" "$BASE_URL/analytics/revenue/daily?start_date=2025-10-01&end_date=2025-10-03"
echo ""

echo "========================================="
echo "Testing Complete"
echo "========================================="
