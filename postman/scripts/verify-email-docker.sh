#!/bin/bash

# BlingAuto Email Verification Helper Script
# This script helps verify user emails by getting the token from the database
# and calling the verification API endpoint

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
DB_CONTAINER="${DB_CONTAINER:-blingauto_api-db-1}"

# Function to display usage
usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 <email>"
    echo ""
    echo -e "${BLUE}Example:${NC}"
    echo "  $0 verifytest123456@example.com"
    echo ""
    echo -e "${BLUE}Environment Variables:${NC}"
    echo "  API_URL      - API base URL (default: http://localhost:8000)"
    echo "  DB_CONTAINER - Database container name (default: blingauto_api-db-1)"
    echo ""
    exit 1
}

# Check if email parameter is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Email address required${NC}"
    echo ""
    usage
fi

EMAIL="$1"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   BlingAuto Email Verification Helper     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Get verification token from database
echo -e "${YELLOW}→ Step 1: Retrieving verification token from database...${NC}"
echo -e "  Email: ${EMAIL}"

TOKEN=$(docker exec -i "$DB_CONTAINER" psql -U postgres -d blingauto -t -A -c \
    "SELECT token FROM email_verification_tokens
     WHERE email = '$EMAIL'
       AND is_used = FALSE
       AND expires_at > NOW()
     ORDER BY created_at DESC
     LIMIT 1;")

# Check if token was found
if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ No valid verification token found${NC}"
    echo ""
    echo -e "${YELLOW}Possible reasons:${NC}"
    echo "  - User hasn't registered yet"
    echo "  - Token has already been used"
    echo "  - Token has expired (24 hour expiration)"
    echo "  - Email address is incorrect"
    echo ""

    # Show token information if any exists
    echo -e "${YELLOW}→ Checking for any tokens for this email...${NC}"
    docker exec -i "$DB_CONTAINER" psql -U postgres -d blingauto -c \
        "SELECT token, created_at, expires_at, is_used, used_at
         FROM email_verification_tokens
         WHERE email = '$EMAIL'
         ORDER BY created_at DESC
         LIMIT 3;"

    exit 1
fi

echo -e "${GREEN}✓ Token found${NC}"
echo -e "  Token: ${TOKEN:0:20}...${TOKEN: -10}"
echo ""

# Step 2: Verify email using the API
echo -e "${YELLOW}→ Step 2: Calling verification API...${NC}"
echo -e "  URL: ${API_URL}/api/v1/auth/verify-email"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/auth/verify-email" \
    -H "Content-Type: application/json" \
    -d "{\"token\": \"$TOKEN\"}")

# Extract status code (last line) and body (everything else)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""

# Check response
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Email verified successfully!${NC}"
    echo ""
    echo -e "${GREEN}Response:${NC}"
    echo "$BODY" | jq -r '.message' 2>/dev/null || echo "$BODY"
    echo ""

    # Verify in database
    echo -e "${YELLOW}→ Step 3: Verifying database status...${NC}"
    docker exec -i "$DB_CONTAINER" psql -U postgres -d blingauto -c \
        "SELECT email, is_email_verified, email_verified_at
         FROM users
         WHERE email = '$EMAIL';"

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Verification Complete! ✓            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"

else
    echo -e "${RED}✗ Verification failed (HTTP $HTTP_CODE)${NC}"
    echo ""
    echo -e "${RED}Response:${NC}"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    exit 1
fi
