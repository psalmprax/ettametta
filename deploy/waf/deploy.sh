#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Deploying Nginx WAF..."

# Create required directories
mkdir -p /tmp/nginx-waf/{ssl,logs}

# Check for SSL certificates
if [ ! -f /tmp/nginx-waf/ssl/cert.pem ] || [ ! -f /tmp/nginx-waf/ssl/key.pem ]; then
  echo "==> Generating self-signed certificates for development..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /tmp/nginx-waf/ssl/key.pem \
    -out /tmp/nginx-waf/ssl/cert.pem \
    -subj "/CN=localhost/O=ettametta/C=US" 2>/dev/null
fi

# Stop existing nginx if running
docker stop nginx-waf 2>/dev/null || true
docker rm nginx-waf 2>/dev/null || true

# Pull image
docker pull nginx:alpine

# Run WAF container
docker run -d \
  --name nginx-waf \
  --network ettametta_default \
  --restart unless-stopped \
  -p 80:80 \
  -p 443:443 \
  -v "${SCRIPT_DIR}/nginx-waf.conf:/etc/nginx/nginx.conf:ro" \
  -v "${SCRIPT_DIR}/owasp-crs.conf:/etc/nginx/modsecurity/owasp-crs.conf:ro" \
  -v "${SCRIPT_DIR}/modsecurity.conf:/etc/nginx/modsecurity/modsecurity.conf:ro" \
  -v /tmp/nginx-waf/ssl:/etc/nginx/ssl:ro \
  -v /tmp/nginx-waf/logs:/var/log/nginx \
  nginx:alpine

echo "==> WAF deployed successfully"
echo "==> Testing configuration..."
docker exec nginx-waf nginx -t

echo "==> Done. WAF is running on ports 80/443"
