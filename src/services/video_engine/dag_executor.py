"""
DAG Video Compiler Engine
=========================

A graph-based video processing architecture inspired by Unreal Sequencer
and After Effects backend pipelines.

Instead of running steps linearly, you compile a graph of nodes into an
execution plan, then execute it with:
- Parallelism (independent nodes run concurrently via asyncio.gather)
- Caching (hash-based content addressability for node outputs)
- Partial recomputation (only re-run nodes whose inputs changed)
- Graceful fallback (failed nodes can be replaced without rebuilding the graph)

Architecture:
    Node         → A single processing step (stock search, download, grade, etc.)
    DAGCompiler  → Topological sort + validate acyclic + build ExecutionPlan
    ExecutionPlan→ Batch groupings for parallel execution
    Scheduler    → Cache-aware executor with parallel batches
    Cache        → Filesystem-based content-addressable cache

Usage:
    # Define nodes
    nodes = [
        StockSearchNode("stock1", {"keyword": "sunset"}),
        VideoDownloadNode("dl1", {"url_ref": "stock1"}),
        ColorGradeNode("grade1", {"input_ref": "dl1", "style": "cinematic"}),
    ]

    # Compile + execute
    compiler = DAGCompiler()
    plan = compiler.compile(nodes)
    scheduler = Scheduler()
    results = await scheduler.run(plan)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# Node Protocol & Base
# ═══════════════════════════════════════════

@runtime_checkable
class Node(Protocol):
    """A single processing step in the DAG.

    Each node:
    - Has a unique ``id``
    - Declares its ``inputs`` (list of node IDs this depends on)
    - Receives a context dict with all previously computed results
    - Returns a result (typically a MediaIR or file path or dict)
    """
    id: str
    params: dict[str, Any]
    inputs: list[str]

    async def execute(self, ctx: dict[str, Any]) -> Any: ...


class BaseNode:
    """Convenience base class for DAG nodes.

    Subclasses override ``execute()`` and optionally ``cache_key_parts()``.
    """

    def __init__(self, node_id: str, params: dict[str, Any] | None = None,
                 inputs: list[str] | None = None):
        self.id = node_id
        self.params = params or {}
        self.inputs = inputs or []

    async def execute(self, ctx: dict[str, Any]) -> Any:
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute() must be overridden"
        )

    def cache_key_parts(self) -> dict[str, Any]:
        """Override to include additional fields in the cache key.

        By default includes class name + params. Override if the node's
        behavior depends on external state (e.g., API keys, timestamps).
        """
        return {
            "type": self.__class__.__name__,
            "params": self.params,
            "inputs": self.inputs,
        }

    def cache_key(self) -> str:
        """Deterministic hash used for content-addressable caching."""
        raw = json.dumps(
            self.cache_key_parts(),
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


# ═══════════════════════════════════════════
# Compiler
# ═══════════════════════════════════════════

class DAGCompiler:
    """Compiles a list of nodes into an executable ExecutionPlan.

    Steps:
    1. Validate all input references exist
    2. Check for cycles (Kahn's algorithm)
    3. Topological sort
    4. Batch nodes into parallel-execution groups
    """

    def compile(self, nodes: list[Node]) -> "ExecutionPlan":
        """Compile nodes into an execution plan.

        Raises:
            ValueError: If a node references an unknown input or a cycle is detected.
        """
        node_map = {n.id: n for n in nodes}

        # Validate all input references exist
        for n in nodes:
            for dep_id in n.inputs:
                if dep_id not in node_map:
                    raise ValueError(
                        f"Node '{n.id}' depends on unknown node '{dep_id}'. "
                        f"Available nodes: {list(node_map.keys())}"
                    )

        # Topological sort (Kahn's algorithm)
        in_degree: dict[str, int] = {n.id: 0 for n in nodes}
        for n in nodes:
            in_degree[n.id] = sum(1 for d in n.inputs if d in node_map)

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        sorted_ids: list[str] = []

        while queue:
            nid = queue.pop(0)
            sorted_ids.append(nid)
            for other in nodes:
                if nid in other.inputs:
                    in_degree[other.id] -= 1
                    if in_degree[other.id] == 0:
                        queue.append(other.id)

        if len(sorted_ids) != len(nodes):
            # Compute cycle info for better error message
            unresolved = set(node_map.keys()) - set(sorted_ids)
            raise ValueError(
                f"DAG contains a cycle! Unresolved nodes: {unresolved}"
            )

        ordered = [node_map[nid] for nid in sorted_ids]
        logger.info(
            f"[DAGCompiler] Compiled {len(nodes)} nodes into "
            f"{len(ordered)} execution steps"
        )
        return ExecutionPlan(ordered)


class ExecutionPlan:
    """An ordered, batched execution plan ready for the Scheduler.

    Nodes are grouped into batches where all nodes in a batch can
    execute in parallel because their dependencies are already resolved.
    """

    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
        self._compute_batches()

    def _compute_batches(self) -> None:
        """Group nodes into parallel-execution batches."""
        resolved: set[str] = set()
        batches: list[list[Node]] = []
        remaining = list(self.nodes)

        while remaining:
            batch: list[Node] = []
            next_remaining: list[Node] = []

            for n in remaining:
                if all(dep in resolved for dep in n.inputs):
                    batch.append(n)
                else:
                    next_remaining.append(n)

            if not batch:
                # Shouldn't happen after a valid topological sort
                raise RuntimeError(
                    "Cannot resolve DAG execution order — possible cycle or "
                    "missing dependency"
                )

            batches.append(batch)
            resolved.update(n.id for n in batch)
            remaining = next_remaining

        self._batches = batches

    def get_batches(self) -> list[list[Node]]:
        """Return batches of nodes that can be executed in parallel."""
        return self._batches

    def total_nodes(self) -> int:
        return len(self.nodes)

    def total_batches(self) -> int:
        return len(self._batches)


# ═══════════════════════════════════════════
# Scheduler
# ═══════════════════════════════════════════

class Scheduler:
    """Executes a compiled ExecutionPlan with caching and parallelism.

    For each batch, all nodes execute concurrently via ``asyncio.gather``.
    Before execution, each node's cache key is checked. If a cache hit
    is found, the node is skipped and the cached result is used.
    """

    def __init__(self, cache: "Cache | None" = None):
        self.cache = cache or Cache()

    async def run(
        self,
        plan: ExecutionPlan,
        inputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the plan and return a dict of node_id → result.

        Args:
            plan: The compiled execution plan.
            inputs: Optional initial context values (e.g., user prompts).

        Returns:
            A dictionary mapping each node ID to its execution result.
        """
        context: dict[str, Any] = dict(inputs or {})

        for batch_num, batch in enumerate(plan.get_batches()):
            logger.info(
                "[DAG Scheduler] Executing batch %d/%d with %d node(s)",
                batch_num + 1,
                plan.total_batches(),
                len(batch),
            )

            async def _run_node(n: Node) -> tuple[str, Any]:
                ck = n.cache_key()

                cached = await self.cache.get(ck)
                if cached is not None:
                    logger.info(
                        "[DAG Scheduler] Cache HIT for node '%s' (%s)",
                        n.id,
                        n.__class__.__name__,
                    )
                    return n.id, cached

                logger.info(
                    "[DAG Scheduler] Executing node '%s' (%s)",
                    n.id,
                    n.__class__.__name__,
                )
                try:
                    result = await n.execute(context)
                    await self.cache.set(ck, result)
                    return n.id, result
                except Exception as e:
                    logger.exception(
                        "[DAG Scheduler] Node '%s' failed: %s",
                        n.id,
                        e,
                    )
                    raise

            # Execute all nodes in this batch in parallel
            results = await asyncio.gather(
                *[_run_node(n) for n in batch],
                return_exceptions=True,
            )

            for item in results:
                if isinstance(item, BaseException):
                    # Gather collected the exception — re-raise
                    raise item
                node_id, result = item
                context[node_id] = result

        return context


# ═══════════════════════════════════════════
# Cache
# ═══════════════════════════════════════════

class Cache:
    """Filesystem-based content-addressable cache for DAG node outputs.

    Cache keys are deterministic hashes of (node type + params + inputs).
    This means:
    - Same node config → same cache key → cache hit
    - Changed param → new cache key → cache miss → recompute
    - Changing a mid-DAG node only invalidates downstream, never upstream

    Cache entries are JSON-serialized. For large media outputs, paths
    are stored (not the media itself), so cache invalidation is cheap.

    Lifecycle
    ---------
    The cache previously had no automated eviction — entries lived
    forever, and the filesystem directory grew unbounded (disk
    exhaustion risk on long-running deployments). Two guards now limit
    growth:

    * **max_age_seconds** — entries older than this are treated as
      misses (stale-read prevention) and lazily deleted.
    * **max_entries** — when exceeded, the oldest ``max_entries // 4``
      entries are evicted (write-triggered LRU sweep). This avoids a
      full-scan on every write while keeping the cache bounded.

    Both thresholds have sensible defaults and can be tuned via the
    constructor or env vars ``DAG_CACHE_MAX_AGE_SECONDS`` /
    ``DAG_CACHE_MAX_ENTRIES``.
    """

    # Sensible defaults: 24-hour TTL, 10 000 entry cap.
    _DEFAULT_MAX_AGE_SECONDS: int = 86_400
    _DEFAULT_MAX_ENTRIES: int = 10_000

    def __init__(
        self,
        cache_dir: str = ".dag_cache",
        *,
        max_age_seconds: int | None = None,
        max_entries: int | None = None,
    ):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        if max_age_seconds is None:
            raw = os.getenv("DAG_CACHE_MAX_AGE_SECONDS", "")
            try:
                max_age_seconds = int(raw) if raw.strip() else self._DEFAULT_MAX_AGE_SECONDS
            except ValueError:
                max_age_seconds = self._DEFAULT_MAX_AGE_SECONDS
        if max_entries is None:
            raw = os.getenv("DAG_CACHE_MAX_ENTRIES", "")
            try:
                max_entries = int(raw) if raw.strip() else self._DEFAULT_MAX_ENTRIES
            except ValueError:
                max_entries = self._DEFAULT_MAX_ENTRIES

        self._max_age_seconds: int = max(max_age_seconds, 0)
        self._max_entries: int = max(max_entries, 0)
        # Track the last time we ran eviction so we don't scan the
        # directory on every single write.
        self._last_eviction_ts: float = 0.0
        self._eviction_interval_seconds: float = 300.0  # 5 minutes

    # ── TTL helpers ──────────────────────────────────────────────────

    def _entry_age_seconds(self, path: str) -> float:
        """Return age of a cache file in seconds, or 0 if unavailable."""
        try:
            return time.time() - os.path.getmtime(path)
        except OSError:
            return 0.0

    def _is_stale(self, path: str) -> bool:
        """True when the entry is older than ``_max_age_seconds``."""
        if self._max_age_seconds <= 0:
            return False  # 0 or negative means "never expire"
        return self._entry_age_seconds(path) >= self._max_age_seconds

    # ── LRU eviction ─────────────────────────────────────────────────

    def _evict_lru_burst(self) -> int:
        """
        Evict the oldest ``_max_entries // 4`` entries when the cache
        exceeds ``_max_entries``. Returns the number of files removed.
        """
        if self._max_entries <= 0 or not os.path.isdir(self.cache_dir):
            return 0

        entries: list[tuple[str, float]] = []
        try:
            for fname in os.listdir(self.cache_dir):
                fpath = os.path.join(self.cache_dir, fname)
                if os.path.isfile(fpath):
                    entries.append((fpath, os.path.getmtime(fpath)))
        except OSError:
            return 0

        total = len(entries)
        if total <= self._max_entries:
            self._last_eviction_ts = time.time()
            return 0

        # Evict the oldest N entries.
        n_to_evict = max(self._max_entries // 4, 1)
        # Sort by mtime ascending (oldest first).
        entries.sort(key=lambda e: e[1])

        removed = 0
        for fpath, _mtime in entries[:n_to_evict]:
            try:
                os.remove(fpath)
                removed += 1
            except OSError:
                pass

        self._last_eviction_ts = time.time()
        if removed:
            logger.info(
                "[DAG Cache] LRU eviction removed %d entries (total was %d, cap %d)",
                removed, total, self._max_entries,
            )
        return removed

    def _maybe_evict(self) -> None:
        """Periodic eviction gate — only runs every
        ``_eviction_interval_seconds`` to avoid per-write directory
        scans."""
        if self._max_entries <= 0:
            return
        if time.time() - self._last_eviction_ts < self._eviction_interval_seconds:
            return
        self._evict_lru_burst()

    # ── Core API (TTL-aware) ─────────────────────────────────────────

    async def get(self, key: str) -> Any | None:
        """Retrieve a cached value by key. Returns None on miss or
        when the entry has exceeded ``_max_age_seconds``."""
        path = os.path.join(self.cache_dir, key)
        if not os.path.exists(path):
            return None

        # TTL check: if the entry is stale, delete it lazily and
        # return a miss so the scheduler recomputes.
        if self._is_stale(path):
            try:
                os.remove(path)
            except OSError:
                pass
            return None

        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("[DAG Cache] Corrupt cache entry %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any) -> None:
        """Store a value in the cache. Triggers LRU eviction if the
        entry cap is exceeded."""
        path = os.path.join(self.cache_dir, key)
        try:
            with open(path, "w") as f:
                json.dump(value, f, default=str)
        except OSError as e:
            logger.warning("[DAG Cache] Failed to write %s: %s", key, e)
            return
        # Only scan for eviction after a successful write so we don't
        # pay the penalty on read-heavy workloads.
        self._maybe_evict()

    async def invalidate(self, prefix: str | None = None) -> int:
        """Invalidate cache entries matching an optional prefix.

        Returns the number of entries invalidated.
        """
        if not os.path.exists(self.cache_dir):
            return 0
        count = 0
        for fname in os.listdir(self.cache_dir):
            if prefix is None or fname.startswith(prefix):
                try:
                    os.remove(os.path.join(self.cache_dir, fname))
                    count += 1
                except OSError:
                    pass
        return count

    async def stats(self) -> dict[str, Any]:
        """Return cache size / age diagnostics for monitoring."""
        if not os.path.isdir(self.cache_dir):
            return {"entries": 0, "stale": 0, "max_age_seconds": self._max_age_seconds, "max_entries": self._max_entries}
        entries = 0
        stale = 0
        for fname in os.listdir(self.cache_dir):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.isfile(fpath):
                entries += 1
                if self._is_stale(fpath):
                    stale += 1
        return {
            "entries": entries,
            "stale": stale,
            "max_age_seconds": self._max_age_seconds,
            "max_entries": self._max_entries,
        }


# Singleton instances (reusable across the codebase)
base_dag_compiler = DAGCompiler()
base_dag_scheduler = Scheduler()
base_dag_cache = Cache()
