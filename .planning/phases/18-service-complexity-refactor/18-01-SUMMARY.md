---
phase: 18-service-complexity-refactor
plan: 01
title: "Service complexity refactor — 5 files, 7 tasks"
status: complete
depends_on: []
created: 2026-06-19
completed: 2026-06-19
gsd_version: 1.1
---

# Phase 18-01 — Summary

## What Shipped

Refactored 5 service files to reduce complexity, eliminate duplication, and improve maintainability. Total: -147 lines (-4%), 5→8 focused classes, 20+ duplicated patterns eliminated.

## Task Results

### T1+T2: Extract video utils ✅ (already done)
- `video_utils.py` already contained `VideoInfo`, `probe_video`, `run_ffmpeg_cmd`
- `processor.py` already imports both at line 25
- No changes needed

### T3: Add resolve_input to DAG base node ✅
- Enhanced `BaseNode.resolve_input()` with `type_` and `default` kwargs
- Updated 5 node classes: StockSearchNode, SemanticSearchNode, ParallelAssetSourceNode, VisionAuditNode, SceneRenderNode
- Eliminated manual `str(self.params.get(...))` / `int(...)` / `bool(...)` casts

### T4+T5: Break NexusOrchestrator god class ✅
- Extracted `VibeAnalyzer` — Dify/LangChain queries + vision audit
- Extracted `AssetManager` — clip sourcing, validation, fill, audio stitching, transcription
- Extracted `RenderPipeline` — Remotion render with circuit breaker, SRT export, thumbnail
- `NexusOrchestrator` now a coordinator delegating to three sub-components
- `assemble_video` split into `_phase_ingress()`, `_phase_cognition()`, `_phase_synthesis()`, `_phase_egress()`
- Synthesis phase unified under `_node_phase()` context manager, eliminating ~12 lines of duplicated status logic
- orchestrator.py: 946 → 878 lines (-68, -7%)

### T6: Fix empire_service.py ✅
- Converted legacy `db.query()` to modern `select()`/`db.scalars()`/`db.scalar()` style
- Added try/except to `get_winning_blueprints` fallback query
- Hoisted model imports to module level
- Added `GATEWAY_HOST` to settings.py as single source of truth
- Fixed `ABTestDB.winner_variant is not None` to `.isnot(None)` (SQLAlchemy correctness)
- empire_service.py: 474 → 405 lines (-69, -15%)

### T7: Extract platform_composer patterns ✅
- Enhanced `_circuit_breaker_call()` with `default` parameter
- Enhanced `_gather_with_exceptions()` with optional `extract` callback
- Replaced manual circuit breaker pattern in `_search_platform`
- Replaced inline asyncio.gather + filter in `_download_pending`
- platform_composer.py: 402 → 392 lines (-10, -2%)

## Files Modified
- `src/services/nexus_engine/orchestrator.py` (-68 lines)
- `src/services/nexus_engine/dag_nodes.py` (resolve_input enhanced)
- `src/services/nexus_engine/platform_composer.py` (-10 lines)
- `src/services/monetization/empire_service.py` (-69 lines)
- `src/services/video_engine/dag_executor.py` (resolve_input enhanced)
- `src/api/config/settings.py` (GATEWAY_HOST added)

## Impact
- 3485 → 3338 total lines (-147, -4%)
- 5 god classes → 8 focused classes
- All files pass AST syntax check
- All existing tests continue to pass
