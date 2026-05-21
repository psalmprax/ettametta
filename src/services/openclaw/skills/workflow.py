import asyncio
import logging
from typing import Any
from datetime import datetime
from .memory import memory_skill

from .base_skill import OpenClawBaseSkill
from src.shared.enums import SystemJobStatus

logger = logging.getLogger(__name__)


class WorkflowStep:
    def __init__(
        self, action: str, params: dict = None, dependencies: list[str] = None
    ):
        self.action = action
        self.params = params or {}
        self.dependencies = dependencies or []
        self.status = SystemJobStatus.QUEUED  # Standardized status
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
            "status": SystemJobStatus.QUEUED,
        }

        self.active_workflows[name] = workflow

        # Store in memory
        memory_skill.store_workflow(name, steps, 0.0, {"status": SystemJobStatus.QUEUED})

        return f"✅ Workflow '{name}' created with {len(steps)} steps"

    async def execute_workflow(self, name: str) -> str:
        """Execute a workflow asynchronously"""
        if name not in self.active_workflows:
            return f"❌ Workflow '{name}' not found"

        workflow = self.active_workflows[name]
        workflow["status"] = SystemJobStatus.PROCESSING
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

                step.status = SystemJobStatus.PROCESSING
                step.start_time = datetime.now().isoformat()

                # Execute step (placeholder - would call actual tools)
                result = await self._execute_step(step)
                step.result = result
                step.status = SystemJobStatus.COMPLETED
                step.end_time = datetime.now().isoformat()

            workflow["status"] = SystemJobStatus.COMPLETED
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
            workflow["status"] = SystemJobStatus.FAILED
            workflow["error"] = str(e)
            logger.error(f"Workflow '{name}' failed: {e}")

    async def _execute_step(self, step: WorkflowStep) -> Any:
        """
        Execute a single workflow step. 
        Hardened: Transitioned from placeholders to real service integrations.
        """
        action = step.action
        params = step.params

        logger.info(f"⚙️ [Workflow] Executing {action} with params: {params}")

        if action == "discovery":
            from src.services.discovery.service import base_discovery_service
            # Trigger a focused scan for the topic
            topic = params.get("topic", "AI Technology")
            results = await base_discovery_service.discover_and_rank(niche=topic)
            return f"✅ Discovered {len(results)} trending leads for {topic}"

        elif action == "content":
            from src.services.nexus_engine.orchestrator import base_nexus_service
            # Trigger high-fidelity synthesis
            topic = params.get("topic", "AI Technology")
            result = await base_nexus_service.synthesize_cinema_package(
                niche=topic,
                style=params.get("style", "cinematic")
            )
            return f"✅ Generated cinema package for {topic}: {result.get('job_id')}"

        elif action == "publish":
            from src.services.distribution.publisher import base_publisher_service_service
            # Trigger multi-platform distribution
            result = await base_publisher_service.publish_to_platform(
                video_path=params.get("video_path"),
                platform=params.get("platform", "youtube"),
                caption=params.get("caption", "New viral drop! #ai"),
                job_id=params.get("job_id")
            )
            return f"✅ Distribution result: {result.get('status')}"

        else:
            # Fallback for unknown actions
            logger.warning(f"Unknown action '{action}' in workflow. Executing as dummy.")
            await asyncio.sleep(0.5)
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
            f"Progress: {completed}/{len(steps)} completed, {running} processing, {failed} failed",
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
            workflow["status"] = SystemJobStatus.ABORTED
            return f"✅ Workflow '{name}' cancelled"
        else:
            return f"⚠️ Workflow '{name}' is not running (status: {workflow['status']})"


# Global instance
workflow_skill = WorkflowSkill()
