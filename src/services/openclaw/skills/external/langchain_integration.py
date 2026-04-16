import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

LANGCHAIN_ENABLED = os.getenv("ENABLE_LANGCHAIN", "false").lower() == "true"


class LangChainService:
    """
    Optional LangChain integration for advanced prompt management and LLM chaining.
    Disabled by default - enable with ENABLE_LANGCHAIN=true
    """

    def __init__(self):
        self.enabled = LANGCHAIN_ENABLED
        self.client = None

        if self.enabled:
            try:
                from langchain_groq import ChatGroq
                from langchain.prompts import ChatPromptTemplate
                from langchain.chains import LLMChain
                from langchain.schema import HumanMessage, SystemMessage

                self.ChatGroq = ChatGroq
                self.ChatPromptTemplate = ChatPromptTemplate
                self.LLMChain = LLMChain
                self.SystemMessage = SystemMessage
                self.HumanMessage = HumanMessage

                logger.info("LangChain integration enabled")
            except ImportError as e:
                logger.warning(
                    f"LangChain not installed: {e}. Running in disabled mode."
                )
                self.enabled = False

    def create_chain(
        self,
        system_prompt: str,
        human_prompt: str,
        model_name: str = "llama-3.3-70b-versatile",
    ) -> Optional[Any]:
        """Create an LLM chain with system and human prompts."""
        if not self.enabled or not self.client:
            return None

        try:
            llm = self.ChatGroq(model=model_name)

            prompt = ChatPromptTemplate.from_messages(
                [("system", system_prompt), ("human", "{input}")]
            )

            return LLMChain(llm=llm, prompt=prompt)
        except Exception as e:
            logger.error(f"Error creating LangChain: {e}")
            return None

    async def invoke_chain(self, chain: Any, input_text: str, **kwargs) -> str:
        """Invoke a LangChain with input text."""
        if not chain:
            return "LangChain not initialized"

        try:
            result = await chain.ainvoke({"input": input_text}, **kwargs)
            return result.get("text", str(result))
        except Exception as e:
            logger.error(f"Error invoking chain: {e}")
            return f"Error: {str(e)}"

    def create_sequence(
        self, prompts: List[str], model_name: str = "llama-3.3-70b-versatile"
    ) -> Optional[Any]:
        """Create a sequence of prompts for multi-step processing."""
        if not self.enabled:
            return None

        try:
            from langchain.chains import SimpleSequentialChain

            llm = self.ChatGroq(model=model_name)
            chains = []

            for i, prompt in enumerate(prompts):
                prompt_template = ChatPromptTemplate.from_template(prompt)
                chain = LLMChain(llm=llm, prompt=prompt_template)
                chains.append(chain)

            return SimpleSequentialChain(chains=chains)
        except Exception as e:
            logger.error(f"Error creating sequence: {e}")
            return None


class PromptTemplateManager:
    """
    Manage reusable prompt templates for viral_forge agent.
    """

    TEMPLATES = {
        "trend_analysis": {
            "system": """You are an expert trend analyst for viral content.
Analyze trends for potential viral video content.
Consider: engagement patterns, audience size, competition level, monetization potential.""",
            "human": "Analyze this trend for video content: {topic}",
        },
        "script_generation": {
            "system": """You are a viral script writer for short-form video content.
Create engaging, high-retention scripts for YouTube Shorts/TikTok.
Focus on: hooks, value delivery, emotional triggers, call-to-action.""",
            "human": "Write a viral script about: {topic}",
        },
        "seo_optimization": {
            "system": """You are an SEO expert for video content.
Optimize titles, descriptions, and tags for maximum discoverability.""",
            "human": "SEO optimize this content: {title}",
        },
        "affiliate_recommendation": {
            "system": """You are an affiliate marketing expert.
Recommend relevant products/services that fit the niche and audience.""",
            "human": "Find affiliate products for: {niche}",
        },
        "thumbnail_idea": {
            "system": """You are a thumbnail design expert for viral videos.
Suggest eye-catching thumbnail concepts with high click-through potential.""",
            "human": "Thumbnail ideas for: {title}",
        },
        "publishing_strategy": {
            "system": """You are a multi-platform publishing strategist.
Optimize posting times, hashtags, and cross-platform strategies.""",
            "human": "Publishing strategy for: {content}",
        },
    }

    @classmethod
    def get_template(cls, name: str) -> Optional[Dict]:
        """Get a prompt template by name."""
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_templates(cls) -> List[str]:
        """List all available templates."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def render_template(cls, name: str, **kwargs) -> Dict[str, str]:
        """Render a template with variables."""
        template = cls.get_template(name)
        if not template:
            return {}

        return {
            "system": template["system"],
            "human": template["human"].format(**kwargs),
        }


langchain_service = LangChainService()
prompt_manager = PromptTemplateManager()
