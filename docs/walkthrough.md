# ettametta: The Autonomous Social Engine

ettametta is the world's first fully autonomous, multimodal AI engine designed for solo creators to build and scale content empires with professional-grade intuition.

## Core Pillars of the Ecosystem

### 👁️ The Visual Cortex (VLM Intuition)
ettametta doesn't just "read"—it "watches." By integrating **Vision-Language Models (Gemini 1.5 Flash)**, the engine performs keyframe analysis to intuit mood, lighting, and aesthetic quality, ensuring every creative decision is visually grounded.
- **Dynamic Grading**: Captions and filters are selected based on the visual mood of the scene.
- **Semantic Trimming**: AI-driven "hook" detection keeps only high-energy segments.

### 🕸️ Nexus V2 (Graph-Based Orchestration)
The **Nexus Pipeline** allows creators to visually compose complex content workflows.
- **Visual Graph**: Use [React Flow](file:///home/psalmprax/ettametta/apps/dashboard/src/app/nexus/page.tsx) to drag-and-drop nodes for Discovery, Synthesis, Transformation, and Publishing.
- **Blueprints**: Save and reuse successful pipeline templates to scale production instantly across different niches.

### 🦅 OpenClaw (White-Labeled Agent Network)
Every creator gets a dedicated, private AI agent.
- **Multi-Bot Manager**: Connect your own private bot via @BotFather. ettametta orchestrates concurrent bot lifecycles for every user.
- **Autonomous Control**: Command your entire engine via Telegram—trigger scans, approve videos, and monitor metrics from anywhere.

### 🎨 Generative Dreamscapes
Beyond transformation, ettametta is a **Synthesis Engine**.
- **Dual-Engine Support**: Integration with Google Veo 3 and high-performance open-source models (Wan2.2, LTX-2).
- **Scene Orchestration**: Intelligent narrative expansion for multi-scene generative videos with perfectly synced voiceovers.

---

## Technical Milestones

- **Phase 1-15**: Established the core Python/Go infrastructure and Security Sentinel.
- **Phase 16-20**: Migrated to multimodal VLM intuition and established the Visual Cortex.
- **Phase 21-25**: Launched Nexus V2 (Graph Pipelines) and Storytelling Synthesis.
- **Phase 36-41**: Expansion into WhatsApp, Persona-based content, Skool discovery, and Dashoard monetization settings.
- **Phase 42-44**: Infrastructure Hardening & Final Rebrand. Dockerized Jenkins, automated YouTube bot bypass, and standardized **ettametta** branding across UI and authentication tokens.
- **Phase 45**: Portfolio Harmonization & Remote CI/CD deployment to OCI.
- **Phase 46**: Nexus Flow UI Optimization. Enabled manual node selection and fixed cursor pointer inconsistencies for improved pipeline inspection.
- **Phase 47**: Jenkins Pipeline Resilience. Fixed Groovy syntax errors, resolved workspace context issues in post-build actions, and synchronized CI/CD parameters with new platform features.
- **Phase 48**: CI/CD Environment Hardening. Pivoted to `python3 -m pip` to resolve environment-specific command path issues in the Jenkins test runner.
- **Phase 49**: CI/CD Dependency Bootstrapping. Implemented a robust `pip` installer fallback to ensure Python tooling availability in minimal container environments.
- **Phase 50**: Jenkins venv Migration. Transitioned to Python virtual environments for CI stages to bypass PEP 668 restriction on system-wide package modification.
- **Phase 53**: Native Docker Agent Migration. Adopted Jenkins-native Docker agents for CI stages, ensuring reliable volume mounting and workspace visibility in complex containerized environments.
- **Phase 54**: LTX-2 Connectivity & CI Hardening. Restored host-side API accessibility for ngrok/LTX-2 integration and hardened post-deployment tests with virtual environment isolation.
- **Phase 55**: LTX-2 Configuration. Configured the `RENDER_NODE_URL` to route video synthesis requests to the ngrok-exposed LTX-2 render node.
- **Phase 56**: LTX-2 Memory Optimization. Implemented model CPU offloading and `bfloat16` precision to support LTX-Video on 16GB GPUs.
- **Phase 57**: LTX-2 Library Resilience. Resolved environment-specific library version conflicts by implementing source-based installation from GitHub, ensuring guaranteed support for latest generation architectures.
48: - **Phase 58**: Discovery Engine Restoration. Repaired Go scraper regex, implemented User-Agent rotation, and synchronized Python bridge with 300s timeout to resolve "NO VIRAL SIGNALS DETECTED" error. Verified real-time discovery across 8+ platforms.
- **Phase 59**: Tiered Synthesis Subscriptions. Implemented refined monetization tiers (Free, Creator, Empire, Sovereign, Studio). Enforced engine gating (e.g., `veo3` / `wan2.2` restricted to STUDIO) and daily limits (1/day Free, 5/day Creator).
- **Phase 60**: Frontend Subscription Propagation. Synchronized Next.js dashboard with refined tiers. Updated `settings/page.tsx` billing UI and `discovery/page.tsx` engine gating with "Studio Tier Req" guards.


## 🎨 Branding & Performance Resilience

ettametta is now a unified, production-hardened environment:
- **Global Rebrand**: Full migration from legacy ViralForge to **ettametta**. All UI headers and authentication token keys (`et_token`) are standardized.
- **Downloader Resiliency**: `yt-dlp` integration is optimized with broad format fallbacks to support YouTube Shorts and authenticated cookie synchronization for bot bypass.
- **Dockerized Jenkins**: No more manual setup; all CI/CD logic is containerized for portability.
- **JCasC (Configuration as Code)**: Credentials and system settings are managed via YAML for secret-safe, repeatable deployments.
- **Optimized Networking**: Stale Docker bridges and duplicate networks have been pruned for seamless service-to-service communication.

## 🏆 Portfolio Harmonization & CI/CD
Viral Forge is now part of a harmonized software portfolio, co-existing with the National Security Platform on shared OCI infrastructure.

### Resource Isolation
- **Port Harmony**: Viral Forge occupies the primary `3000` (Web) and `6379` (Redis) ports, with NSP resources shifted to higher ranges to prevent collisions.
- **Automated Delivery**: A new `Jenkinsfile.remote` enables one-click deployment and automated data seeding, ensuring that the Visual Intelligence engine is always backed by a fresh, verified database state.

### Jenkins Pipeline Setup (Critical)
To resolve the "Identity file not accessible" error, the pipeline now uses Jenkins **Credentials**:
1. Go to **Manage Jenkins** > **Credentials**.
2. Click **(global)** > **Add Credentials**.
3. **Kind**: SSH Username with private key.
4. **ID**: `OCI_SSH_KEY` (MUST match the ID in the Jenkinsfile).
5. **Username**: `ubuntu`
6. **Private Key**: Paste the content of your `.pem` file.

---
**Viral Forge // Harmonization & CI/CD Complete**
**Efficient. Automated. Sovereign.**

For a deep dive into the engineering, see the [**Architecture Design**](file:///home/psalmprax/ettametta/docs/architecture_design.md) or the [**Competitive Landscape**](file:///home/psalmprax/ettametta/docs/competitive_landscape.md).
