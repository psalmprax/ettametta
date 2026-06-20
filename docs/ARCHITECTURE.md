# Architecture

This repository implements a content generation and automation platform featuring an AI-driven creation pipeline, an administrative dashboard, and a backend API. The system integrates autonomous agents, A/B testing for content optimization, and a credit-based usage system, supported by a PostgreSQL database managed via Alembic migrations.

### Main Modules & Responsibilities

*   **`apps/dashboard`**: A Next.js frontend providing the primary user interface.
    *   **Creation Pipeline**: Interfaces for script generation (`ScriptEnginePanel`), visual asset creation (`VisualCorePanel`), and voice synthesis (`VoiceForgePanel`).
    *   **Analytics & Optimization**: Tools for A/B testing (`ab-testing/page.tsx`), intelligence/reasoning (`intelligence/page.tsx`), and general performance metrics (`analytics/page.tsx`).
    *   **Management**: Administrative panels for security audits, bias scanning, credit tracking, and autonomous agent controls.
    *   **Video Editing**: A specialized interface for script generation and render committing (`video-editor/page.tsx`).
*   **`apps/remotion-studio`**: A dedicated service for programmatic video composition and rendering.
*   **`src/api`**: The backend REST API providing the core business logic.
    *   **Routing**: Dedicated endpoints for discovery, publishing, and general API configuration.
    *   **Task Orchestration**: Integration with Celery for asynchronous job processing and a custom scheduler for timed tasks.
    *   **Middleware**: Request handling and authentication layers.
*   **`alembic`**: Database schema versioning and migration management, handling the evolution of tables for users, affiliate links, revenue logs, and credit systems.
*   **`scripts`**: Utility scripts for environment synchronization, credential checking, and codebase maintenance.