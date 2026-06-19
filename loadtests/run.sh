#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BASE_URL="${BASE_URL:-http://localhost:8000}"
SCENARIO="${1:-all}"
DOCKER_IMAGE="grafana/k6:latest"

echo "=== ettametta Load Tests ==="
echo "Target: $BASE_URL"
echo "Scenario: $SCENARIO"
echo ""

build_scenarios() {
  local scenarios=()

  for file in "$SCRIPT_DIR/scenarios/"*.js; do
    if [ -f "$file" ]; then
      local name
      name=$(basename "$file" .js)

      if [ "$SCENARIO" = "all" ] || [ "$SCENARIO" = "$name" ]; then
        scenarios+=("$file")
      fi
    fi
  done

  echo "${scenarios[@]}"
}

run_single() {
  local scenario_file="$1"
  local scenario_name
  scenario_name=$(basename "$scenario_file" .js)

  echo "--- Running: $scenario_name ---"

  docker run --rm \
    -v "$SCRIPT_DIR/scenarios:/scripts" \
    -e BASE_URL="$BASE_URL" \
    "$DOCKER_IMAGE" \
    run --out json=- \
    "/scripts/${scenario_name}.js" 2>&1 | tail -20

  echo ""
}

if [ "$SCENARIO" = "all" ]; then
  echo "Running all scenarios sequentially..."
  for file in "$SCRIPT_DIR/scenarios/"*.js; do
    if [ -f "$file" ]; then
      run_single "$file"
    fi
  done
elif [ "$SCENARIO" = "parallel" ]; then
  echo "Running all scenarios in parallel..."
  for file in "$SCRIPT_DIR/scenarios/"*.js; do
    if [ -f "$file" ]; then
      run_single "$file" &
    fi
  done
  wait
  echo "All parallel scenarios completed."
else
  scenario_file="$SCRIPT_DIR/scenarios/${SCENARIO}.js"
  if [ ! -f "$scenario_file" ]; then
    echo "Error: Scenario '${SCENARIO}' not found in scenarios/"
    echo "Available scenarios:"
    ls "$SCRIPT_DIR/scenarios/"*.js 2>/dev/null | xargs -I {} basename {} .js
    exit 1
  fi
  run_single "$scenario_file"
fi

echo "=== Load Tests Complete ==="
