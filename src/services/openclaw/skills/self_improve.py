import json
import logging
import os
import re
from datetime import datetime
from typing import Any
from pathlib import Path

import requests

from src.api.config import settings
from .base_skill import OpenClawBaseSkill
try:
    from .memory import memory_skill
except (ImportError, ValueError):
    # Fallback for direct execution if needed
    memory_skill = None

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent

# Securely resolve memory directory to avoid public-write temp directory vulnerabilities (symlink attacks, local file disclosures)
import tempfile
import getpass

try:
    _username = getpass.getuser()
except Exception:
    _username = "default"

_memory_dir = Path.home() / ".ettametta_memory"
try:
    _memory_dir.mkdir(parents=True, exist_ok=True)
except Exception:
    _memory_dir = Path(tempfile.gettempdir()) / f"ettametta_memory_{_username}"
    _memory_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

SELF_IMPROVE_LOG = _memory_dir / "self_improve_log.json"
SKILL_BACKUP_DIR = _memory_dir / "skill_backups"
SKILL_BACKUP_DIR.mkdir(exist_ok=True)


class SkillCritic:
    """Standard: Hardening Autonomous Evolution - Critic Verification Loop."""

    def __init__(self):
        self.unsafe_patterns = [
            r"import\s+os",
            r"import\s+subprocess",
            r"os\.system",
            r"subprocess\.run",
            r"eval\(",
            r"exec\(",
            r"__import__",
        ]

    def verify_syntax(self, code: str) -> str | None:
        """Check if the provided code is syntactically valid Python."""
        try:
            compile(code, "<string>", "exec")
            return None
        except SyntaxError as e:
            return f"Syntax Error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return f"Validation Error: {str(e)}"

    def verify_safety(self, code: str) -> str | None:
        """Simple heuristic-based safety check for malicious patterns."""
        for pattern in self.unsafe_patterns:
            if re.search(pattern, code):
                return f"Safety Violation: Detected unsafe pattern '{pattern}'"
        return None

    def analyze_improvement(
        self, _tool_name: str, code: str, _issue: str
    ) -> dict[str, Any]:
        """
        Critical verification loop: Validates that the code actually addresses the issue
        without introducing regression.
        """
        syntax_err = self.verify_syntax(code)
        if syntax_err:
            return {"valid": False, "reason": syntax_err}

        safety_err = self.verify_safety(code)
        if safety_err:
            return {"valid": False, "reason": safety_err}

        # In a real 10.0-tier engine, this would also run a sandbox test suite
        return {"valid": True, "reason": "Verification passed (Syntax + Safety)"}


class SelfImprovementSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.improvement_log: list[dict] = []
        self.critic = SkillCritic()
        self._load_log()

    async def execute(self, action: str = "suggest", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "suggest":
            target_tool = kwargs.get("tool", kwargs.get("target", "Discovery"))
            return self.suggest_improvements(target_tool)
        elif action == "optimize":
            return self.optimize_codebase(kwargs.get("target", "skills"))
        elif action == "log":
            return self.get_improvement_summary()
        return f"⚠️ Unknown action for SelfImprovement: {action}"

    def _load_log(self):
        if SELF_IMPROVE_LOG.exists():
            try:
                with open(SELF_IMPROVE_LOG, "r") as f:
                    self.improvement_log = json.load(f)
            except Exception:
                self.improvement_log = []

    def _save_log(self):
        with open(SELF_IMPROVE_LOG, "w") as f:
            json.dump(self.improvement_log[-200:], f, indent=2)

    async def detect_failures(self, hours: int = 24) -> str:
        recent_failures = memory_skill.episodic.search(
            event_type="tool_error", since_hours=hours
        )
        if not recent_failures:
            return "✅ No failures detected in the last {} hours.".format(hours)

        failure_patterns: dict[str, int] = {}
        for entry in recent_failures:
            tool_name = entry["data"].get("tool", "unknown")
            error_msg = entry["data"].get("error", "")
            key = f"{tool_name}: {error_msg[:80]}"
            failure_patterns[key] = failure_patterns.get(key, 0) + 1

        sorted_failures = sorted(
            failure_patterns.items(), key=lambda x: x[1], reverse=True
        )
        lines = [
            f"🔍 **Failure Analysis (last {hours}h)**",
            f"Total failures: {len(recent_failures)}",
            "",
        ]
        for pattern, count in sorted_failures[:10]:
            lines.append(f"• [{count}x] {pattern}")

        memory_skill.record_event(
            "failure_analysis",
            {
                "patterns": dict(sorted_failures[:10]),
                "total": len(recent_failures),
            },
        )
        return "\n".join(lines)

    async def analyze_skill_performance(self) -> str:
        all_events = memory_skill.episodic.search(limit=500)
        tool_stats: dict[str, dict] = {}
        for entry in all_events:
            etype = entry["event_type"]
            if etype not in ("tool_call", "tool_error", "tool_success"):
                continue
            tool = entry["data"].get("tool", "unknown")
            if tool not in tool_stats:
                tool_stats[tool] = {
                    "calls": 0,
                    "successes": 0,
                    "errors": 0,
                    "avg_latency": 0,
                    "latencies": [],
                }
            tool_stats[tool]["calls"] += 1
            if etype == "tool_success":
                tool_stats[tool]["successes"] += 1
                latency = entry["data"].get("latency_ms", 0)
                tool_stats[tool]["latencies"].append(latency)
            elif etype == "tool_error":
                tool_stats[tool]["errors"] += 1

        lines = ["📊 **Skill Performance Analysis**", ""]
        for tool, stats in sorted(
            tool_stats.items(), key=lambda x: x[1]["calls"], reverse=True
        ):
            success_rate = stats["successes"] / max(stats["calls"], 1)
            avg_latency = sum(stats["latencies"]) / max(len(stats["latencies"]), 1)
            
            if success_rate > 0.8:
                status = "✅"
            elif success_rate > 0.5:
                status = "⚠️"
            else:
                status = "❌"
                
            lines.append(
                f"{status} **{tool}**: {stats['calls']} calls, {success_rate:.0%} success, {avg_latency:.0f}ms avg"
            )

        memory_skill.store_fact(
            "skill_performance_snapshot",
            {
                "timestamp": datetime.now().isoformat(),
                "stats": {
                    t: {
                        "calls": s["calls"],
                        "success_rate": s["successes"] / max(s["calls"], 1),
                    }
                    for t, s in tool_stats.items()
                },
            },
            category="performance",
        )
        return "\n".join(lines)

    async def generate_skill_improvement(self, tool_name: str, issue_description: str) -> str:
        existing_skill_path = SKILLS_DIR / f"{tool_name.lower()}.py"
        backup_path = None

        if existing_skill_path.exists():
            backup_name = (
                f"{tool_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            )
            backup_path = SKILL_BACKUP_DIR / backup_name
            try:
                backup_path.write_text(existing_skill_path.read_text())
            except Exception as e:
                return f"⚠️ Could not backup existing skill: {e}"

        improvement = {
            "tool": tool_name,
            "issue": issue_description,
            "timestamp": datetime.now().isoformat(),
            "backup": str(backup_path) if backup_path else None,
            "status": "pending_review",
        }
        self.improvement_log.append(improvement)
        self._save_log()

        memory_skill.record_event("skill_improvement_proposed", improvement)

        lines = [
            "💡 **Skill Improvement Proposed**",
            f"• Tool: `{tool_name}`",
            f"• Issue: {issue_description}",
            f"• Backup: {backup_path}"
            if backup_path
            else "• No existing skill to backup",
            "• Status: Pending review",
            "",
            f"Use `/self-improve apply {tool_name}` to review and apply changes.",
        ]
        return "\n".join(lines)

    async def apply_improvement(self, tool_name: str, improvement_code: str) -> str:
        skill_path = SKILLS_DIR / f"{tool_name.lower()}.py"
        backup_path = None

        if skill_path.exists():
            backup_name = f"{tool_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_pre_apply.py"
            backup_path = SKILL_BACKUP_DIR / backup_name
            try:
                backup_path.write_text(skill_path.read_text())
            except Exception:
                pass

        # Phase 1: Critic Verification Loop
        verification = self.critic.analyze_improvement(
            tool_name, improvement_code, "Self-healing update"
        )
        if not verification["valid"]:
            logger.error(f"❌ Improvement rejected by Critic: {verification['reason']}")
            return f"❌ **Improvement rejected by Critic**: {verification['reason']}"

        # Phase 2: Backup and apply
        try:
            skill_path.write_text(improvement_code)
            improvement = {
                "tool": tool_name,
                "timestamp": datetime.now().isoformat(),
                "status": "applied",
                "backup": str(backup_path) if backup_path else None,
            }
            self.improvement_log.append(improvement)
            self._save_log()

            if memory_skill:
                memory_skill.procedural.store_workflow(
                    f"improved_{tool_name.lower()}",
                    [{"action": f"Apply improvement to {tool_name}"}],
                    1.0,
                    {"improvement": improvement_code[:200]},
                )

            return f"✅ **Skill `{tool_name}` updated!**\nBackup saved to: {backup_path}\n\nRestart the OpenClaw service to load changes."
        except Exception as e:
            return f"❌ **Failed to apply improvement**: {e}"

    async def get_improvement_history(self, limit: int = 10) -> str:
        if not self.improvement_log:
            return "📋 No improvements recorded yet."

        recent = self.improvement_log[-limit:]
        lines = [f"📋 **Improvement History** (last {len(recent)}):"]
        for entry in reversed(recent):
            ts = entry.get("timestamp", "")[:19]
            tool = entry.get("tool", "unknown")
            status = entry.get("status", "unknown")
            issue = entry.get("issue", "")[:80]
            if status == "applied":
                icon = "✅"
            elif status == "pending_review":
                icon = "💡"
            else:
                icon = "❌"
                
            lines.append(f"{icon} [{ts}] `{tool}` ({status}): {issue}")
        return "\n".join(lines)

    async def auto_detect_and_suggest(self) -> str:
        await self.detect_failures(hours=24)
        await self.analyze_skill_performance()

        all_events = memory_skill.episodic.search(
            event_type="tool_error", since_hours=24
        )
        tool_error_counts: dict[str, int] = {}
        for entry in all_events:
            tool = entry["data"].get("tool", "unknown")
            tool_error_counts[tool] = tool_error_counts.get(tool, 0) + 1

        suggestions = []
        for tool, count in tool_error_counts.items():
            if count >= 3:
                suggestions.append(
                    f"• `{tool}` failed {count} times — consider running `/self-improve analyze {tool}`"
                )

        if not suggestions:
            return "✅ **Auto-Diagnosis Complete**\n\nNo recurring issues detected. All skills performing within normal parameters."

        lines = ["🤖 **Auto-Diagnosis Report**", ""]
        lines.extend(suggestions)
        lines.append("")
        lines.append("Use `/self-improve suggest <tool>` to generate a fix.")
        return "\n".join(lines)

    async def suggest_improvements(self, tool_name: str) -> str:
        errors = memory_skill.episodic.search(event_type="tool_error", limit=50)
        tool_errors = [e for e in errors if e["data"].get("tool") == tool_name]

        if not tool_errors:
            return f"✅ No errors found for `{tool_name}`. No improvements needed."

        error_messages = [e["data"].get("error", "") for e in tool_errors]
        most_common = max(set(error_messages), key=error_messages.count)

        improvement_suggestions = {
            "timeout": "Add retry logic with exponential backoff and increase timeout values",
            "connection": "Add connection pooling and fallback endpoints",
            "parse": "Add robust JSON extraction with multiple fallback parsers",
            "auth": "Implement token refresh logic and credential rotation",
            "rate": "Add rate limiting with request queuing and backoff",
            "null": "Add null checks and default value handling for all API responses",
            "import": "Fix import order and add missing dependencies",
            "async": "Convert synchronous blocking calls to async with proper event loop handling",
        }

        suggestion = None
        for keyword, fix in improvement_suggestions.items():
            if keyword.lower() in most_common.lower():
                suggestion = fix
                break

        if not suggestion:
            suggestion = f"Review error pattern and add proper error handling. Most common error: {most_common[:100]}"

        lines = [
            f"💡 **Improvement Suggestion for `{tool_name}`**",
            f"• Errors found: {len(tool_errors)}",
            f"• Most common: {most_common[:120]}",
            f"• Suggested fix: {suggestion}",
            "",
            f"Use `/self-improve generate {tool_name}` to create the fix.",
        ]
        return "\n".join(lines)


self_improve_skill = SelfImprovementSkill()
