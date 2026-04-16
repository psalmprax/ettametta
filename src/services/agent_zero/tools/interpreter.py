import logging
from typing import Dict, Any
from services.interpreter.service import interpreter_service

logger = logging.getLogger(__name__)

class InterpreterTool:
    """
    Standardized Tool for Agent Zero to execute custom Python/JS code.
    Enables dynamic video processing and troubleshooting.
    """
    def __init__(self):
        self.service = interpreter_service

    async def run(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Executes code securely in a sandboxed environment.
        """
        try:
            if not self.service.is_enabled():
                return {"error": "Interpreter service is disabled. Set ENABLE_INTERPRETER=true."}
            
            result = await self.service.execute_code(code, language)
            return result
                
        except Exception as e:
            logger.error(f"InterpreterTool Error: {e}")
            return {"error": str(e)}

interpreter_tool = InterpreterTool()
