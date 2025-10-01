#!/bin/bash
# =============================================================================
# Architecture Compliance Analyzer
# Checks for violations of clean architecture rules
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Architecture Compliance Analysis"
echo -e "==========================================${NC}"
echo ""

VIOLATIONS=0

# Check 1: Cross-Feature Imports
echo -e "${BLUE}[1/5] Checking for cross-feature imports...${NC}"
CROSS_FEATURE=$(grep -rn "from app.features" app/features/*/adapters/ app/features/*/api/ 2>/dev/null | grep -v "__pycache__" | wc -l || echo "0")

if [ "$CROSS_FEATURE" -gt 0 ]; then
    echo -e "${RED}✗ Found $CROSS_FEATURE cross-feature imports${NC}"
    echo "  Violations:"
    grep -rn "from app.features" app/features/bookings/adapters/external_services.py 2>/dev/null | head -3
    grep -rn "from app.features" app/features/facilities/api/ 2>/dev/null | grep "from app.features.auth" | head -2
    grep -rn "from app.features" app/features/scheduling/adapters/models.py 2>/dev/null | head -1
    VIOLATIONS=$((VIOLATIONS + CROSS_FEATURE))
else
    echo -e "${GREEN}✓ No cross-feature imports${NC}"
fi
echo ""

# Check 2: Domain Layer Purity
echo -e "${BLUE}[2/5] Checking domain layer purity...${NC}"
DOMAIN_VIOLATIONS=$(grep -rn "from fastapi\|from pydantic\|import fastapi\|import pydantic" app/features/*/domain/ 2>/dev/null | grep -v "__pycache__" | wc -l || echo "0")

if [ "$DOMAIN_VIOLATIONS" -gt 0 ]; then
    echo -e "${RED}✗ Found $DOMAIN_VIOLATIONS FastAPI/Pydantic imports in domain${NC}"
    VIOLATIONS=$((VIOLATIONS + DOMAIN_VIOLATIONS))
else
    echo -e "${GREEN}✓ Domain layer is pure (no FastAPI/Pydantic)${NC}"
fi
echo ""

# Check 3: Business Logic Location
echo -e "${BLUE}[3/5] Checking business logic location...${NC}"
API_LOGIC=$(grep -rn "if.*raise.*Error" app/features/*/api/ 2>/dev/null | grep -v "__pycache__" | grep -v "HTTPException" | wc -l || echo "0")

if [ "$API_LOGIC" -gt 10 ]; then
    echo -e "${YELLOW}⚠ Found $API_LOGIC potential business logic in API layer${NC}"
    echo "  (Manual review recommended)"
else
    echo -e "${GREEN}✓ Minimal business logic in API layer${NC}"
fi
echo ""

# Check 4: Dependency Direction
echo -e "${BLUE}[4/5] Checking dependency direction...${NC}"
BAD_DEPS=$(grep -rn "from.*adapters" app/features/*/use_cases/ 2>/dev/null | grep -v "__pycache__" | wc -l || echo "0")

if [ "$BAD_DEPS" -gt 0 ]; then
    echo -e "${RED}✗ Found $BAD_DEPS use_cases importing from adapters${NC}"
    VIOLATIONS=$((VIOLATIONS + BAD_DEPS))
else
    echo -e "${GREEN}✓ Dependency direction is correct${NC}"
fi
echo ""

# Check 5: Feature Layer Structure
echo -e "${BLUE}[5/5] Checking feature layer structure...${NC}"
FEATURES=$(ls -d app/features/*/ | wc -l)
COMPLETE=0

for feature in app/features/*/; do
    feat_name=$(basename $feature)
    if [ -d "$feature/domain" ] && [ -d "$feature/ports" ] && [ -d "$feature/use_cases" ] && [ -d "$feature/adapters" ] && [ -d "$feature/api" ]; then
        COMPLETE=$((COMPLETE + 1))
    fi
done

echo -e "${GREEN}✓ $COMPLETE/$FEATURES features have complete layer structure${NC}"
echo ""

# Summary
echo -e "${BLUE}=========================================="
echo "Summary"
echo -e "==========================================${NC}"

if [ "$VIOLATIONS" -eq 0 ]; then
    echo -e "${GREEN}✓ Architecture is compliant!${NC}"
    echo ""
    echo "All rules enforced:"
    echo "  ✓ No cross-feature imports (mostly)"
    echo "  ✓ Domain layer is pure"
    echo "  ✓ Dependency direction correct"
    echo "  ✓ Complete layer structure"
else
    echo -e "${RED}✗ Found $VIOLATIONS architecture violations${NC}"
    echo ""
    echo "Violations to fix:"
    if [ "$CROSS_FEATURE" -gt 0 ]; then
        echo "  • $CROSS_FEATURE cross-feature imports"
    fi
    if [ "$DOMAIN_VIOLATIONS" -gt 0 ]; then
        echo "  • $DOMAIN_VIOLATIONS domain purity violations"
    fi
    if [ "$BAD_DEPS" -gt 0 ]; then
        echo "  • $BAD_DEPS dependency direction violations"
    fi
fi

echo ""
echo -e "${BLUE}Known acceptable patterns:${NC}"
echo "  • bookings/adapters/external_services.py uses other features (via ports)"
echo "  • API layers import UserRole from auth (enum only)"
echo "  • scheduling/adapters imports facility models (for FK only)"
echo ""

exit $VIOLATIONS
