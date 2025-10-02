#!/bin/bash
set -e

BASE_URL="http://localhost:8000"

echo "=== Testing Login ==="
curl -s -X POST "$BASE_URL/api/v1/auth/login" -H "Content-Type: application/json" -d @login_request.json > login_resp.json
cat login_resp.json
echo ""

TOKEN=$(cat login_resp.json | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo -e "\n=== Testing GET /api/v1/auth/me ==="
curl -s -X GET "$BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN"
echo ""

echo -e "\n=== Testing GET /api/v1/auth/users ==="
curl -s -X GET "$BASE_URL/api/v1/auth/users" -H "Authorization: Bearer $TOKEN"
echo ""

echo -e "\n=== Testing GET /api/v1/services ==="
curl -s -X GET "$BASE_URL/api/v1/services"
echo ""

echo -e "\n=== Testing GET /api/v1/vehicles ==="
curl -s -X GET "$BASE_URL/api/v1/vehicles/" -H "Authorization: Bearer $TOKEN"
echo ""

echo -e "\n=== Testing GET /api/v1/bookings ==="
curl -s -X GET "$BASE_URL/api/v1/bookings" -H "Authorization: Bearer $TOKEN"
echo ""

echo -e "\n=== All tests complete ==="
