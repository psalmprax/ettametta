"""
Interpreter Service - Any Open Interpreter integration
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
import asyncio
import json
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Lazy import
_interpreter_available = False
try:
    from interpreter import interpreter

    _interpreter_available = True
except ImportError:
    logger.warning(
        "Open Interpreter not installed. Install with: pip install open-interpreter"
    )


class InterpreterService:
    """
    Any Open Interpreter for code execution.

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
            logger.info(
                f"Interpreter service initialized (sandbox={self.sandbox_mode})"
            )
        except Exception as e:
            logger.exception(f"Failed to initialize Interpreter: {e}")
            self.enabled = False

    def is_enabled(self) -> bool:
        """Check if service is enabled."""
        return self.enabled

    async def execute_code(self, code: str, language: str = "python") -> dict[str, Any]:
        """
        Execute code for custom processing using subprocess isolation with enhanced security.
        """
        if not self.enabled:
            raise RuntimeError("Interpreter service is not enabled")

        # Enhanced security validation
        security_issues = self._validate_code_security(code, language)
        if security_issues:
            return {
                "success": False,
                "error": f"Security violation: {', '.join(security_issues)}",
                "output": "",
            }

        # Rate limiting check
        if not self._check_rate_limit():
            return {
                "success": False,
                "error": "Rate limit exceeded. Please wait before executing more code.",
                "output": "",
            }

        # Language-specific forbidden patterns
        forbidden_map = {
            "python": [
                "os.",
                "subprocess.",
                "socket.",
                "sys.",
                "eval(",
                "getattr(",
                "__import__",
            ],
            "javascript": [
                "require(",
                "process.",
                "child_process",
                "fs.",
                "eval(",
                "ActiveX",
            ],
        }

        forbidden = forbidden_map.get(language, [])
        for f in forbidden:
            if f in code:
                return {
                    "success": False,
                    "error": f"Forbidden keyword detected in {language}: {f}",
                    "output": "",
                }

        start_time = datetime.now(timezone.utc)

        try:
            if language == "python":
                result = await self._execute_python_sandboxed(code)
            elif language == "javascript":
                result = await self._execute_javascript(code)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported language: {language}",
                    "output": "",
                }

            return {
                "success": True,
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "execution_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
            }

        except Exception as e:
            logger.exception(f"Code execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
            }

    async def _execute_python_sandboxed(self, code: str) -> dict[str, Any]:
        """
        Execute Python code in a separate process for isolation.
        """
        sandbox_script = os.path.join(os.path.dirname(__file__), "sandbox_runner.py")

        try:
            # Pass code and timeout to the runner
            proc = await asyncio.create_subprocess_exec(
                "python3",
                sandbox_script,
                code,
                str(self.max_runtime),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # The runner has its own internal alarm, but we still keep the process communicate timeout
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.max_runtime + 2
            )

            if proc.returncode != 0:
                err_msg = (
                    stderr.decode().strip()
                    or f"Process exited with rc={proc.returncode}"
                )
                return {"output": "", "error": err_msg}

            output = stdout.decode().strip()
            try:
                # Try to find the JSON part of the output (in case of unexpected stdout)
                if "{" in output and "}" in output:
                    json_str = output[output.find("{") : output.rfind("}") + 1]
                    return json.loads(json_str)
                return {"output": output, "error": "Invalid sandbox response format"}
            except json.JSONDecodeError:
                return {"output": output, "error": "Invalid sandbox output format"}

        except asyncio.TimeoutError:
            return {"output": "", "error": f"Execution timeout ({self.max_runtime}s)"}
        except Exception as e:
            return {"output": "", "error": str(e)}

    async def _execute_javascript(self, code: str) -> dict[str, Any]:
        """Execute JavaScript code via Node.js."""
        try:
            # Simple JS sandbox wrapper to restrict globals a bit more
            wrapped_code = f"""
(function() {{
    const forbidden = ['os', 'fs', 'child_process', 'process', 'net', 'http', 'https'];
    const originalRequire = require;
    global.require = function(module) {{
        if (forbidden.includes(module)) {{
            throw new Error('Access to ' + module + ' is forbidden');
        }}
        return originalRequire(module);
    }};
    // Disable process access
    global.process = {{ exit: () => {{}}, env: {{}} }};
    
    {code}
}})();
"""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
                f.write(wrapped_code)
                temp_file = f.name

            result = subprocess.run(
                ["node", "--disallow-code-generation-from-strings", temp_file],
                capture_output=True,
                text=True,
                timeout=self.max_runtime,
            )

            os.unlink(temp_file)
            return {"output": result.stdout, "error": result.stderr}

        except subprocess.TimeoutExpired:
            return {"output": "", "error": f"Execution timeout ({self.max_runtime}s)"}
        except Exception as e:
            return {"output": "", "error": str(e)}

    async def generate_video_effect(
        self, effect_name: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate parameters for custom video effects.
        Refactored to delegate to VideoProcessor instead of generating raw code.
        """
        if not self.enabled:
            raise RuntimeError("Interpreter service is not enabled")

        # Map desired effect to native VideoProcessor methods/params
        effect_mapping = {
            "zoom": {
                "method": "apply_originality_transformation",
                "params": {"zoom": parameters.get("zoom_factor", 1.05)},
            },
            "glitch": {
                "method": "apply_random_glitch",
                "params": {"intensity": parameters.get("intensity", 1.0)},
            },
            "colorgrade": {
                "method": "apply_vibe_adjustments",
                "params": {
                    "visual_mood": parameters.get("mood", "energetic"),
                    "aesthetic_rating": 8,
                },
            },
            "noir": {"method": "apply_grayscale", "params": {}},
        }

        effect_spec = effect_mapping.get(effect_name)
        if not effect_spec:
            return {"success": False, "error": f"Unknown effect: {effect_name}"}

        # Return the specification for the engine to use
        return {
            "success": True,
            "effect": effect_name,
            "instruction": effect_spec,
            "message": f"Effect '{effect_name}' initialized using native engine methods.",
        }

    def _validate_code_security(self, code: str, language: str) -> list[str]:
        """
        Comprehensive security validation for code execution.
        Returns list of security violations found.
        """
        issues = []
        
        # 1. Normalize code for bypass detection (remove whitespace, common separators)
        normalized = "".join(code.split()).replace('"', "").replace("'", "").replace("+", "").lower()

        # Language-specific forbidden patterns
        forbidden_patterns = {
            "python": [
                "os.",
                "subprocess",
                "socket",
                "sys.",
                "eval(",
                "getattr",
                "hasattr",
                "__import__",
                "open(",
                "exec(",
                "compile(",
                "importlib",
                "builtins",
                "globals",
                "locals",
                "vars(",
                "dir(",
                "inspect",
                "pickle",
                "marshal",
                "shelve",
                "__class__",
                "__mro__",
                "__subclasses__",
            ],
            "javascript": [
                "require(",
                "process.",
                "child_process",
                "fs.",
                "eval(",
                "ActiveX",
                "XMLHttpRequest",
                "fetch(",
                "import(",
                "document.",
                "window.",
                "global.",
                "console.",
            ],
        }

        patterns = forbidden_patterns.get(language, [])
        for pattern in patterns:
            # Check raw code
            if pattern in code:
                issues.append(f"forbidden pattern '{pattern}'")
            
            # Check normalized code for obfuscated concatenation (e.g. "o" + "s." + "s" + "ystem")
            # We strip separators for the check
            clean_pattern = pattern.replace(".", "").replace("(", "").replace("__", "").lower()
            if clean_pattern and clean_pattern in normalized:
                 # Only add if not already caught by raw check to avoid duplicates
                 if f"obfuscated {clean_pattern}" not in [i.split("'")[1] if "'" in i else i for i in issues]:
                    issues.append(f"possible obfuscated {pattern}")

        # Length limits
        if len(code) > 10000:
            issues.append("code too long (>10KB)")
        if len(code.split("\n")) > 100:
            issues.append("too many lines (>100)")

        # Suspicious shell patterns
        suspicious = ["rm ", "del ", "format(", "delete", "drop table", "truncate", "sh ", "bash "]
        for pattern in suspicious:
            if pattern.lower() in code.lower():
                issues.append(f"suspicious pattern '{pattern}'")

        return issues

    def _check_rate_limit(self) -> bool:
        """
        Rate limiting for code execution to prevent abuse.
        """
        import time

        current_time = time.time()

        if not hasattr(self, "_execution_times"):
            self._execution_times = []

        # Clean old entries (keep last 10 minutes)
        self._execution_times = [
            t for t in self._execution_times if current_time - t < 600
        ]

        # Allow max 10 executions per 10 minutes
        if len(self._execution_times) >= 10:
            return False

        self._execution_times.append(current_time)
        return True


# Singleton instance
interpreter_service = InterpreterService()
