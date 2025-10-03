#!/bin/bash

# BlingAuto API - Master Test Runner
# Runs all Postman collections with Newman and generates HTML reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
COLLECTIONS_DIR="$SCRIPT_DIR/collections"
ENV_FILE="$SCRIPT_DIR/environments/BlingAuto-Local.postman_environment.json"
REPORTS_DIR="$SCRIPT_DIR/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo -e "${RED}Error: Newman is not installed${NC}"
    echo "Install with: npm install -g newman newman-reporter-htmlextra"
    exit 1
fi

# Create reports directory
mkdir -p "$REPORTS_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   BlingAuto API - Test Suite Runner       ║${NC}"
echo -e "${BLUE}║   Logical Workflow Order (Data Flow)       ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

# Check if API is running
echo -e "${YELLOW}→ Checking API health...${NC}"
if ! curl -s -f http://localhost:8000/health > /dev/null; then
    echo -e "${RED}✗ API is not running on http://localhost:8000${NC}"
    echo "Start with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ API is healthy${NC}"
echo ""

# Counter for test results
TOTAL_COLLECTIONS=0
PASSED_COLLECTIONS=0
FAILED_COLLECTIONS=0

# Function to run a collection
run_collection() {
    local collection_file=$1
    local collection_name=$(basename "$collection_file" .postman_collection.json)
    local report_file="$REPORTS_DIR/${collection_name}_${TIMESTAMP}.html"

    TOTAL_COLLECTIONS=$((TOTAL_COLLECTIONS + 1))

    echo -e "${BLUE}══════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Running: ${collection_name}${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════${NC}"

    if newman run "$collection_file" \
        -e "$ENV_FILE" \
        --reporters cli,htmlextra \
        --reporter-htmlextra-export "$report_file" \
        --reporter-htmlextra-title "BlingAuto API Tests - $collection_name" \
        --reporter-htmlextra-logs \
        --color on; then

        echo -e "${GREEN}✓ $collection_name - PASSED${NC}"
        PASSED_COLLECTIONS=$((PASSED_COLLECTIONS + 1))
        return 0
    else
        echo -e "${RED}✗ $collection_name - FAILED${NC}"
        FAILED_COLLECTIONS=$((FAILED_COLLECTIONS + 1))
        return 1
    fi
}

# Run all collections in order
echo -e "${YELLOW}→ Starting test execution...${NC}"
echo ""

# List of collections to run (in logical workflow order)
collections=(
    # Phase 1: Configuration & Authentication (Foundation)
    "00-Master-Configuration.postman_collection.json"
    "02-Complete-Authentication-Profile.postman_collection.json"

    # Phase 2: Core Data Setup (Prerequisites)
    "03-Services-Categories.postman_collection.json"
    "11-Facilities-Management.postman_collection.json"
    "04-Staff-Management.postman_collection.json"

    # Phase 3: Operations (Business Workflows)
    "01-Walkins-Complete-Flow.postman_collection.json"
    "06-Bookings-Management.postman_collection.json"
    "09-Scheduling-Resources.postman_collection.json"

    # Phase 4: Supporting Systems (Financial & Inventory)
    "08-Expenses-Budgets.postman_collection.json"
    "05-Inventory-Management.postman_collection.json"

    # Phase 5: Analytics & Validation (Verification)
    "07-Analytics-Reports.postman_collection.json"
    "10-Data-Validation-Security.postman_collection.json"
)

for collection in "${collections[@]}"; do
    collection_path="$COLLECTIONS_DIR/$collection"

    if [ -f "$collection_path" ]; then
        run_collection "$collection_path"
        echo ""
    else
        echo -e "${YELLOW}⚠ Skipping: $collection (file not found)${NC}"
        echo ""
    fi
done

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Test Execution Summary            ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""
echo -e "Total Collections:  ${BLUE}$TOTAL_COLLECTIONS${NC}"
echo -e "Passed:             ${GREEN}$PASSED_COLLECTIONS${NC}"
echo -e "Failed:             ${RED}$FAILED_COLLECTIONS${NC}"
echo ""
echo -e "${YELLOW}Reports saved to: $REPORTS_DIR${NC}"
echo ""

# Open summary report if all passed
if [ $FAILED_COLLECTIONS -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     ✓ All Tests Passed Successfully!      ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"

    # Generate summary HTML
    SUMMARY_FILE="$REPORTS_DIR/test-summary_${TIMESTAMP}.html"
    cat > "$SUMMARY_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>BlingAuto API Test Summary</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .header { background: #4CAF50; color: white; padding: 20px; border-radius: 5px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: white; padding: 20px; border-radius: 5px; flex: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 36px; font-weight: bold; color: #4CAF50; }
        .reports { background: white; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .report-link { display: block; padding: 10px; margin: 5px 0; background: #2196F3; color: white; text-decoration: none; border-radius: 3px; }
        .report-link:hover { background: #0b7dda; }
    </style>
</head>
<body>
    <div class="header">
        <h1>✓ BlingAuto API Test Suite</h1>
        <p>All tests passed successfully - $(date)</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">$TOTAL_COLLECTIONS</div>
            <div>Collections Run</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">$PASSED_COLLECTIONS</div>
            <div>Passed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: #f44336;">$FAILED_COLLECTIONS</div>
            <div>Failed</div>
        </div>
    </div>

    <div class="reports">
        <h2>Test Reports</h2>
EOF

    for collection in "${collections[@]}"; do
        collection_name=$(basename "$collection" .postman_collection.json)
        report_file="${collection_name}_${TIMESTAMP}.html"
        if [ -f "$REPORTS_DIR/$report_file" ]; then
            echo "        <a href=\"$report_file\" class=\"report-link\">📊 $collection_name Report</a>" >> "$SUMMARY_FILE"
        fi
    done

    cat >> "$SUMMARY_FILE" << EOF
    </div>
</body>
</html>
EOF

    echo -e "${YELLOW}Summary report: file://$SUMMARY_FILE${NC}"

    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║     ✗ Some Tests Failed - Check Reports   ║${NC}"
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    exit 1
fi
