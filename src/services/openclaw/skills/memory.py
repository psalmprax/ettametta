import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any
from pathlib import Path

logger = logging.getLogger(__name__)

MEMORY_DIR = Path("/tmp/viral_forge_memory")
MEMORY_DIR.mkdir(exist_ok=True)

GRAPH_FILE = MEMORY_DIR / "knowledge_graph.json"
EPISODIC_FILE = MEMORY_DIR / "episodic.json"
PROCEDURAL_FILE = MEMORY_DIR / "procedural.json"
SEMANTIC_FILE = MEMORY_DIR / "semantic.json"

DEFAULT_STALENESS_DAYS = {
    "trend": 7,
    "performance": 30,
    "hook": 14,
    "niche": 30,
    "audience": 60,
    "platform_algo": 14,
    "competitor": 21,
    "script": 90,
    "affiliate": 30,
    "default": 60,
}


class MemoryNode:
    def __init__(
        self, node_id: str, category: str, data: dict, actor: str = "openclaw"
    ):
        self.node_id = node_id
        self.category = category
        self.data = data
        self.actor = actor
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.access_count = 0
        self.staleness_days = DEFAULT_STALENESS_DAYS.get(
            category, DEFAULT_STALENESS_DAYS["default"]
        )

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "category": self.category,
            "data": self.data,
            "actor": self.actor,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "staleness_days": self.staleness_days,
        }

    @staticmethod
    def from_dict(d: dict) -> "MemoryNode":
        node = MemoryNode(
            d["node_id"], d["category"], d["data"], d.get("actor", "openclaw")
        )
        node.created_at = d["created_at"]
        node.updated_at = d.get("updated_at", d["created_at"])
        node.access_count = d.get("access_count", 0)
        node.staleness_days = d.get("staleness_days", DEFAULT_STALENESS_DAYS["default"])
        return node

    def is_stale(self) -> bool:
        updated = datetime.fromisoformat(self.updated_at)
        return datetime.now() > updated + timedelta(days=self.staleness_days)

    def touch(self):
        self.access_count += 1
        self.updated_at = datetime.now().isoformat()


class MemoryGraph:
    def __init__(self):
        self.nodes: dict[str, MemoryNode] = {}
        self.edges: list[dict[str, str]] = []
        self._load()

    def _load(self):
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r") as f:
                    data = json.load(f)
                self.nodes = {
                    nid: MemoryNode.from_dict(nd)
                    for nid, nd in data.get("nodes", {}).items()
                }
                self.edges = data.get("edges", [])
            except Exception:
                self.nodes = {}
                self.edges = []

    def _save(self):
        with open(GRAPH_FILE, "w") as f:
            json.dump(
                {
                    "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
                    "edges": self.edges,
                },
                f,
                indent=2,
            )

    def add_node(self, node: MemoryNode):
        self.nodes[node.node_id] = node
        self._save()

    def add_edge(self, from_id: str, to_id: str, relation: str):
        self.edges.append({"from": from_id, "to": to_id, "relation": relation})
        self._save()

    def get_related(
        self, node_id: str, relation: str | None = None
    ) -> list[MemoryNode]:
        related_ids = set()
        for edge in self.edges:
            if relation and edge["relation"] != relation:
                continue
            if edge["from"] == node_id:
                related_ids.add(edge["to"])
            elif edge["to"] == node_id:
                related_ids.add(edge["from"])
        return [self.nodes[nid] for nid in related_ids if nid in self.nodes]

    def get_by_category(self, category: str) -> list[MemoryNode]:
        return [
            n
            for n in self.nodes.values()
            if n.category == category and not n.is_stale()
        ]

    def remove_stale(self) -> int:
        stale_ids = [nid for nid, n in self.nodes.items() if n.is_stale()]
        for nid in stale_ids:
            del self.nodes[nid]
        self.edges = [
            e for e in self.edges if e["from"] in self.nodes and e["to"] in self.nodes
        ]
        if stale_ids:
            self._save()
        return len(stale_ids)


class EpisodicMemory:
    def __init__(self):
        self.entries: list[dict] = []
        self._load()

    def _load(self):
        if EPISODIC_FILE.exists():
            try:
                with open(EPISODIC_FILE, "r") as f:
                    self.entries = json.load(f)
            except Exception:
                self.entries = []

    def _save(self):
        with open(EPISODIC_FILE, "w") as f:
            json.dump(self.entries[-500:], f, indent=2)

    def record(
        self,
        event_type: str,
        data: dict,
        actor: str = "openclaw",
        session_id: str | None = None,
    ):
        entry = {
            "event_type": event_type,
            "data": data,
            "actor": actor,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
        self.entries.append(entry)
        self._save()

    def search(
        self,
        event_type: str | None = None,
        actor: str | None = None,
        limit: int = 10,
        since_hours: int | None = None,
    ) -> list[dict]:
        results = self.entries
        if event_type:
            results = [e for e in results if e["event_type"] == event_type]
        if actor:
            results = [e for e in results if e["actor"] == actor]
        if since_hours:
            cutoff = datetime.now() - timedelta(hours=since_hours)
            results = [
                e for e in results if datetime.fromisoformat(e["timestamp"]) > cutoff
            ]
        return results[-limit:]


class ProceduralMemory:
    def __init__(self):
        self.workflows: dict[str, dict] = {}
        self._load()

    def _load(self):
        if PROCEDURAL_FILE.exists():
            try:
                with open(PROCEDURAL_FILE, "r") as f:
                    self.workflows = json.load(f)
            except Exception:
                self.workflows = {}

    def _save(self):
        with open(PROCEDURAL_FILE, "w") as f:
            json.dump(self.workflows, f, indent=2)

    def store_workflow(
        self,
        name: str,
        steps: list[dict],
        success_rate: float,
        context: dict | None = None,
        actor: str = "openclaw",
    ):
        self.workflows[name] = {
            "steps": steps,
            "success_rate": success_rate,
            "context": context or {},
            "actor": actor,
            "executions": self.workflows.get(name, {}).get("executions", 0) + 1,
            "last_success": datetime.now().isoformat(),
            "created_at": self.workflows.get(name, {}).get(
                "created_at", datetime.now().isoformat()
            ),
        }
        self._save()

    def get_workflow(self, name: str) -> dict | None:
        return self.workflows.get(name)

    def get_all_workflows(self) -> dict[str, dict]:
        return self.workflows

    def delete_workflow(self, name: str):
        self.workflows.pop(name, None)
        self._save()


class SemanticMemory:
    def __init__(self):
        self.facts: dict[str, dict] = {}
        self._load()

    def _load(self):
        if SEMANTIC_FILE.exists():
            try:
                with open(SEMANTIC_FILE, "r") as f:
                    self.facts = json.load(f)
            except Exception:
                self.facts = {}

    def _save(self):
        with open(SEMANTIC_FILE, "w") as f:
            json.dump(self.facts, f, indent=2)

    def store_fact(
        self,
        key: str,
        value: Any,
        category: str = "general",
        source: str = "openclaw",
        confidence: float = 1.0,
    ):
        self.facts[key] = {
            "value": value,
            "category": category,
            "source": source,
            "confidence": confidence,
            "updated_at": datetime.now().isoformat(),
        }
        self._save()

    def get_fact(self, key: str) -> Any:
        fact = self.facts.get(key)
        if fact:
            return fact["value"]
        return None

    def get_by_category(self, category: str) -> dict[str, Any]:
        return {
            k: v["value"] for k, v in self.facts.items() if v["category"] == category
        }

    def delete_fact(self, key: str):
        self.facts.pop(key, None)
        self._save()


class MemorySkill:
    def __init__(self):
        self.graph = MemoryGraph()
        self.episodic = EpisodicMemory()
        self.procedural = ProceduralMemory()
        self.semantic = SemanticMemory()

    def record_event(
        self,
        event_type: str,
        data: dict,
        actor: str = "openclaw",
        session_id: str | None = None,
    ) -> str:
        self.episodic.record(event_type, data, actor, session_id)
        node_id = f"{event_type}_{int(time.time())}"
        node = MemoryNode(node_id, event_type, data, actor)
        self.graph.add_node(node)
        return f"✅ Event recorded: {event_type}"

    def store_workflow(
        self,
        name: str,
        steps: list[dict],
        success_rate: float,
        context: dict | None = None,
    ) -> str:
        self.procedural.store_workflow(name, steps, success_rate, context)
        node = MemoryNode(
            f"workflow_{name}",
            "workflow",
            {"name": name, "steps_count": len(steps), "success_rate": success_rate},
        )
        self.graph.add_node(node)
        return f"✅ Workflow '{name}' stored ({len(steps)} steps, {success_rate:.0%} success rate)"

    def store_fact(
        self,
        key: str,
        value: Any,
        category: str = "general",
        source: str = "openclaw",
        confidence: float = 1.0,
    ) -> str:
        self.semantic.store_fact(key, value, category, source, confidence)
        node = MemoryNode(
            f"fact_{key}", category, {"key": key, "value": str(value)}, source
        )
        self.graph.add_node(node)
        return f"✅ Fact stored: {key} = {value}"

    def link_memories(self, from_id: str, to_id: str, relation: str) -> str:
        self.graph.add_edge(from_id, to_id, relation)
        return f"✅ Linked: {from_id} --[{relation}]--> {to_id}"

    def recall_events(
        self,
        event_type: str | None = None,
        actor: str | None = None,
        limit: int = 10,
        since_hours: int | None = None,
    ) -> str:
        entries = self.episodic.search(event_type, actor, limit, since_hours)
        if not entries:
            return "🧠 No matching memories found."
        lines = [f"🧠 **Episodic Memory** ({len(entries)} entries):"]
        for e in entries:
            ts = e["timestamp"][:19]
            lines.append(
                f"• [{ts}] [{e['actor']}] {e['event_type']}: {json.dumps(e['data'], indent=2)[:200]}"
            )
        return "\n".join(lines)

    def recall_workflows(self, name: str | None = None) -> str:
        if name:
            wf = self.procedural.get_workflow(name)
            if not wf:
                return f"🧠 No workflow found: '{name}'"
            lines = [
                f"🧠 **Workflow: {name}**",
                f"• Success Rate: {wf['success_rate']:.0%}",
                f"• Executions: {wf['executions']}",
                f"• Steps: {len(wf['steps'])}",
            ]
            for i, step in enumerate(wf["steps"], 1):
                lines.append(f"  {i}. {step.get('action', 'unknown')}")
            return "\n".join(lines)
        workflows = self.procedural.get_all_workflows()
        if not workflows:
            return "🧠 No workflows stored."
        lines = [f"🧠 **Stored Workflows** ({len(workflows)}):"]
        for n, w in workflows.items():
            lines.append(
                f"• {n}: {w['success_rate']:.0%} success, {w['executions']} runs"
            )
        return "\n".join(lines)

    def recall_facts(
        self, category: str | None = None, key: str | None = None
    ) -> str:
        if key:
            val = self.semantic.get_fact(key)
            if val is None:
                return f"🧠 Fact not found: '{key}'"
            return f"🧠 **Fact**: {key} = {val}"
        if category:
            facts = self.semantic.get_by_category(category)
            if not facts:
                return f"🧠 No facts in category: '{category}'"
            lines = [f"🧠 **Facts: {category}** ({len(facts)}):"]
            for k, v in facts.items():
                lines.append(f"• {k}: {v}")
            return "\n".join(lines)
        return f"🧠 {len(self.semantic.facts)} facts stored across {len(set(f['category'] for f in self.semantic.facts.values()))} categories"

    def get_related_memories(self, node_id: str, relation: str | None = None) -> str:
        related = self.graph.get_related(node_id, relation)
        if not related:
            return f"🧠 No related memories for '{node_id}'"
        lines = [f"🧠 **Related to {node_id}** ({len(related)}):"]
        for r in related:
            lines.append(f"• [{r.category}] {r.node_id}: {json.dumps(r.data)[:150]}")
        return "\n".join(lines)

    def cleanup_stale(self) -> str:
        removed_graph = self.graph.remove_stale()
        cutoff = datetime.now() - timedelta(days=90)
        old_count = len(self.episodic.entries)
        self.episodic.entries = [
            e
            for e in self.episodic.entries
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        removed_episodic = old_count - len(self.episodic.entries)
        if removed_episodic:
            self.episodic._save()
        return f"🧹 Cleaned up {removed_graph} stale graph nodes, {removed_episodic} old episodic entries"

    def get_memory_summary(self) -> str:
        graph_nodes = len(self.graph.nodes)
        graph_edges = len(self.graph.edges)
        episodic_count = len(self.episodic.entries)
        workflow_count = len(self.procedural.workflows)
        fact_count = len(self.semantic.facts)
        stale_count = sum(1 for n in self.graph.nodes.values() if n.is_stale())
        lines = [
            "🧠 **Memory System Summary**",
            f"• Graph: {graph_nodes} nodes, {graph_edges} edges ({stale_count} stale)",
            f"• Episodic: {episodic_count} events",
            f"• Procedural: {workflow_count} workflows",
            f"• Semantic: {fact_count} facts",
        ]
        return "\n".join(lines)


memory_skill = MemorySkill()
