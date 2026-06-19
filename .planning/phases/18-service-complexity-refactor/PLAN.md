# Phase 18: Service Complexity Refactor

## Objective
Refactor 5 service files to reduce complexity, eliminate duplication, and improve maintainability.

## Scope
1. `src/services/nexus_engine/orchestrator.py` (1154 lines) — needs work
2. `src/services/video_engine/processor.py` (1052 lines) — needs work
3. `src/services/nexus_engine/dag_nodes.py` (698 lines) — mediocre
4. `src/services/monetization/empire_service.py` (458 lines) — mediocre
5. `src/services/nexus_engine/platform_composer.py` (392 lines) — clean

## Tasks

### T1: Extract shared `probe_video()` helper
**File:** `src/services/video_engine/utils.py` (new)
- Create `probe_video(path) -> VideoInfo` dataclass
- Returns width, height, fps, frame_count, codec, has_audio
- Eliminates 5x OpenCV probe duplication in processor.py

### T2: Extract shared `run_ffmpeg_cmd()` async helper
**File:** `src/services/video_engine/utils.py`
- Create `async run_ffmpeg_cmd(cmd: list[str], timeout: int = 300) -> bytes`
- Handles subprocess creation, wait, returncode check, logging
- Eliminates 2x FFmpeg subprocess duplication in processor.py

### T3: Add `resolve_input()` to DAG base node
**File:** `src/services/nexus_engine/dag_nodes.py`
- Add method to `BaseNode` class
- Encapsulates: params → inputs → ctx → type-check pattern
- Update 5 nodes to use shared method

### T4: Break `NexusOrchestrator` god class
**File:** `src/services/nexus_engine/` (new files)
- Extract `VibeAnalyzer` — Dify/LangChain queries
- Extract `AssetManager` — clip sourcing, validation, fill
- Extract `RenderPipeline` — Remotion render, SRT export, thumbnail
- Keep `Orchestrator` as coordinator

### T5: Refactor `assemble_video` into phases
**File:** `src/services/nexus_engine/orchestrator.py`
- Split 371-line method into: `_phase_ingress()`, `_phase_cognition()`, `_phase_synthesis()`, `_phase_egress()`
- Create `node_phase()` context manager for status updates
- Eliminates 14x `_update_node_status` calls

### T6: Fix `empire_service.py` issues
**File:** `src/services/monetization/empire_service.py`
- Replace hardcoded IP `149.104.110.122` with config
- Add try/except to `get_activity_stream` query blocks
- Add try/except to `get_winning_blueprints`
- Convert legacy `query()` to `select()` style

### T7: Extract `platform_composer.py` patterns
**File:** `src/services/nexus_engine/platform_composer.py`
- Create `_circuit_breaker_call()` wrapper
- Create `_gather_with_exceptions()` helper
- Eliminates 3x + 4x pattern duplication

## Verification
- [ ] All existing tests pass
- [ ] `tsc --noEmit` passes (if TS changes)
- [ ] No new type errors
- [ ] Line counts reduced by ~30% total
- [ ] No duplicated patterns >2x

## Dependencies
- None (standalone refactoring phase)

## Estimated Impact
- ~2000 lines reduced across 5 files
- 5 god classes → 8 focused classes
- 20+ duplicated patterns eliminated
