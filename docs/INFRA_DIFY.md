# Dify Infrastructure Integration Walkthrough

This document summarizes the production-grade hardening performed to integrate the Dify AI orchestration stack into the Ettametta infrastructure.

## 1. Network Architecture
Dify is integrated into the `ettametta` Docker network, enabling secure, low-latency inter-service communication.

| Service | Internal URL | Purpose |
|---------|--------------|---------|
| **Dify API** | `http://ettametta-dify-api:5001` | Backend processing and orchestration. |
| **Dify Web** | `http://ettametta-dify-web:3000` | Frontend console interface. |
| **Ollama** | `http://ettametta-ollama:11434` | Local LLM provider for Dify. |

## 2. Nginx Proxy & CORS Hardening
To support the Dify Console through the central Ettametta proxy, the following Nginx configurations were implemented in `infra/docker/nginx.conf`:

### Centralized CORS Management
- **Dynamic Origin**: Instead of a wildcard `*`, Nginx now returns the specific `$http_origin` of the request.
- **Credential Support**: Added `Access-Control-Allow-Credentials: true` to allow Dify to handle login sessions through the proxy.
- **Preflight Handling**: Nginx intercepts `OPTIONS` requests directly at the proxy level to ensure consistent cross-origin handshakes.
- **Header Stripping**: Used `proxy_set_header Origin ""` and `proxy_hide_header` to prevent Dify from injecting conflicting CORS headers.

## 3. Security & Encryption
### Secret Key Stability
To prevent encryption mismatches during environment updates, a dedicated secret key was established:
- **Variable**: `DIFY_INNER_SECRET_KEY`
- **Mapping**: Mapped to `SECRET_KEY` inside Dify containers in `docker-compose.dify.yml`.

### Troubleshooting: "Private Key Not Found" (500 Error)
If Dify returns a 500 error related to RSA keys after a secret key change, the internal encryption pair must be reset:
```bash
docker exec -it ettametta-dify-api flask reset-encrypt-key-pair
```

## 4. Dify Application Setup (Manual)
Once the infrastructure is deployed:
1. Access Dify at `http://[IP]:8081`.
2. Create an Admin account.
3. Create a **Chat App** named "Nexus Orchestrator".
4. Generate an **API Key** from the "API Access" tab and add it to `.env` as `DIFY_API_KEY`.

## 5. Connecting Ollama
In the Dify "Model Provider" settings, add Ollama with the following:
- **Base URL**: `http://ettametta-ollama:11434` (Internal network name)
- **Model**: `llama3.2:3b` (Pre-pulled on the server)
