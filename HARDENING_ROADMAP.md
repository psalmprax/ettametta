# Ettametta (AlphaHecta) Enterprise Hardening Roadmap

This document outlines the strategic plan to transition Ettametta from a local-first development environment to an enterprise-grade, high-availability platform.

## 1. Architectural & High Availability (HA)
**Goal**: Decouple core services to eliminate single points of failure and database contention.

### 1.1 Database Decoupling & Event Sourcing
- [ ] **Infrastructure isolation**: Separate Go (Gateway) and Python (ML/Engine) database access patterns.
- [ ] **Message Bus Integration**: Introduce Redis Streams or RabbitMQ as the primary communication channel between Go and Python services.
- [ ] **State Synchronization**: Implement an event-driven state machine to handle Video Job lifecycles without direct cross-service DB writes.

### 1.2 Hybrid Inference Scaling
- [ ] **Inference Load Balancing**: Implement a dynamic router that shifts loads between local Ollama (for low-cost reasoning) and cloud providers (for high-throughput bursts).
- [ ] **GPU Auto-Scaling**: Integrate with remote GPU clusters (e.g., Lambda Labs, Modal) for overflow processing during resource saturation.

## 2. Core Technical Excellence
**Goal**: Eliminate high-severity technical debt and implement unified observability.

### 2.1 Zero-Crash Hardening
- [ ] **Nil-Pointer Audit**: Comprehensive audit of Go auth handlers and registry patterns to prevent nil-pointer dereferences.
- [ ] **Recursion & Stack Protection**: Refactor `AuthContext` and deep-nested React components to use non-recursive state management.
- [ ] **Input Sanitization**: Hardened validation for all cross-service payloads (Pydantic <-> Go Structs).

### 2.2 Unified Observability
- [ ] **Request-ID Tracing**: Implement a global `X-Request-ID` propagated through the entire stack (Dashboard -> Go -> Python -> Celery).
- [ ] **Structured Logging**: Transition all service logs to JSON format for ingestion by Loki/Grafana.
- [ ] **OpenTelemetry (OTEL)**: Standardize on OTEL for performance monitoring and bottleneck detection.

## 3. Intelligence Hub Resilience
**Goal**: Ensure LLM reliability and cost governance.

### 3.1 Unified LLM Proxy
- [ ] **Provider Abstraction**: Create a unified interface for Azure, Anthropic, Google, and OpenAI.
- [ ] **Dynamic Failover**: Automated switching between providers based on real-time latency and error rates.
- [ ] **Circuit Breakers**: Implement Hystrix-style circuit breakers for every external AI vendor.

### 3.2 Cost-Aware Routing
- [ ] **Token Economy Service**: Track token usage per user/organization.
- [ ] **Economic Optimization**: Automatically route "simple" queries to low-cost models (e.g., Flash, 8B) while reserving "complex" reasoning for Hermes 3 or GPT-4.

## 4. Enterprise Compliance & Governance
**Goal**: Automate compliance with global AI regulations.

### 4.1 EU AI Act Automation
- [ ] **Incident Webhooks**: Implement Article 71 compliant incident reporting for automated logging of "high-risk" AI failures.
- [ ] **Evidence Collection**: Automated collection of metadata, model versions, and training/fine-tuning datasets for compliance audits.

## 5. Premium UI/UX Resilience
**Goal**: Professional-grade interface stability and aesthetics.

### 5.1 Resilient Frontend
- [ ] **Global Error Boundaries**: Implement granular error boundaries to prevent full-page crashes.
- [ ] **Sandbox Mode**: Graceful degradation to a "Read-Only/Local" mode if the backend service is unreachable.

### 5.2 Premium Component Refactor
- [ ] **Dialog Modernization**: Replace all browser-native `confirm()` and `alert()` calls with custom Framer-Motion based overlays.
- [ ] **Micro-Interaction Polish**: Implement high-fidelity loading states and transitions for all long-running AI operations.
