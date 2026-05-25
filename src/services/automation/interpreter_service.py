import os
import logging
from typing import Any, Dict
from src.api.config import settings

logger = logging.getLogger(__name__)

class CodeInterpreterService:
    """
    Code Interpreter Service
    Uses Open Interpreter to execute code locally via natural language commands.
    Configured for CPU-safe local execution using Ollama.
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_INTERPRETER", "true").lower() == "true"
        self._setup_interpreter()

    def _setup_interpreter(self):
        """Initializes the interpreter with local-first configuration."""
        try:
            from interpreter import interpreter
            
            # Configure to use local Ollama (OpenAI compatible)
            interpreter.offline = True
            interpreter.auto_run = True
            interpreter.llm.model = f"ollama/{settings.OLLAMA_MODEL}"
            # Use our internal proxy to sanitize responses
            interpreter.llm.api_base = "http://127.0.0.1:8000/api/v1/proxy/ollama/v1"
            interpreter.llm.api_key = "local-unlimited"
            interpreter.llm.temperature = 0
            interpreter.llm.stream = False
            interpreter.llm.max_tokens = 4096
            
            # Additional hardening: Custom instructions to force JSON
            interpreter.custom_instructions = "Return ONLY JSON when executing code. No conversational filler."
            
            # CPU Safety: Limit execution time and prevent heavy background tasks
            interpreter.safe_mode = "ask" # Or "auto" for full automation
            
            self.interpreter = interpreter
            logger.info("🤖 [CodeInterpreter] Initialized with local Ollama support.")
        except Exception as e:
            logger.exception(f"❌ [CodeInterpreter] Initialization failed: {e}")
            self.interpreter = None

    async def execute(self, command: str) -> Dict[str, Any]:
        """
        Executes a natural language command by translating it to code.
        """
        if not self.enabled or not self.interpreter:
            return {"error": "Interpreter service is disabled or not initialized"}

        try:
            logger.info(f"🏃 [CodeInterpreter] Executing: {command}")
            
            # Open Interpreter's chat method returns a list of messages/results
            results = self.interpreter.chat(command)
            
            return {
                "command": command,
                "results": results,
                "status": "success"
            }
        except Exception as e:
            logger.exception(f"❌ [CodeInterpreter] Execution failed: {e}")
            return {"error": str(e), "status": "failed"}

# Singleton instance
base_interpreter_service = CodeInterpreterService()
