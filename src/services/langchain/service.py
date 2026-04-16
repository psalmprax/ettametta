import os
import logging
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def _check_langchain_available():
    try:
        import langchain
        return True
    except ImportError:
        return False

class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 60):
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
            logger.warning("[LangChain] Circuit opened due to failures")

# Lazy import to avoid dependency issues when disabled
_langchain_available = False
try:
    from langchain.prompts import ChatPromptTemplate, PromptTemplate
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain_community.chat_models import ChatGroq
    from langchain.chains import LLMChain, ConversationalChain
    from langchain.memory import ConversationBufferMemory
    from langchain.output_parsers import PydanticOutputParser
    from pydantic import BaseModel
    _langchain_available = True
except ImportError:
    logger.warning("LangChain not installed. Install with: pip install langchain langchain-community")


class LangChainService:
    """
    Optional LangChain enhancement for LLM orchestration.
    
    Disabled by default - set ENABLE_LANGCHAIN=true to enable.
    Uses existing Groq API as the LLM backend.
    """
    
    def __init__(self):
        self.hot_reload()

    def hot_reload(self):
        """Re-initialize service from current environment/settings."""
        self.enabled = os.getenv("ENABLE_LANGCHAIN", "false").lower() == "true"
        
        if not self.enabled:
            self.llm = None
            self.memory = None
            return
            
        if not _langchain_available:
            self.enabled = False
            return
        
        # Initialize with Groq
        from api.config import settings
        
        api_key = settings.GROQ_API_KEY
        if not api_key:
            self.enabled = False
            return
        
        try:
            self.llm = ChatGroq(
                model=settings.LANGCHAIN_MODEL or "llama-3.3-70b-versatile",
                temperature=settings.LANGCHAIN_TEMPERATURE or 0.7,
                api_key=api_key
            )
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            logger.info("[LangChain] Service hot-reloaded successfully")
        except Exception as e:
            logger.error(f"[LangChain] Failed to hot-reload: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if service is enabled and available."""
        return self.enabled and self.llm is not None and not self.circuit_breaker.is_open()
    
    async def analyze_video_vibe(self, niche: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cognitive analysis of video metadata to suggest optimal 'Vibe' and 'Style' overrides.
        Implemented for NexusOrchestrator integration.
        """
        if not self.is_enabled():
            return {}

        prompt = ChatPromptTemplate.from_template("""
        Analyze the following video metadata for the {niche} niche and suggest a viral visual vibe.
        
        METADATA:
        {metadata}
        
        TASK:
        1. Suggest a 'vibe' (e.g., Cinematic, Energetic, Hectic, Calm, Noir).
        2. Suggest a 'filter_override' code (e.g., f7, f8, f9, f12).
        3. Explain why.
        
        Output JSON only.
        """)
        
        try:
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result_str = await chain.arun(niche=niche, metadata=json.dumps(metadata))
            import json as json_lib
            data = json_lib.loads(result_str)
            self.circuit_breaker.record_success()
            logger.info(f"[LangChain] Vibe Analysis Success for {niche}: {data.get('vibe')}")
            return data
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[LangChain] Vibe Analysis Failed: {e}")
            return {}
    
    async def chain_prompt(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        system_message: Optional[str] = None
    ) -> str:
        """
        Use LangChain for structured prompting with context.
        
        Args:
            prompt: User prompt
            context: Additional context dict
            system_message: Optional system message
            
        Returns:
            LLM response string
        """
        if not self.is_enabled():
            raise RuntimeError("LangChain service is not enabled")
        
        # Build messages
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            messages.append(HumanMessage(content=f"Context: {context_str}\n\n{prompt}"))
        else:
            messages.append(HumanMessage(content=prompt))
        
        # Invoke LLM
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
    
    async def chain_with_template(
        self,
        template: str,
        template_vars: Dict[str, Any]
    ) -> str:
        """
        Use a prompt template with variables.
        
        Args:
            template: Prompt template string with {var} placeholders
            template_vars: Dict of variables to fill
            
        Returns:
            Filled prompt response
        """
        if not self.is_enabled():
            raise RuntimeError("LangChain service is not enabled")
        
        prompt = PromptTemplate(
            template=template,
            input_variables=list(template_vars.keys())
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(**template_vars)
        return result
    
    async def conversational_response(
        self,
        user_input: str,
        session_id: str = "default"
    ) -> str:
        """
        Maintain conversation context with memory.
        
        Args:
            user_input: User message
            session_id: Session identifier for memory
            
        Returns:
            AI response with context
        """
        if not self.is_enabled():
            raise RuntimeError("LangChain service is not enabled")
        
        # Get or create session memory
        memory_key = f"session_{session_id}"
        if not hasattr(self, '_session_memories'):
            self._session_memories = {}
        
        if memory_key not in self._session_memories:
            self._session_memories[memory_key] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        
        memory = self._session_memories[memory_key]
        
        chain = ConversationalChain(
            llm=self.llm,
            memory=memory
        )
        
        result = await chain.arun(input=user_input)
        return result
    
    async def predict_virality_score(
        self,
        script_text: str,
        niche: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use LangChain memory and cognitive patterns to predict a script's viral potential.
        Provides a 'Viral Probability' score and improvement tips.
        
        Args:
            script_text: The video script content
            niche: Target niche (e.g. 'coding', 'funny')
            metadata: Additional context (visuals, duration, etc.)
            
        Returns:
            Dict containing viral_score, confidence, and feedback
        """
        if not self.is_enabled():
            return {"viral_score": 0, "status": "disabled"}

        start_time = time.time()
        try:
            prompt = ChatPromptTemplate.from_template("""
                System: You are the ViralForge Predictor. Analyze the following script for viral potential.
                Niche: {niche}
                Metadata: {metadata}
                
                Script:
                {script_text}
                
                Analyze based on:
                1. Hook Strength (0-100)
                2. Translatability (0-100)
                3. Retention Hooks (0-100)
                
                Return a JSON object with:
                - viral_score (int)
                - probability (float)
                - feedback (str)
                - suggested_edits (list)
            """)
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            result = await chain.arun(
                niche=niche,
                metadata=json.dumps(metadata or {}),
                script_text=script_text
            )
            
            # Record success
            self.circuit_breaker.record_success()
            
            # Simple cleanup of response if it's not pure JSON
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            
            return json.loads(result)
            
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"[LangChain] Virality prediction failed: {e}")
            return {"error": str(e), "viral_score": 0}
        finally:
            logger.info(f"[LangChain] Virality prediction completed in {time.time() - start_time:.2f}s")
    
    async def parse_output(
        self,
        prompt: str,
        output_class: type[BaseModel]
    ) -> BaseModel:
        """
        Parse LLM output into a Pydantic model.
        
        Args:
            prompt: User prompt
            output_class: Pydantic model class
            
        Returns:
            Parsed Pydantic object
        """
        if not self.is_enabled():
            raise RuntimeError("LangChain service is not enabled")
        
        parser = PydanticOutputParser(pydantic_object=output_class)
        
        prompt_with_format = f"""{prompt}

{parser.get_format_instructions()}
"""
        
        response = await self.chain_prompt(prompt_with_format)
        return parser.parse(response)


# Singleton instance
langchain_service = LangChainService()
