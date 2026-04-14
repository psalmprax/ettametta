"""
CrewAI Service - Optional multi-agent orchestration
==================================================
Disabled by default. Enable with: ENABLE_CREWAI=true

This service adds multi-agent workflows for complex content creation:
- Researcher agent (finds trends, topics)
- Writer agent (creates scripts)
- Editor agent (reviews, improves)
- Publisher agent (formats, schedules)
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


# Lazy import - check availability dynamically
def _check_crewai_available() -> bool:
    global _crewai_available
    if _crewai_available is None:
        try:
            import crewai

            _crewai_available = True
        except ImportError:
            _crewai_available = False
            logger.warning("CrewAI not installed")
    return _crewai_available


_crewai_available = None  # Will be checked on first use


class CrewAIService:
    """
    Optional CrewAI multi-agent orchestration.

    Disabled by default - set ENABLE_CREWAI=true to enable.
    Uses Groq as the LLM backend for agents.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_CREWAI", "false").lower() == "true"
        self.agents_config = self._parse_agents_config()
        self.llm = None

        if not self.enabled:
            logger.info("CrewAI service is disabled (ENABLE_CREWAI=false)")
            return

        # Check crewai availability
        if not _check_crewai_available():
            logger.error("CrewAI not installed. Cannot enable service.")
            self.enabled = False
            return

        # Initialize - Try Groq first, then OpenAI
        from api.config import settings

        # Try Groq first
        groq_key = settings.GROQ_API_KEY
        openai_key = settings.OPENAI_API_KEY

        if groq_key and not groq_key.startswith("gsk_"):
            groq_key = None  # Invalid key

        if groq_key:
            try:
                from langchain_community.chat_models import ChatGroq

                self.llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)
                logger.info("CrewAI initialized with Groq")
            except Exception as e:
                logger.warning(f"Groq failed: {e}, trying OpenAI...")
                groq_key = None

        # Fallback to OpenAI if Groq not available
        if not self.llm and openai_key:
            try:
                from langchain_openai import ChatOpenAI

                self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
                logger.info("CrewAI initialized with OpenAI")
            except Exception as e:
                logger.error(f"Failed to initialize CrewAI with OpenAI: {e}")
                self.enabled = False
                return
        elif not self.llm:
            logger.error("No valid LLM key (GROQ_API_KEY or OPENAI_API_KEY)")
            self.enabled = False
            return

        try:
            self.search_tool = DuckDuckGoSearchRun()
            logger.info("CrewAI service initialized successfully")
        except Exception as e:
            logger.warning(f"Search tool failed: {e}")

    def _parse_agents_config(self) -> List[str]:
        """Parse CREWAI_AGENTS from config."""
        from api.config import settings

        agents_str = settings.CREWAI_AGENTS
        return [a.strip() for a in agents_str.split(",") if a.strip()]

    def is_enabled(self) -> bool:
        """Check if service is enabled and available."""
        return self.enabled and self.llm is not None

    def _create_researcher_agent(self):
        """Create researcher agent."""
        from crewai import Agent

        return Agent(
            llm=self.llm,
            role="Researcher",
            goal="Find trending topics, viral content patterns, and audience interests",
            backstory="""You are an expert content researcher with deep knowledge 
            of social media trends, viral content patterns, and audience psychology.
            You excel at identifying emerging topics that resonate with target audiences.""",
            tools=[self.search_tool],
            verbose=True,
        )

    def _create_writer_agent(self):
        """Create writer agent."""
        from crewai import Agent

        return Agent(
            llm=self.llm,
            role="Writer",
            goal="Create engaging scripts and content based on research findings",
            backstory="""You are a professional content writer specializing in 
            short-form video scripts. You know how to hook viewers in the first 
            3 seconds and keep them engaged until the end.""",
            verbose=True,
        )

    def _create_editor_agent(self):
        """Create editor agent."""
        from crewai import Agent

        return Agent(
            llm=self.llm,
            role="Editor",
            goal="Review, refine, and improve content quality",
            backstory="""You are an expert editor with years of experience in 
            video content. You ensure scripts are polished, engaging, and 
            optimized for the platform.""",
            verbose=True,
        )

    def _create_publisher_agent(self):
        """Create publisher agent."""
        from crewai import Agent

        return Agent(
            llm=self.llm,
            role="Publisher",
            goal="Format content for specific platforms and schedule optimally",
            backstory="""You are a social media publishing expert. You know the 
            best times to post, optimal hashtags, and platform-specific formatting.""",
            verbose=True,
        )

    async def run_content_team(
        self, topic: str, platform: str = "youtube"
    ) -> Dict[str, Any]:
        """
        Run content creation team workflow.

        Args:
            topic: Topic to research and create content about
            platform: Target platform (youtube, tiktok, instagram)

        Returns:
            Dict with research, script, edited content, and publishing info
        """
        if not self.is_enabled():
            raise RuntimeError("CrewAI service is not enabled")

        # Create agents based on config
        agents = []
        if "researcher" in self.agents_config:
            agents.append(self._create_researcher_agent())
        if "writer" in self.agents_config:
            agents.append(self._create_writer_agent())
        if "editor" in self.agents_config:
            agents.append(self._create_editor_agent())
        if "publisher" in self.agents_config:
            agents.append(self._create_publisher_agent())

        # If no agents configured, use defaults
        if not agents:
            agents = [
                self._create_researcher_agent(),
                self._create_writer_agent(),
                self._create_editor_agent(),
            ]

        # Create tasks
        from crewai import Task, Crew

        tasks = []

        if any(a.role == "Researcher" for a in agents):
            research_task = Task(
                description=f"Research trending content about: {topic}. Find 3-5 key angles that would work well on {platform}.",
                agent=next(a for a in agents if a.role == "Researcher"),
                expected_output="A list of trending angles and hook ideas",
            )
            tasks.append(research_task)

        if any(a.role == "Writer" for a in agents):
            writer = next(a for a in agents if a.role == "Writer")
            write_task = Task(
                description=f"Write a short-form video script about {topic}. Target 60-90 seconds. Include hooks and calls to action.",
                agent=writer,
                expected_output="A complete video script with hook, body, and CTA",
            )
            tasks.append(write_task)

        if any(a.role == "Editor" for a in agents):
            editor = next(a for a in agents if a.role == "Editor")
            edit_task = Task(
                description="Review and improve the script. Ensure it's engaging, properly formatted, and platform-optimized.",
                agent=editor,
                expected_output="Refined and polished script",
            )
            tasks.append(edit_task)

        # Create and run crew
        crew = Crew(agents=agents, tasks=tasks, verbose=True)

        result = crew.kickoff()

        return {
            "topic": topic,
            "platform": platform,
            "crew_result": str(result),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def run_research_only(self, topic: str) -> Dict[str, Any]:
        """Run just the research agent for trend discovery."""
        if not self.is_enabled():
            raise RuntimeError("CrewAI service is not enabled")

        researcher = self._create_researcher_agent()

        task = Task(
            description=f"Research the following topic and find trending angles: {topic}",
            agent=researcher,
            expected_output="Comprehensive research findings",
        )

        crew = Crew(agents=[researcher], tasks=[task])
        result = crew.kickoff()

        return {
            "topic": topic,
            "research": str(result),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton instance
crewai_service = CrewAIService()
