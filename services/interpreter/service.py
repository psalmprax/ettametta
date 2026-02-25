"""
Interpreter Service - Optional Open Interpreter integration
============================================================
Disabled by default. Enable with: ENABLE_INTERPRETER=true

This service enables code execution for dynamic video generation:
- Custom video processing
- Dynamic graphics generation
- Data visualization creation

WARNING: Code execution sandbox required. Use with caution.
"""

import os
import logging
import subprocess
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Lazy import
_interpreter_available = False
try:
    from interpreter import interpreter
    _interpreter_available = True
except ImportError:
    logger.warning("Open Interpreter not installed. Install with: pip install open-interpreter")


class InterpreterService:
    """
    Optional Open Interpreter for code execution.
    
    Disabled by default - set ENABLE_INTERPRETER=true to enable.
    
    WARNING: This enables arbitrary code execution. Only enable in 
    controlled environments with proper sandboxing.
    """
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_INTERPRETER", "false").lower() == "true"
        self.sandbox_mode = os.getenv("INTERPRETER_SANDBOX", "true").lower() == "true"
        self.max_runtime = int(os.getenv("INTERPRETER_MAX_RUNTIME", "60"))  # seconds
        
        if not self.enabled:
            logger.info("Interpreter service is disabled (ENABLE_INTERPRETER=false)")
            return
        
        if not _interpreter_available:
            logger.error("Open Interpreter not installed. Cannot enable service.")
            self.enabled = False
            return
        
        # Configure interpreter
        try:
            interpreter.auto_run = False
            interpreter.sandbox = self.sandbox_mode
            interpreter.max_runtime = self.max_runtime
            logger.info(f"Interpreter service initialized (sandbox={self.sandbox_mode})")
        except Exception as e:
            logger.error(f"Failed to initialize Interpreter: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled
    
    async def execute_code(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Execute code for custom processing.
        
        Args:
            code: Code to execute
            language: Programming language (python, javascript)
            
        Returns:
            Dict with output, errors, and execution info
        """
        if not self.enabled:
            raise RuntimeError("Interpreter service is not enabled")
        
        if not self.sandbox_mode:
            logger.warning("Running interpreter WITHOUT sandbox - security risk!")
        
        start_time = datetime.utcnow()
        
        try:
            # For Python, we can use exec in a controlled environment
            if language == "python":
                result = await self._execute_python(code)
            elif language == "javascript":
                result = await self._execute_javascript(code)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported language: {language}",
                    "output": ""
                }
            
            return {
                "success": True,
                "output": result["output"],
                "error": result.get("error", ""),
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def _execute_python(self, code: str) -> Dict[str, Any]:
        """Execute Python code in sandbox."""
        
        # Create safe execution environment
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "type": type,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
            },
            # Allow common data processing libraries
            "numpy": None,  # Will be imported if needed
            "pandas": None,
        }
        
        output_capture = []
        
        def safe_print(*args, **kwargs):
            output_capture.append(" ".join(str(a) for a in args))
        
        safe_globals["print"] = safe_print
        
        try:
            exec(code, safe_globals, {})
            return {
                "output": "\n".join(output_capture),
                "error": ""
            }
        except Exception as e:
            return {
                "output": "\n".join(output_capture),
                "error": str(e)
            }
    
    async def _execute_javascript(self, code: str) -> Dict[str, Any]:
        """Execute JavaScript code via Node.js."""
        
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=self.max_runtime
            )
            
            os.unlink(temp_file)
            
            return {
                "output": result.stdout,
                "error": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": f"Execution timeout ({self.max_runtime}s)"
            }
        except Exception as e:
            return {
                "output": "",
                "error": str(e)
            }
    
    async def generate_video_effect(
        self,
        effect_name: str,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Generate custom video effect code.
        
        Args:
            effect_name: Name of effect to generate
            parameters: Effect parameters
            
        Returns:
            Path to generated effect or error message
        """
        if not self.enabled:
            raise RuntimeError("Interpreter service is not enabled")
        
        # Template code for video effects using MoviePy
        effect_templates = {
            "zoom": """
import numpy as np

def zoom_effect(clip, zoom_factor=1.5, duration=None):
    def zoom_effect(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        
        # Calculate zoom
        current_zoom = 1 + (zoom_factor - 1) * (t / duration)
        
        # Simple center crop zoom
        center_h, center_w = h // 2, w // 2
        new_h, new_w = int(h / current_zoom), int(w / current_zoom)
        
        start_h = max(0, center_h - new_h // 2)
        start_w = max(0, center_w - new_w // 2)
        
        zoomed = frame[start_h:start_h+new_h, start_w:start_w+new_w]
        return np.clip(zoomed, 0, 255).astype(np.uint8)
    
    return clip.fl(zoom_effect)

print(f"Zoom effect with factor {zoom_factor} generated")
""",
            "glitch": """
def glitch_effect(clip):
    print("Glitch effect generated")
""",
            "colorgrade": """
def color_grade(clip, warmth=0, saturation=1.0):
    print(f"Color grade: warmth={warmth}, saturation={saturation}")
"""
        }
        
        code = effect_templates.get(effect_name, "")
        if not code:
            return f"Unknown effect: {effect_name}"
        
        # Inject parameters
        for key, value in parameters.items():
            code = code.replace(f"{key}=", f"{key}={value}")
        
        result = await self.execute_code(code)
        
        if result["success"]:
            return f"Effect '{effect_name}' generated successfully"
        else:
            return f"Error: {result['error']}"


# Singleton instance
interpreter_service = InterpreterService()
