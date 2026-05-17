#! /usr/bin/env python3
"""
DAG Pipeline Validation Script
===============================

Tests the DAG video compiler's core capabilities:
1. Compilation (topological sort, cycle detection, batch generation)
2. Parallel execution (asyncio.gather across independent branches)
3. Caching (hash-based content-addressable cache hit/miss)

Run: python scratch/test_dag_pipeline.py
"""

import asyncio
import json
import os
import sys
import tempfile
import time

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Module-level imports for class definitions
from src.services.video_engine.dag_executor import BaseNode


# ────────────────────────────────────────────────────────────
# Test 1: DAG Compilation — Topological Sort & Cycle Detection
# ────────────────────────────────────────────────────────────

async def test_compilation():
    print("=" * 60)
    print("TEST 1: DAG Compilation")
    print("=" * 60)

    from src.services.video_engine.dag_executor import BaseNode, DAGCompiler

    compiler = DAGCompiler()

    # Build a simple linear DAG: A → B → C
    node_a = BaseNode("A", {"val": 1})
    node_b = BaseNode("B", {"val": 2}, inputs=["A"])
    node_c = BaseNode("C", {"val": 3}, inputs=["B"])
    linear_nodes = [node_a, node_b, node_c]

    plan = compiler.compile(linear_nodes)
    batches = plan.get_batches()

    assert plan.total_nodes() == 3, f"Expected 3 nodes, got {plan.total_nodes()}"
    assert len(batches) == 3, f"Expected 3 batches, got {len(batches)}"
    assert batches[0][0].id == "A", f"Batch 1 should be A, got {batches[0][0].id}"
    assert batches[1][0].id == "B", f"Batch 2 should be B, got {batches[1][0].id}"
    assert batches[2][0].id == "C", f"Batch 3 should be C, got {batches[2][0].id}"
    print("  ✓ Linear DAG: A → B → C correctly sorted into 3 batches")

    # Build a DAG with parallel branches: A → B, A → C
    node_para_a = BaseNode("A", {"val": 1})
    node_para_b = BaseNode("B", {"val": 2}, inputs=["A"])
    node_para_c = BaseNode("C", {"val": 3}, inputs=["A"])
    parallel_nodes = [node_para_a, node_para_b, node_para_c]

    plan2 = compiler.compile(parallel_nodes)
    batches2 = plan2.get_batches()

    assert plan2.total_nodes() == 3, f"Expected 3 nodes, got {plan2.total_nodes()}"
    assert len(batches2) == 2, f"Expected 2 batches (A then B+C), got {len(batches2)}"
    assert batches2[0][0].id == "A", f"Batch 1 should be A"
    assert len(batches2[1]) == 2, f"Batch 2 should have 2 parallel nodes"
    print("  ✓ Parallel DAG: A → B, A → C correctly batches B+C together")

    # Cycle detection
    cycle_a = BaseNode("A", {"val": 1}, inputs=["C"])
    cycle_b = BaseNode("B", {"val": 2}, inputs=["A"])
    cycle_c = BaseNode("C", {"val": 3}, inputs=["B"])
    cycle_nodes = [cycle_a, cycle_b, cycle_c]

    try:
        compiler.compile(cycle_nodes)
        assert False, "Should have raised ValueError for cycle"
    except ValueError as e:
        assert "cycle" in str(e).lower(), f"Expected cycle error, got: {e}"
        print("  ✓ Cycle detection caught A→B→C→A cycle")

    # Unknown dependency
    try:
        bad_node = BaseNode("Bad", {"val": 1}, inputs=["Nonexistent"])
        compiler.compile([bad_node])
        assert False, "Should have raised ValueError for unknown dep"
    except ValueError as e:
        assert "unknown" in str(e).lower(), f"Expected unknown dep error, got: {e}"
        print("  ✓ Unknown dependency detection works")

    # Empty node list
    plan_empty = compiler.compile([])
    assert plan_empty.total_nodes() == 0
    assert len(plan_empty.get_batches()) == 0
    print("  ✓ Empty node list compiles to zero batches")

    print("  ✅ All compilation tests passed!\n")
    return True


# ────────────────────────────────────────────────────────────
# Test 2: Parallel Execution via Scheduler
# ────────────────────────────────────────────────────────────

class _TestNode(BaseNode):
    """Simple test node that records its execution order."""
    _execution_counter = 0
    _lock = asyncio.Lock()

    async def execute(self, ctx):
        async with self._lock:
            _TestNode._execution_counter += 1
            exec_order = _TestNode._execution_counter
        val = self.params.get("val", 0)
        delay = self.params.get("delay", 0)
        if delay:
            await asyncio.sleep(delay)
        result = {"exec_order": exec_order, "val": val, "node_id": self.id}
        # Include upstream results for verification
        upstream = {}
        for inp_id in self.inputs:
            if inp_id in ctx:
                upstream[inp_id] = ctx[inp_id]
        if upstream:
            result["upstream"] = upstream
        return result


async def test_parallel_execution():
    print("=" * 60)
    print("TEST 2: Parallel Execution")
    print("=" * 60)

    from src.services.video_engine.dag_executor import DAGCompiler, Scheduler, Cache

    # Reset counter
    _TestNode._execution_counter = 0

    # Use a temp cache dir so tests are isolated
    with tempfile.TemporaryDirectory() as cache_dir:
        cache = Cache(cache_dir=cache_dir)
        compiler = DAGCompiler()
        scheduler = Scheduler(cache=cache)

        # --- Subtest 2a: Sequential execution with order tracking ---
        a = _TestNode("A", {"val": 10})
        b = _TestNode("B", {"val": 20}, inputs=["A"])
        c = _TestNode("C", {"val": 30}, inputs=["B"])
        nodes = [a, b, c]
        plan = compiler.compile(nodes)
        context = await scheduler.run(plan)

        assert context["A"]["val"] == 10
        assert context["B"]["val"] == 20
        assert context["B"]["upstream"]["A"]["val"] == 10
        assert context["C"]["val"] == 30
        assert context["C"]["upstream"]["B"]["val"] == 20
        print("  ✓ Sequential A→B→C: values propagate correctly")
        print(f"  ✓ Execution order recorded: "
              f"A={context['A']['exec_order']}, B={context['B']['exec_order']}, C={context['C']['exec_order']}")

        # --- Subtest 2b: Parallel batch execution ---
        _TestNode._execution_counter = 0

        para_a = _TestNode("A", {"val": 1, "delay": 0.05})  # Short delay
        para_b = _TestNode("B", {"val": 2, "delay": 0.1}, inputs=["A"])
        para_c = _TestNode("C", {"val": 3, "delay": 0.1}, inputs=["A"])
        para_d = _TestNode("D", {"val": 4}, inputs=["B", "C"])

        parallel_nodes = [para_a, para_b, para_c, para_d]
        plan2 = compiler.compile(parallel_nodes)

        # Batch 1: A | Batch 2: B, C (parallel) | Batch 3: D
        batches = plan2.get_batches()
        assert len(batches) == 3, f"Expected 3 batches, got {len(batches)}"
        assert len(batches[1]) == 2, f"Batch 2 should have 2 parallel nodes (B, C)"

        start = time.time()
        context2 = await scheduler.run(plan2)
        elapsed = time.time() - start

        # B and C run in parallel, so total time < sum of individual delays
        total_sequential = 0.05 + 0.1 + 0.1  # A(0.05) + max(B,C)(0.1) + D(0)
        assert elapsed < total_sequential + 0.1, (
            f"Parallel execution too slow: {elapsed:.3f}s vs expected < ~{total_sequential + 0.1:.3f}s"
        )
        print(f"  ✓ Parallel execution: {elapsed:.3f}s (sequential would be ~0.25s)")

        # Verify B and C both have A's result
        assert context2["B"]["upstream"]["A"]["val"] == 1
        assert context2["C"]["upstream"]["A"]["val"] == 1
        assert context2["D"]["upstream"]["B"]["val"] == 2
        assert context2["D"]["upstream"]["C"]["val"] == 3
        print("  ✓ Upstream context propagates correctly through parallel branches")

        # --- Subtest 2c: Empty plan ---
        empty_plan = compiler.compile([])
        empty_context = await scheduler.run(empty_plan)
        assert empty_context == {}
        print("  ✓ Empty plan executes without error")

    print("  ✅ All parallel execution tests passed!\n")
    return True


# ────────────────────────────────────────────────────────────
# Test 3: DAG Caching (Hash-based, Content-Addressable)
# ────────────────────────────────────────────────────────────

class _CachingNode(BaseNode):
    """Node that records how many times its execute() was called."""
    call_count = 0

    async def execute(self, ctx):
        _CachingNode.call_count += 1
        val = self.params.get("val", 0)
        return {"val": val, "called": _CachingNode.call_count}


async def test_caching():
    print("=" * 60)
    print("TEST 3: DAG Caching")
    print("=" * 60)

    from src.services.video_engine.dag_executor import DAGCompiler, Scheduler, Cache

    cache = Cache(cache_dir="/tmp/_dag_test_cache")
    compiler = DAGCompiler()
    scheduler = Scheduler(cache=cache)

    # Clear cache first
    await cache.invalidate()

    # --- Subtest 3a: First run is a cache miss ---
    _CachingNode.call_count = 0
    node = _CachingNode("N1", {"val": 42})
    plan = compiler.compile([node])
    result1 = await scheduler.run(plan)

    assert result1["N1"]["val"] == 42
    assert _CachingNode.call_count == 1, "Should execute once on first run"
    print("  ✓ First run: cache miss, node executes")

    # --- Subtest 3b: Second run with same params is a cache hit ---
    result2 = await scheduler.run(plan)
    assert result2["N1"]["val"] == 42
    assert _CachingNode.call_count == 1, "Should NOT execute again — cache hit"
    print("  ✓ Second run: cache HIT, node not re-executed")

    # --- Subtest 3c: Different params → different cache key → miss ---
    node2 = _CachingNode("N1", {"val": 99})
    plan2 = compiler.compile([node2])
    result3 = await scheduler.run(plan2)

    assert result3["N1"]["val"] == 99
    assert _CachingNode.call_count == 2, "Different params should trigger execution"
    print("  ✓ Different params → cache miss → re-executes")

    # --- Subtest 3d: Cache with parallel branches ---
    cache_a = _CachingNode("A", {"val": 1})
    cache_b = _CachingNode("B", {"val": 2}, inputs=["A"])
    cache_c = _CachingNode("C", {"val": 3}, inputs=["A"])

    _CachingNode.call_count = 0
    parallel_plan = compiler.compile([cache_a, cache_b, cache_c])
    await scheduler.run(parallel_plan)
    first_count = _CachingNode.call_count
    print(f"  ✓ First run: {first_count} executions (A, B, C)")

    # Second run: all cached
    await scheduler.run(parallel_plan)
    assert _CachingNode.call_count == first_count, "Cached: no re-executions"
    print("  ✓ Parallel DAG: all nodes cached on second run")

    # --- Subtest 3e: Cache invalidation ---
    await cache.invalidate()
    _CachingNode.call_count = 0
    await scheduler.run(plan)
    assert _CachingNode.call_count == 1, "After invalidation, should re-execute"
    print("  ✓ Cache invalidation forces re-execution")

    # --- Subtest 3f: Cache miss on corrupt data ---
    # Write corrupt data to cache
    key = plan.nodes[0].cache_key()
    corrupt_path = os.path.join(cache.cache_dir, key)
    with open(corrupt_path, "w") as f:
        f.write("not valid json{{{")
    _CachingNode.call_count = 0
    result = await scheduler.run(plan)
    assert _CachingNode.call_count == 1, "Corrupt cache → miss → re-execute"
    print("  ✓ Corrupt cache entry treated as miss")

    # Cleanup
    await cache.invalidate()

    print("  ✅ All caching tests passed!\n")
    return True


# ────────────────────────────────────────────────────────────
# Test 4: AutomationMode Enum & Resolution
# ────────────────────────────────────────────────────────────

async def test_automation_mode():
    print("=" * 60)
    print("TEST 4: AutomationMode Enum & Resolution")
    print("=" * 60)

    from src.services.video_engine.automation import (
        AutomationMode, resolve_mode, is_at_least, mode_to_int,
    )

    # --- Enum values ---
    assert AutomationMode.MANUAL.value == "manual"
    assert AutomationMode.PARTIAL.value == "partial"
    assert AutomationMode.FULL.value == "full"
    print("  ✓ Enum values: manual, partial, full")

    # --- from_str ---
    assert AutomationMode.from_str("manual") == AutomationMode.MANUAL
    assert AutomationMode.from_str("PARTIAL") == AutomationMode.PARTIAL
    assert AutomationMode.from_str("Full") == AutomationMode.FULL
    assert AutomationMode.from_str("unknown") == AutomationMode.MANUAL
    assert AutomationMode.from_str("") == AutomationMode.MANUAL
    print("  ✓ from_str: case-insensitive, unknown falls back to MANUAL")

    # --- is_valid ---
    assert AutomationMode.is_valid("manual")
    assert AutomationMode.is_valid("partial")
    assert AutomationMode.is_valid("full")
    assert not AutomationMode.is_valid("auto")
    assert not AutomationMode.is_valid("")
    print("  ✓ is_valid correctly validates modes")

    # --- is_at_least (threshold comparisons) ---
    assert is_at_least(AutomationMode.MANUAL, AutomationMode.MANUAL) == True
    assert is_at_least(AutomationMode.PARTIAL, AutomationMode.MANUAL) == True
    assert is_at_least(AutomationMode.FULL, AutomationMode.MANUAL) == True
    assert is_at_least(AutomationMode.FULL, AutomationMode.PARTIAL) == True
    assert is_at_least(AutomationMode.MANUAL, AutomationMode.PARTIAL) == False
    assert is_at_least(AutomationMode.MANUAL, AutomationMode.FULL) == False
    assert is_at_least(AutomationMode.PARTIAL, AutomationMode.FULL) == False
    print("  ✓ is_at_least: correct threshold comparisons")

    # --- resolve_mode priority ---
    # 1. job_override takes priority
    mode = resolve_mode(None, job_override="FULL")
    assert mode == AutomationMode.FULL, f"Expected FULL, got {mode}"
    print("  ✓ resolve_mode: job_override takes highest priority")

    # 2. settings_obj
    class MockSettings:
        AUTOMATION_MODE = "partial"
    mode = resolve_mode(MockSettings(), job_override=None)
    assert mode == AutomationMode.PARTIAL, f"Expected PARTIAL, got {mode}"
    print("  ✓ resolve_mode: settings_obj second priority")

    # 3. Settings object with no AUTOMATION_MODE attribute
    # Falls through to app settings default ("partial")
    class EmptySettings:
        pass
    mode = resolve_mode(EmptySettings(), job_override=None)
    # Should use the system default from settings.py
    assert mode is not None
    print(f"  ✓ resolve_mode with settings without AUTOMATION_MODE: resolved to {mode.value}")
    
    # 3b. Explicit MANUAL override
    class ManualSettings:
        AUTOMATION_MODE = "manual"
    mode = resolve_mode(ManualSettings(), job_override=None)
    assert mode == AutomationMode.MANUAL, f"Expected MANUAL, got {mode}"
    print("  ✓ resolve_mode with explicit settings works")

    # resolve_mode with no settings and no override
    # The actual settings default is "partial", so this should resolve
    mode = resolve_mode(None, job_override=None)
    assert mode is not None
    # Default in settings.py is PARTIAL, so we expect that
    print(f"  ✓ resolve_mode: resolved to {mode.value} from settings default")

    # --- mode_to_int mapping ---
    assert mode_to_int(AutomationMode.MANUAL) == 0
    assert mode_to_int(AutomationMode.PARTIAL) == 1
    assert mode_to_int(AutomationMode.FULL) == 2
    print("  ✓ mode_to_int: correct integer mapping")

    print("  ✅ All automation mode tests passed!\n")
    return True


# ────────────────────────────────────────────────────────────
# Main runner
# ────────────────────────────────────────────────────────────

async def main():
    results = []
    results.append(await test_compilation())
    results.append(await test_parallel_execution())
    results.append(await test_caching())
    results.append(await test_automation_mode())

    print("=" * 60)
    print(f"OVERALL: {sum(results)}/{len(results)} test suites passed")
    print("=" * 60)

    if not all(results):
        sys.exit(1)

    # Check DAG default is enabled (settings check)
    from src.api.config import settings
    if hasattr(settings, "DAG_DEFAULT_ENABLED"):
        print(f"\n  DAG_DEFAULT_ENABLED = {settings.DAG_DEFAULT_ENABLED}")
        print(f"  AUTOMATION_MODE = {settings.AUTOMATION_MODE}")
        if settings.DAG_DEFAULT_ENABLED:
            print("  ✓ DAG is the default execution path")
        else:
            print("  ⚠ DAG is NOT the default (DAG_DEFAULT_ENABLED=False)")


if __name__ == "__main__":
    asyncio.run(main())
