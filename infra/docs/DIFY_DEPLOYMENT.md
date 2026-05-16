# Dify Deployment Guide (Ettametta Infrastructure)

This document outlines the deployment and configuration of the Dify AI orchestration stack within the Ettametta production environment.

## 1. Architecture Overview

Dify is deployed as a sidecar stack using `docker-compose.dify.yml`. It shares the core database and Redis infrastructure with the main application but operates on a dedicated external network for isolation and routing.

- **Frontend**: `ettametta-dify-web` (Port 8081)
- **API Server**: `ettametta-dify-api` (Port 5001 internal)
- **Worker**: `ettametta-dify-worker`
- **Reverse Proxy**: Integrated via the main Nginx gateway (Port 7200)

## 2. Networking Configuration

Dify services are connected to an external network named `ettametta_ettametta`. 

### Required Network Links
The following core services **MUST** be connected to the `ettametta_ettametta` network to enable communication:
1. `ettametta-nginx-1` (Routing)
2. `ettametta-db-1` (Data Persistence)
3. `ettametta-redis-1` (Task Queue & Cache)

**Command to verify/connect:**
```bash
docker network connect ettametta_ettametta ettametta-nginx-1
docker network connect ettametta_ettametta ettametta-db-1
docker network connect ettametta_ettametta ettametta-redis-1
```

## 3. Nginx Reverse Proxy Configuration

To allow the Dify frontend to reach its backend via the main domain/port, the following block was added to `/infra/docker/nginx.conf`:

```nginx
location /api/v1/dify/ {
    set $dify_api_upstream ettametta-dify-api;
    rewrite ^/api/v1/dify/(.*) /$1 break;
    proxy_pass http://$dify_api_upstream:5001;
    
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
}
```

## 4. Database Setup

Dify requires a dedicated database named `dify` within the Postgres cluster.

**Creation Steps:**
1. Connect to the DB container:
   ```bash
   docker exec ettametta-db-1 psql -U psalmprax -d ettametta -c "CREATE DATABASE dify;"
   ```
2. Run migrations manually if auto-migration fails:
   ```bash
   docker exec ettametta-dify-api flask db upgrade
   ```

## 5. Environment Variables

Key variables in `docker-compose.dify.yml` must use explicit container names for internal resolution:
- `DB_HOST=ettametta-db-1`
- `REDIS_HOST=ettametta-redis-1`
- `CONSOLE_API_URL=http://<ip_or_domain>:7200/api/v1/dify`

## 6. Access Information

- **URL**: `http://149.104.110.122:8081`
- **Default Setup**: Accessible via the initial setup wizard on the first visit.
