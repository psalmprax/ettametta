import pytest
import asyncio
import os
import shutil
from unittest.mock import AsyncMock, MagicMock

from src.services.video_engine.dag_executor import (
    BaseNode,
    DAGCompiler,
    Scheduler,
    Cache,
    ExecutionPlan
)


class DummyNode(BaseNode):
    """A dummy node for testing DAG execution."""
    def __init__(self, node_id: str, params: dict = None, inputs: list = None, delay: float = 0.0):
        super().__init__(node_id, params, inputs)
        self.delay = delay
        self.executed_count = 0

    async def execute(self, ctx: dict) -> dict:
        self.executed_count += 1
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        # Build output based on inputs and params
        input_vals = {dep: ctx[dep] for dep in self.inputs if dep in ctx}
        return {
            "node_id": self.id,
            "params": self.params,
            "inputs": input_vals
        }


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Creates a temporary cache directory for DAG execution tests."""
    cache_path = tmp_path / "dag_cache_test"
    yield str(cache_path)
    if cache_path.exists():
        shutil.rmtree(cache_path)


def test_dag_compiler_linear():
    """Verify compilation of a linear dependency graph."""
    # A -> B -> C
    node_a = DummyNode("A")
    node_b = DummyNode("B", inputs=["A"])
    node_c = DummyNode("C", inputs=["B"])

    compiler = DAGCompiler()
    plan = compiler.compile([node_a, node_b, node_c])

    assert plan.total_nodes() == 3
    assert plan.total_batches() == 3
    
    batches = plan.get_batches()
    assert len(batches) == 3
    assert [n.id for n in batches[0]] == ["A"]
    assert [n.id for n in batches[1]] == ["B"]
    assert [n.id for n in batches[2]] == ["C"]


def test_dag_compiler_parallel_batches():
    """Verify that independent nodes are grouped into the same batch."""
    # A, B (independent)
    # C depends on A and B
    # D depends on C
    node_a = DummyNode("A")
    node_b = DummyNode("B")
    node_c = DummyNode("C", inputs=["A", "B"])
    node_d = DummyNode("D", inputs=["C"])

    compiler = DAGCompiler()
    plan = compiler.compile([node_a, node_b, node_c, node_d])

    assert plan.total_nodes() == 4
    assert plan.total_batches() == 3
    
    batches = plan.get_batches()
    # Batch 1: A and B
    batch1_ids = {n.id for n in batches[0]}
    assert batch1_ids == {"A", "B"}
    # Batch 2: C
    assert [n.id for n in batches[1]] == ["C"]
    # Batch 3: D
    assert [n.id for n in batches[2]] == ["D"]


def test_dag_compiler_missing_dependency():
    """Verify compiler raises ValueError if a dependency is missing."""
    node_a = DummyNode("A", inputs=["UNKNOWN"])
    compiler = DAGCompiler()
    with pytest.raises(ValueError) as excinfo:
        compiler.compile([node_a])
    assert "depends on unknown node" in str(excinfo.value)


def test_dag_compiler_cycle_detection():
    """Verify compiler raises ValueError if a cycle is detected."""
    # A -> B -> A
    node_a = DummyNode("A", inputs=["B"])
    node_b = DummyNode("B", inputs=["A"])
    compiler = DAGCompiler()
    with pytest.raises(ValueError) as excinfo:
        compiler.compile([node_a, node_b])
    assert "contains a cycle" in str(excinfo.value)


@pytest.mark.asyncio
async def test_scheduler_execution_success(temp_cache_dir):
    """Verify complete success execution of a branching DAG."""
    # A, B -> C
    node_a = DummyNode("A", params={"val": 10})
    node_b = DummyNode("B", params={"val": 20})
    node_c = DummyNode("C", inputs=["A", "B"])

    compiler = DAGCompiler()
    plan = compiler.compile([node_a, node_b, node_c])

    cache = Cache(cache_dir=temp_cache_dir)
    scheduler = Scheduler(cache=cache)
    
    results = await scheduler.run(plan, inputs={"global_var": "hello"})

    # Check results mapping
    assert "A" in results
    assert "B" in results
    assert "C" in results
    
    assert results["A"]["params"]["val"] == 10
    assert results["B"]["params"]["val"] == 20
    
    # Check that C correctly received the input results from A and B
    assert results["C"]["inputs"]["A"]["node_id"] == "A"
    assert results["C"]["inputs"]["B"]["node_id"] == "B"


@pytest.mark.asyncio
async def test_scheduler_failure_handling(temp_cache_dir):
    """Verify scheduler propagates node execution exceptions."""
    class FailingNode(BaseNode):
        async def execute(self, ctx: dict) -> None:
            raise RuntimeError("Simulation of node failure")

    node_a = DummyNode("A")
    node_fail = FailingNode("Fail", inputs=["A"])

    compiler = DAGCompiler()
    plan = compiler.compile([node_a, node_fail])
    
    cache = Cache(cache_dir=temp_cache_dir)
    scheduler = Scheduler(cache=cache)

    with pytest.raises(RuntimeError) as excinfo:
        await scheduler.run(plan)
    assert "Simulation of node failure" in str(excinfo.value)


@pytest.mark.asyncio
async def test_scheduler_caching_and_invalidation(temp_cache_dir):
    """Verify that cached nodes are not executed twice, and parameter changes invalidate cache."""
    # We use DummyNode which increments its executed_count
    node_a = DummyNode("A", params={"x": 1})
    compiler = DAGCompiler()
    plan1 = compiler.compile([node_a])

    cache = Cache(cache_dir=temp_cache_dir)
    scheduler = Scheduler(cache=cache)

    # 1. First Run: Cache Miss
    res1 = await scheduler.run(plan1)
    assert node_a.executed_count == 1
    assert res1["A"]["node_id"] == "A"

    # 2. Second Run with same plan/node: Cache Hit
    # Reset executed count of node_a
    node_a.executed_count = 0
    res2 = await scheduler.run(plan1)
    # Executed count should be 0 because it was retrieved from cache
    assert node_a.executed_count == 0
    assert res2["A"]["node_id"] == "A"

    # 3. Third Run: Parameter changes -> Cache Miss
    node_a_changed = DummyNode("A", params={"x": 2}) # changed param
    plan2 = compiler.compile([node_a_changed])
    res3 = await scheduler.run(plan2)
    assert node_a_changed.executed_count == 1
    assert res3["A"]["params"]["x"] == 2

    # 4. Invalidate Cache
    await cache.invalidate()
    node_a_changed.executed_count = 0
    res4 = await scheduler.run(plan2)
    # Cache was invalidated, must run again
    assert node_a_changed.executed_count == 1
