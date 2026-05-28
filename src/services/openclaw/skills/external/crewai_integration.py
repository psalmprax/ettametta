import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

CREWAI_ENABLED = os.getenv("ENABLE_CREWAI", "false").lower() == "true"


class CrewAIService:
    """
    Any CrewAI multi-agent orchestration integration.
    Disabled by default - enable with ENABLE_CREWAI=true

    Used for complex workflows requiring multiple specialized agents.
    """

    def __init__(self):
        self.enabled = CREWAI_ENABLED
        self.agents = {}

        if self.enabled:
            try:
                from crewai import Agent, Task, Crew  # type: ignore
                
                tool_class = None
                try:
                    from langchain_core.tools import Tool  # type: ignore
                    tool_class = Tool
                except ImportError:
                    try:
                        from langchain.tools import Tool  # type: ignore
                        tool_class = Tool
                    except ImportError:
                        pass

                self.agent_class = Agent
                self.task_class = Task
                self.crew_class = Crew
                self.tool_class = tool_class

                logger.info("CrewAI integration enabled")
            except ImportError as e:
                logger.warning(f"CrewAI not installed: {e}. Running in disabled mode.")
                self.enabled = False

    def create_agent(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: list[Any] | None = None,
        verbose: bool = False,
    ) -> Any:
        """Create a CrewAI agent with role and goal."""
        if not self.enabled:
            return None

        try:
            return self.agent_class(
                role=role,
                goal=goal,
                backstory=backstory,
                tools=tools or [],
                verbose=verbose,
            )
        except Exception as e:
            logger.exception(f"Error creating agent: {e}")
            return None

    def create_task(
        self, description: str, agent: Any, expected_output: str | None = None
    ) -> Any:
        """Create a task for an agent."""
        if not self.enabled:
            return None

        try:
            return self.task_class(
                description=description, agent=agent, expected_output=expected_output
            )
        except Exception as e:
            logger.exception(f"Error creating task: {e}")
            return None

    async def run_crew(
        self, agents: list[Any], tasks: list[Any], process: str = "sequential"
    ) -> str:
        """Run a crew with agents and tasks."""
        if not self.enabled:
            return "CrewAI not enabled"

        try:
            crew = self.crew_class(agents=agents, tasks=tasks, process=process)

            result = crew.kickoff()
            return str(result)
        except Exception as e:
            logger.exception(f"Error running crew: {e}")
            return f"Error: {str(e)}"


class EttamettaCrew:
    """
    Pre-configured CrewAI crews for ettametta workflows.
    """

    @staticmethod
    async def run_content_team(topic: str) -> str:
        """Run a content creation team."""
        if not CREWAI_ENABLED:
            return "CrewAI not enabled. Set ENABLE_CREWAI=true"

        try:
            from crewai import Agent, Task, Crew

            researcher = Agent(
                role="Trend Researcher",
                goal="Find the most viral trends and topics",
                backstory="Expert at identifying emerging trends and viral content patterns",
            )

            writer = Agent(
                role="Script Writer",
                goal="Write engaging viral scripts",
                backstory="Expert at crafting high-retention video scripts",
            )

            strategist = Agent(
                role="Publishing Strategist",
                goal="Optimize for maximum reach and monetization",
                backstory="Expert at multi-platform publishing and SEO",
            )

            research_task = Task(
                description=f"Research trending topics for: {topic}",
                agent=researcher,
                expected_output="list of top 5 trending topics with engagement metrics",
            )

            write_task = Task(
                description="Write a viral script based on research",
                agent=writer,
                expected_output="A 60-second viral script with hook, content, CTA",
            )

            strategy_task = Task(
                description="Create publishing strategy for the content",
                agent=strategist,
                expected_output="Multi-platform posting schedule and SEO keywords",
            )

            crew = Crew(
                agents=[researcher, writer, strategist],
                tasks=[research_task, write_task, strategy_task],
                process="sequential",
            )

            return str(crew.kickoff())
        except Exception as e:
            logger.exception(f"Error running content team: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    async def run_affiliate_campaign(niche: str) -> str:
        """Run an affiliate marketing campaign team."""
        if not CREWAI_ENABLED:
            return "CrewAI not enabled. Set ENABLE_CREWAI=true"

        try:
            from crewai import Agent, Task, Crew

            researcher = Agent(
                role="Product Researcher",
                goal=f"Find best affiliate products for {niche}",
                backstory="Expert at finding high-commission affiliate products",
            )

            promoter = Agent(
                role="Content Promoter",
                goal="Create promotional content for products",
                backstory="Expert at creating compelling product promotions",
            )

            researcher_task = Task(
                description=f"Find top affiliate products for {niche}",
                agent=researcher,
                expected_output="list of 5 products with commission rates",
            )

            promoter_task = Task(
                description="Create promotional content for the products",
                agent=promoter,
                expected_output="Promotional posts for each product",
            )

            crew = Crew(
                agents=[researcher, promoter],
                tasks=[researcher_task, promoter_task],
                process="sequential",
            )

            return str(crew.kickoff())
        except Exception as e:
            logger.exception(f"Error running affiliate campaign: {e}")
            return f"Error: {str(e)}"


crewai_service = CrewAIService()
ettametta_crew = EttamettaCrew()
