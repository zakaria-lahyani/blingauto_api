#!/bin/bash

# Test all API endpoints for 500 errors
BASE_URL="http://localhost:8000"
TOKEN=""

echo "========================================="
echo "API Endpoint Testing Suite"
echo "========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local method=$1
    local path=$2
    local data=$3
    local auth=$4
    local description=$5

    echo -n "Testing $method $path ... "

    headers="-H 'Content-Type: application/json'"
    if [ "$auth" = "true" ] && [ -n "$TOKEN" ]; then
        headers="$headers -H 'Authorization: Bearer $TOKEN'"
    fi

    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$path" -H "Content-Type: application/json" ${auth:+-H "Authorization: Bearer $TOKEN"} -d "$data" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$path" -H "Content-Type: application/json" ${auth:+-H "Authorization: Bearer $TOKEN"} 2>&1)
    fi

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" -ge 500 ]; then
        echo -e "${RED}FAIL${NC} - Status: $status_code"
        echo "  Error: $body" | head -c 200
        echo ""
        return 1
    elif [ "$status_code" -ge 400 ]; then
        echo -e "${YELLOW}EXPECTED ERROR${NC} - Status: $status_code"
        return 0
    else
        echo -e "${GREEN}OK${NC} - Status: $status_code"
        return 0
    fi
}

# 1. Test Health Endpoints (No Auth)
echo "=== Health Endpoints ==="
test_endpoint "GET" "/health/health" "" "false" "Health check"
test_endpoint "GET" "/health/ready" "" "false" "Ready check"
echo ""

# 2. Login and get token
echo "=== Authentication ==="
echo -n "Logging in... "
login_response=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d @login_request.json)

TOKEN=$(echo $login_response | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  Token: ${TOKEN:0:50}..."
else
    echo -e "${RED}FAILED${NC}"
    echo "  Response: $login_response"
    exit 1
fi
echo ""

# 3. Test Auth Endpoints
echo "=== Auth Endpoints ==="
test_endpoint "GET" "/api/v1/auth/me" "" "true" "Get current user"
test_endpoint "GET" "/api/v1/auth/profile" "" "true" "Get user profile"
test_endpoint "GET" "/api/v1/auth/users" "" "true" "List users (admin)"
echo ""

# 4. Test Services Endpoints
echo "=== Services Endpoints ==="
test_endpoint "GET" "/api/v1/services" "" "false" "List services"
test_endpoint "GET" "/api/v1/services/categories" "" "false" "List categories"
test_endpoint "GET" "/api/v1/services/popular" "" "false" "Popular services"
echo ""

# 5. Test Vehicles Endpoints
echo "=== Vehicles Endpoints ==="
test_endpoint "GET" "/api/v1/vehicles/" "" "true" "List vehicles"
echo ""

# 6. Test Bookings Endpoints
echo "=== Bookings Endpoints ==="
test_endpoint "GET" "/api/v1/bookings" "" "true" "List bookings"
echo ""

# 7. Test Pricing Endpoints
echo "=== Pricing Endpoints ==="
test_endpoint "GET" "/api/v1/pricing/quote" "" "false" "Get pricing quote"
echo ""

# 8. Test Facilities Endpoints
echo "=== Facilities Endpoints ==="
test_endpoint "GET" "/api/v1/facilities/wash-bays/" "" "false" "List wash bays"
test_endpoint "GET" "/api/v1/facilities/mobile-teams/" "" "false" "List mobile teams"
echo ""

echo "========================================="
echo "Testing Complete"
echo "========================================="
