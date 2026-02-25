"""
LangChain Service - Optional LLM chaining & prompt management
=============================================================
Disabled by default. Enable with: ENABLE_LANGCHAIN=true

This service enhances the existing Groq integration with:
- Prompt templates
- L
LM chaining- Memory management
- Output parsing
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

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
        self.enabled = os.getenv("ENABLE_LANGCHAIN", "false").lower() == "true"
        self.llm = None
        self.memory = None
        
        if not self.enabled:
            logger.info("LangChain service is disabled (ENABLE_LANGCHAIN=false)")
            return
            
        if not _langchain_available:
            logger.error("LangChain not installed. Cannot enable service.")
            self.enabled = False
            return
        
        # Initialize with Groq
        from api.config import settings
        
        api_key = settings.GROQ_API_KEY
        if not api_key:
            logger.error("GROQ_API_KEY not configured. LangChain service disabled.")
            self.enabled = False
            return
        
        try:
            self.llm = ChatGroq(
                model=settings.LANGCHAIN_MODEL,
                temperature=settings.LANGCHAIN_TEMPERATURE,
                api_key=api_key
            )
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            logger.info("LangChain service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangChain: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if service is enabled and available."""
        return self.enabled and self.llm is not None
    
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
