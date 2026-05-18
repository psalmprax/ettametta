#!/bin/bash
#
# Remote E2E Test Runner
# =====================
# This script runs E2E tests on a remote server via SSH
#
# Usage: ./run_remote_e2e.sh [options]
# Options:
#   --scenario N     Run specific scenario (1-10), or 'all' for all scenarios
#   --browser BROWSER Run on specific browser (chromium, firefox, webkit)
#   --headed         Run in headed mode (visible browser)
#   --debug          Run with Playwright debug mode
#   --port PORT      Port for the dashboard (default: 7202)
#
# Default: Run all scenarios on chromium in headless mode

set -e

# Configuration - Non-GPU server (dashboard)
NON_GPU_HOST="root@149.104.110.122"
NON_GPU_PORT="7200"

# Configuration - GPU server (for video processing if needed)
GPU_HOST="root@175.155.64.174"
GPU_PORT="19461"

SSH_KEY="/home/psalmprax/Music/id_rsa"
SSH_OPTS="-o StrictHostKeyChecking=no -o PasswordAuthentication=no -o UserKnownHostsFile=/dev/null"
E2E_DIR="/home/psalmprax/ALL_PROJECTS/ettametta/src/tests/e2e"
REMOTE_E2E_DIR="/tmp/viral-forge-e2e"
REMOTE_BASE_URL="${REMOTE_BASE_URL:-http://149.104.110.122:7200}"

# Parse arguments
SCENARIO="all"
BROWSER="chromium"
HEADED=false
DEBUG=false
PORT="7200"

while [[ $# -gt 0 ]]; do
    case $1 in
        --scenario)
            SCENARIO="$2"
            shift 2
            ;;
        --browser)
            BROWSER="$2"
            shift 2
            ;;
        --headed)
            HEADED=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Use provided port or default
REMOTE_BASE_URL="http://149.104.110.122:$PORT"

echo "=========================================="
echo "Viral Forge - Remote E2E Test Runner"
echo "=========================================="
echo "Remote Host: $NON_GPU_HOST"
echo "Port: $PORT"
echo "Base URL: $REMOTE_BASE_URL"
echo "Scenario: $SCENARIO"
echo "Browser: $BROWSER"
echo "=========================================="

# Map scenarios to test files (Updated for consolidated structure)
declare -A SCENARIO_FILES=(
    ["1"]="auth_flow.spec.ts"
    ["2"]="discovery_flow.spec.ts"
    ["3"]="payment_flow.spec.ts"
    ["4"]="publishing_flow.spec.ts"
    ["5"]="visual_regression.spec.ts"
    ["6"]="accessibility.spec.ts"
    ["7"]="stack_switching.spec.ts"
    ["8"]="agent_skills_e2e.spec.ts"
    ["9"]="real_first_hardening.spec.ts"
)

# Build test file list
if [ "$SCENARIO" = "all" ]; then
    TEST_FILES=""
    for key in "${!SCENARIO_FILES[@]}"; do
        TEST_FILES="$TEST_FILES ${SCENARIO_FILES[$key]}"
    done
else
    TEST_FILES="${SCENARIO_FILES[$SCENARIO]}"
fi

# SSH command function
ssh_cmd() {
    ssh $SSH_OPTS -i "$SSH_KEY" "$NON_GPU_HOST" "$@"
}

# Sync e2e directory to remote
echo ""
echo "Step 1: Syncing E2E tests to remote server..."
rsync -az --delete -e "ssh $SSH_OPTS -i $SSH_KEY" \
    "$E2E_DIR/" \
    "$NON_GPU_HOST:$REMOTE_E2E_DIR/"

# Install dependencies on remote
echo ""
echo "Step 2: Installing dependencies on remote..."
ssh_cmd "cd $REMOTE_E2E_DIR && npm install && npx playwright install --with-deps"

# Run tests
echo ""
echo "Step 3: Running E2E tests..."

# Build playwright command
PLAYWRIGHT_CMD="SKIP_WEB_SERVER=1 BASE_URL=$REMOTE_BASE_URL npx playwright test"

# Add specific test files
if [ "$SCENARIO" != "all" ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD tests/${SCENARIO_FILES[$SCENARIO]}"
else
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD tests/"
fi

# Add browser project
if [ "$BROWSER" != "all" ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --project=$BROWSER"
fi

# Add headed mode
if [ "$HEADED" = true ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --headed"
fi

# Add debug mode
if [ "$DEBUG" = true ]; then
    PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --debug"
fi

# Run the tests
ssh_cmd "cd $REMOTE_E2E_DIR && $PLAYWRIGHT_CMD"

echo ""
echo "=========================================="
echo "E2E Tests Complete!"
echo "=========================================="