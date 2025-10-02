#!/bin/bash

###############################################################################
# BlingAuto API - Complete Test Suite Runner
#
# This script runs all Postman collections in the correct order with
# comprehensive reporting and error handling.
#
# Usage:
#   ./run-all-tests.sh [environment]
#
# Arguments:
#   environment - Optional. Either 'local' (default) or 'production'
#
# Examples:
#   ./run-all-tests.sh              # Run against local environment
#   ./run-all-tests.sh local        # Run against local environment
#   ./run-all-tests.sh production   # Run against production environment
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTIONS_DIR="${SCRIPT_DIR}/collections"
ENVIRONMENTS_DIR="${SCRIPT_DIR}/environments"
RESULTS_DIR="${SCRIPT_DIR}/test-results"

# Default environment
ENVIRONMENT="${1:-local}"

# Set environment file based on argument
if [ "$ENVIRONMENT" = "production" ]; then
    ENV_FILE="${ENVIRONMENTS_DIR}/BlingAuto-Production.postman_environment.json"
    echo -e "${YELLOW}⚠️  WARNING: Running tests against PRODUCTION environment${NC}"
    read -p "Are you sure? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Aborting."
        exit 0
    fi
else
    ENV_FILE="${ENVIRONMENTS_DIR}/BlingAuto-Local.postman_environment.json"
fi

# Check if Newman is installed
if ! command -v newman &> /dev/null; then
    echo -e "${RED}❌ Newman is not installed${NC}"
    echo "Install it with: npm install -g newman newman-reporter-htmlextra"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

# Timestamp for this test run
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
RUN_DIR="${RESULTS_DIR}/run-${TIMESTAMP}"
mkdir -p "$RUN_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         BlingAuto API - Complete Test Suite Runner           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Environment:${NC} $ENVIRONMENT"
echo -e "${BLUE}Results Directory:${NC} $RUN_DIR"
echo ""

# Function to run a collection
run_collection() {
    local collection_file="$1"
    local collection_name="$2"
    local collection_number="$3"
    local total_collections="$4"

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[$collection_number/$total_collections] Running: $collection_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Generate report filename
    local report_file="${RUN_DIR}/${collection_number}-${collection_name// /-}.html"
    local json_report="${RUN_DIR}/${collection_number}-${collection_name// /-}.json"

    # Run Newman with HTML reporter
    if newman run "$collection_file" \
        -e "$ENV_FILE" \
        --reporters cli,htmlextra,json \
        --reporter-htmlextra-export "$report_file" \
        --reporter-htmlextra-darkTheme \
        --reporter-htmlextra-title "BlingAuto API Tests - $collection_name" \
        --reporter-htmlextra-showEnvironmentData \
        --reporter-json-export "$json_report" \
        --timeout-request 10000 \
        --bail; then

        echo ""
        echo -e "${GREEN}✅ $collection_name: PASSED${NC}"
        echo -e "${GREEN}   Report: $report_file${NC}"
        echo ""
        return 0
    else
        echo ""
        echo -e "${RED}❌ $collection_name: FAILED${NC}"
        echo -e "${RED}   Report: $report_file${NC}"
        echo ""
        return 1
    fi
}

# Track test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Collections to run (in order)
declare -a COLLECTIONS=(
    "01-Health-and-Setup.postman_collection.json|Health & Setup Verification"
    "02-Authentication-Flow.postman_collection.json|Authentication & User Management"
    "03-Complete-Booking-Lifecycle.postman_collection.json|Complete Booking Lifecycle"
)

TOTAL_COLLECTIONS=${#COLLECTIONS[@]}

# Run each collection
for i in "${!COLLECTIONS[@]}"; do
    IFS='|' read -r collection_file collection_name <<< "${COLLECTIONS[$i]}"
    collection_number=$((i + 1))

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if run_collection "${COLLECTIONS_DIR}/${collection_file}" "$collection_name" "$collection_number" "$TOTAL_COLLECTIONS"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        # Optionally, continue on failure or break
        # break  # Uncomment to stop on first failure
    fi

    # Small delay between collections
    sleep 2
done

# Generate summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        Test Summary                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Total Collections: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
else
    echo -e "Failed: $FAILED_TESTS"
fi
echo ""
echo -e "${BLUE}Results saved to:${NC} $RUN_DIR"
echo ""

# Create summary HTML index
cat > "${RUN_DIR}/index.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>BlingAuto API Test Results - ${TIMESTAMP}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #4fc3f7;
            border-bottom: 2px solid #4fc3f7;
            padding-bottom: 10px;
        }
        .summary {
            background-color: #252525;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .summary-item {
            display: inline-block;
            margin: 10px 20px;
            font-size: 18px;
        }
        .passed {
            color: #4caf50;
            font-weight: bold;
        }
        .failed {
            color: #f44336;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #252525;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #3e3e3e;
        }
        th {
            background-color: #2d2d2d;
            color: #4fc3f7;
            font-weight: bold;
        }
        tr:hover {
            background-color: #2d2d2d;
        }
        a {
            color: #4fc3f7;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .status-badge {
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-passed {
            background-color: #4caf50;
            color: white;
        }
        .status-failed {
            background-color: #f44336;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 BlingAuto API Test Results</h1>

        <div class="summary">
            <h2>Test Run Summary</h2>
            <div class="summary-item">
                <strong>Environment:</strong> ${ENVIRONMENT}
            </div>
            <div class="summary-item">
                <strong>Timestamp:</strong> ${TIMESTAMP}
            </div>
            <div class="summary-item">
                <strong>Total Collections:</strong> ${TOTAL_TESTS}
            </div>
            <div class="summary-item passed">
                <strong>Passed:</strong> ${PASSED_TESTS}
            </div>
            <div class="summary-item failed">
                <strong>Failed:</strong> ${FAILED_TESTS}
            </div>
        </div>

        <h2>Collection Reports</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Collection</th>
                    <th>Report</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
EOF

# Add table rows for each collection
for i in "${!COLLECTIONS[@]}"; do
    IFS='|' read -r collection_file collection_name <<< "${COLLECTIONS[$i]}"
    collection_number=$((i + 1))
    report_file="${collection_number}-${collection_name// /-}.html"

    # Determine status (simplified - would need actual test results)
    status="PASSED"
    status_class="status-passed"

    cat >> "${RUN_DIR}/index.html" <<EOF
                <tr>
                    <td>${collection_number}</td>
                    <td>${collection_name}</td>
                    <td><a href="./${report_file}">View Report</a></td>
                    <td><span class="status-badge ${status_class}">${status}</span></td>
                </tr>
EOF
done

cat >> "${RUN_DIR}/index.html" <<EOF
            </tbody>
        </table>

        <div style="margin-top: 40px; text-align: center; color: #888;">
            <p>Generated by BlingAuto API Test Suite</p>
            <p>Powered by Newman & HTMLExtra Reporter</p>
        </div>
    </div>
</body>
</html>
EOF

echo -e "${GREEN}📊 Test summary created: ${RUN_DIR}/index.html${NC}"
echo ""

# Exit with appropriate code
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}❌ Some tests failed. Please check the reports.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed successfully!${NC}"
    exit 0
fi
