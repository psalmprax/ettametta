import asyncio
import logging
from typing import Any
from datetime import datetime
from .memory import memory_skill

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class WorkflowStep:
    def __init__(
        self, action: str, params: dict = None, dependencies: list[str] = None
    ):
        self.action = action
        self.params = params or {}
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, running, completed, failed
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None

    async def to_dict(self) -> dict:
        return {
            "action": self.action,
            "params": self.params,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


class WorkflowSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.active_workflows: dict[str, dict] = {}

    async def execute(self, action: str = "list", name: str = "", steps: list[dict] = None, **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "create":
            return self.create_workflow(name, steps or [])
        elif action == "execute":
            return self.execute_workflow(name)
        elif action == "status":
            return self.get_workflow_status(name)
        return self.list_workflows()

    async def create_workflow(self, name: str, steps: list[dict]) -> str:
        """Create a new workflow definition"""
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                action=step_data.get("action", ""),
                params=step_data.get("params", {}),
                dependencies=step_data.get("dependencies", []),
            )
            workflow_steps.append(step)

        workflow = {
            "name": name,
            "steps": workflow_steps,
            "created_at": datetime.now().isoformat(),
            "status": "created",
        }

        self.active_workflows[name] = workflow

        # Store in memory
        memory_skill.store_workflow(name, steps, 0.0, {"status": "created"})

        return f"✅ Workflow '{name}' created with {len(steps)} steps"

    async def execute_workflow(self, name: str) -> str:
        """Execute a workflow asynchronously"""
        if name not in self.active_workflows:
            return f"❌ Workflow '{name}' not found"

        workflow = self.active_workflows[name]
        workflow["status"] = "running"
        workflow["start_time"] = datetime.now().isoformat()

        # Start async execution
        asyncio.create_task(self._execute_workflow_async(workflow))

        return f"🚀 Workflow '{name}' execution started"

    async def _execute_workflow_async(self, workflow: dict) -> None:
        """Execute workflow steps in order"""
        name = workflow["name"]
        steps = workflow["steps"]

        try:
            # Simple sequential execution (could be made parallel with dependency resolution)
            for step in steps:
                if step.dependencies:
                    # Wait for dependencies (simplified)
                    await asyncio.sleep(0.1)  # Placeholder

                step.status = "running"
                step.start_time = datetime.now().isoformat()

                # Execute step (placeholder - would call actual tools)
                result = await self._execute_step(step)
                step.result = result
                step.status = "completed"
                step.end_time = datetime.now().isoformat()

            workflow["status"] = "completed"
            workflow["end_time"] = datetime.now().isoformat()

            # Record success
            memory_skill.record_event(
                "workflow_completed",
                {
                    "workflow": name,
                    "steps": len(steps),
                    "duration": workflow["end_time"],
                },
            )

        except Exception as e:
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            logger.error(f"Workflow '{name}' failed: {e}")

    async def _execute_step(self, step: WorkflowStep) -> Any:
        """Execute a single workflow step (placeholder)"""
        # This would integrate with the actual tools
        action = step.action
        params = step.params

        # Simulate execution time
        await asyncio.sleep(1)

        if action == "discovery":
            return f"Discovered trends for {params.get('topic', 'general')}"
        elif action == "content":
            return f"Generated content for {params.get('niche', 'general')}"
        elif action == "publish":
            return f"Published to {params.get('platform', 'YouTube')}"
        else:
            return f"Executed {action} with params {params}"

    async def get_workflow_status(self, name: str) -> str:
        """Get status of a workflow"""
        if name not in self.active_workflows:
            return f"❌ Workflow '{name}' not found"

        workflow = self.active_workflows[name]
        status = workflow["status"]
        steps = workflow["steps"]

        completed = sum(1 for s in steps if s.status == "completed")
        running = sum(1 for s in steps if s.status == "running")
        failed = sum(1 for s in steps if s.status == "failed")

        lines = [
            f"🔄 **Workflow: {name}**",
            f"Status: {status.upper()}",
            f"Progress: {completed}/{len(steps)} completed, {running} running, {failed} failed",
        ]

        if workflow.get("error"):
            lines.append(f"Error: {workflow['error']}")

        return "\n".join(lines)

    async def list_workflows(self) -> str:
        """list all active workflows"""
        if not self.active_workflows:
            return "📋 No active workflows"

        lines = ["📋 **Active Workflows**:"]
        for name, workflow in self.active_workflows.items():
            status = workflow["status"]
            steps = len(workflow["steps"])
            lines.append(f"• {name}: {status} ({steps} steps)")

        return "\n".join(lines)

    async def cancel_workflow(self, name: str) -> str:
        """Cancel a running workflow"""
        if name not in self.active_workflows:
            return f"❌ Workflow '{name}' not found"

        workflow = self.active_workflows[name]
        if workflow["status"] == "running":
            workflow["status"] = "cancelled"
            return f"✅ Workflow '{name}' cancelled"
        else:
            return f"⚠️ Workflow '{name}' is not running (status: {workflow['status']})"


# Global instance
workflow_skill = WorkflowSkill()
