import os
import logging
import time
import json
from typing import Any
from datetime import datetime

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 120):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("[CrewAI] Circuit opened due to agent execution failures")

class CrewAIService:
    """
    Elite CrewAI multi-agent orchestration.
    Uses dynamic task generation to tailor agent missions to specific topics.
    """

    def __init__(self):
        self._available = None
        self.enabled = False
        self.llm = None
        self.search_tool = None
        self.circuit_breaker = CircuitBreaker()
        self.hot_reload()

    def _check_crewai_available(self) -> bool:
        """Dynamically check if CrewAI and required deps are installed."""
        if self._available is None:
            try:
                import crewai
                from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
                self._available = True
            except ImportError:
                self._available = False
                logger.warning("[CrewAI] CrewAI or dependencies not installed")
        return self._available

    def hot_reload(self):
        """Re-initialize service from current environment/settings."""
        from src.api.config import settings
        
        self.enabled = settings.ENABLE_CREWAI
        if not self.enabled:
            return
            
        if not self._check_crewai_available():
            logger.error("[CrewAI] Service enabled but dependencies missing. Disabling.")
            self.enabled = False
            return

        # Initialize LLM - Try Groq first, then OpenAI
        groq_key = settings.GROQ_API_KEY
        openai_key = settings.OPENAI_API_KEY

        if groq_key and groq_key.startswith("gsk_"):
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
                logger.info("[CrewAI] Initialized with Groq (Elite Model)")
            except Exception as e:
                logger.warning(f"[CrewAI] Groq initialization failed: {e}")
                self.llm = None

        if not self.llm and openai_key:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
                logger.info("[CrewAI] Initialized with OpenAI fallback")
            except Exception as e:
                logger.error(f"[CrewAI] Failed fallback to OpenAI: {e}")
                self.enabled = False
                return

        if not self.llm:
            logger.error("[CrewAI] No valid LLM keys configured")
            self.enabled = False
            return

        try:
            from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
            self.search_tool = DuckDuckGoSearchRun()
        except Exception as e:
            logger.warning(f"[CrewAI] Search tool unavailable: {e}")

    def is_enabled(self) -> bool:
        return self.enabled and self.llm is not None

    async def _generate_dynamic_tasks(self, topic: str, platform: str) -> list[dict[str, str]]:
        """
        Uses an LLM to generate specific tasks for the crew based on the topic.
        This ensures 'Elite' tier dynamism over static stubs.
        """
        prompt = f"""
        You are the ViralForge Strategy Architect.
        Generate a set of tasks for a content creation crew working on: '{topic}' for {platform}.
        
        CREW ROLES: Researcher, Fact Checker, Writer, Editor.
        
        OUTPUT FORMAT (JSON list of Task Objects):
        [
            {{
                "role": "Researcher",
                "description": "...",
                "expected_output": "..."
            }},
            ...
        ]
        """
        
        try:
            # For dynamic task generation, we use the initialized LLM
            response = self.llm.invoke(prompt)
            content = getattr(response, 'content', str(response))
            # Basic cleanup if LLM wraps in code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)
        except Exception as e:
            logger.warning(f"[CrewAI] Dynamic task generation failed, using fallback: {e}")
            return self._get_fallback_tasks(topic, platform)

    def _get_fallback_tasks(self, topic: str, platform: str) -> list[dict[str, str]]:
        return [
            {"role": "Researcher", "description": f"Find trending patterns for {topic}", "expected_output": "Viral angles list"},
            {"role": "Fact Checker", "description": "Verify claims and data", "expected_output": "Verification report"},
            {"role": "Writer", "description": f"Write a {platform} script", "expected_output": "Complete script"},
            {"role": "Editor", "description": "Polish and optimize for virality", "expected_output": "Final script"}
        ]

    def _create_agent(self, role: str, goal: str, backstory: str, tools: list = None):
        """Generic agent factory."""
        from crewai import Agent
        return Agent(
            llm=self.llm,
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools or [],
            verbose=True
        )

    async def run_content_team(self, topic: str, platform: str = "youtube") -> dict[str, Any]:
        """Execute the content team workflow with dynamic tasks."""
        if not self.is_enabled():
            raise RuntimeError("CrewAI service is disabled")

        if self.circuit_breaker.is_open():
            raise RuntimeError("CrewAI circuit breaker is OPEN")

        try:
            from crewai import Crew, Task, Agent
            
            # 1. Generate dynamic tasks
            task_specs = await self._generate_dynamic_tasks(topic, platform)
            
            # 2. Build Agent definitions (Elite patterns)
            agents_map = {
                "Researcher": self._create_agent("Researcher", f"Find viral {topic} hooks", "Expert trend hunter", [self.search_tool] if self.search_tool else []),
                "Fact Checker": self._create_agent("Fact Checker", "Ensure 100% accuracy", "Meticulous verification expert", [self.search_tool] if self.search_tool else []),
                "Writer": self._create_agent("Writer", "Write high-retention scripts", "Viral scriptwriting master"),
                "Editor": self._create_agent("Editor", "Polish for maximum engagement", "Elite platform editor")
            }
            
            # 3. Assemble Tasks
            tasks = []
            for spec in task_specs:
                role = spec.get("role")
                if role in agents_map:
                    tasks.append(Task(
                        description=spec["description"],
                        expected_output=spec["expected_output"],
                        agent=agents_map[role]
                    ))
            
            # 4. Run Crew
            crew = Crew(agents=list(agents_map.values()), tasks=tasks, verbose=True)
            result = crew.kickoff()
            
            self.circuit_breaker.record_success()
            return {
                "topic": topic,
                "platform": platform,
                "result": str(result),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[CrewAI] Workflow failed: {e}")
            raise

# Singleton instance
crewai_service = CrewAIService()


# Standalone function for module-level imports (e.g., from llm/service.py)
def _check_crewai_available() -> bool:
    """Check if CrewAI and required dependencies are available."""
    try:
        import crewai
        from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
        return True
    except ImportError:
        return False
