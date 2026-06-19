#!/usr/bin/env bash
set -euo pipefail

CONSUL_ADDR="${CONSUL_ADDR:-http://localhost:8500}"

echo "==> Registering ettametta services with Consul..."

register_service() {
  local name=$1
  local port=$2
  local tags=$3
  local check_http=${4:-""}
  local check_interval=${5:-"10s"}

  local payload="{
    \"Service\": {
      \"Name\": \"${name}\",
      \"Port\": ${port},
      \"Tags\": [\"${tags}\"],
      \"Meta\": {
        \"version\": \"${APP_VERSION:-1.0.0}\",
        \"env\": \"${APP_ENV:-production}\"
      }"

  if [ -n "$check_http" ]; then
    payload="${payload},
      \"Check\": {
        \"HTTP\": \"${check_http}\",
        \"Interval\": \"${check_interval}\",
        \"Timeout\": \"3s\",
        \"DeregisterCriticalServiceAfter\": \"30s\"
      }"
  fi

  payload="${payload}
    }
  }"

  curl -s -X PUT "${CONSUL_ADDR}/v1/agent/service/register" \
    -H "Content-Type: application/json" \
    -d "$payload"

  echo "  ✓ Registered: ${name} on port ${port}"
}

register_check() {
  local name=$1
  local http=$2
  local interval=${3:-"10s"}

  curl -s -X PUT "${CONSUL_ADDR}/v1/agent/check/register" \
    -H "Content-Type: application/json" \
    -d "{
      \"ID\": \"${name}-check\",
      \"Name\": \"${name} Health\",
      \"HTTP\": \"${http}\",
      \"Interval\": \"${interval}\",
      \"Timeout\": \"3s\",
      \"DeregisterCriticalServiceAfter\": \"30s\"
    }"

  echo "  ✓ Health check: ${name}"
}

# Register ettametta services
register_service "ettametta-api" 8000 "api,http" "http://api:8000/health" "10s"
register_service "ettametta-celery-worker" 0 "celery,worker"
register_service "ettametta-redis" 6379 "redis,cache" "http://redis:6379" "15s"
register_service "ettametta-discovery" 8001 "discovery,http" "http://discovery:8001/health" "10s"
register_service "ettametta-ai-gateway" 8002 "ai-gateway,http" "http://ai-gateway:8002/health" "10s"
register_service "ettametta-postgres" 5432 "database,postgres"
register_service "ettametta-remotion" 3000 "remotion,renderer" "http://remotion:3000/health" "15s"

# Register health checks separately
register_check "ettametta-api" "http://api:8000/health" "10s"
register_check "ettametta-redis" "http://redis:6379" "15s"
register_check "ettametta-celery" "http://celery:5555/api/health" "20s"

echo ""
echo "==> All services registered"
echo "==> View at: ${CONSUL_ADDR}/ui"

# List registered services
curl -s "${CONSUL_ADDR}/v1/catalog/services" | python3 -m json.tool 2>/dev/null || \
  curl -s "${CONSUL_ADDR}/v1/catalog/services"
