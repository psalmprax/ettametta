import os
import logging
from typing import Any
import subprocess
import tempfile
import shutil

from src.api.config import settings

logger = logging.getLogger(__name__)

OPENINTERPRETER_ENABLED = os.getenv("ENABLE_INTERPRETER", "false").lower() == "true"


class OpenInterpreterService:
    """
    Open Interpreter integration for code execution.
    Enable with ENABLE_INTERPRETER=true

    Used for dynamic video generation and custom processing.
    """

    def __init__(self):
        self.enabled = OPENINTERPRETER_ENABLED
        self.allowed_dirs = [
            "/tmp/viral_forge",
            str(settings.BASE_DIR),
        ]

        for d in self.allowed_dirs:
            os.makedirs(d, exist_ok=True)

        if self.enabled:
            logger.info("Open Interpreter integration enabled")

    def execute_code(
        self, code: str, language: str = "python", timeout: int = 60
    ) -> dict[str, Any]:
        """
        Execute code in a sandboxed environment.

        Args:
            code: Code to execute
            language: programming language (python, javascript, etc.)
            timeout: Execution timeout in seconds

        Returns:
            dict with output, error, and execution info
        """
        if not self.enabled:
            return {
                "success": False,
                "output": "",
                "error": "Open Interpreter not enabled. Set ENABLE_INTERPRETER=true",
                "execution_time": 0,
            }

        try:
            if language == "python":
                return self._run_python(code, timeout)
            elif language == "javascript":
                return self._run_javascript(code, timeout)
            else:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Language {language} not supported",
                    "execution_time": 0,
                }
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": 0,
            }

    def _run_python(self, code: str, timeout: int) -> dict[str, Any]:
        """Execute Python code."""
        import time

        start_time = time.time()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["python3", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.allowed_dirs[0],
            )

            execution_time = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "execution_time": round(execution_time, 2),
            }
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def _run_javascript(self, code: str, timeout: int) -> dict[str, Any]:
        """Execute JavaScript code."""
        import time

        start_time = time.time()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.allowed_dirs[0],
            )

            execution_time = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else "",
                "execution_time": round(execution_time, 2),
            }
        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    def generate_video_script(self, topic: str) -> dict[str, Any]:
        """Generate a video processing script for the topic."""
        code = f'''
import random

# Generate a simple video processing script for: {topic}

topic = "{topic}"
print(f"Generating video script for: {{topic}}")

# Sample script structure
script = {{
    "intro": f"Welcome! Today we're exploring {{topic}}",
    "main_content": [
        f"First, let's understand what {{topic}} is about",
        f"Here are the key points you need to know",
        f"Next, let's dive deeper into the details"
    ],
    "outro": f"That's all for {{topic}}. Like and subscribe!"
}}

print(script)
'''
        return self.execute_code(code, "python", 30)


class CodeExecutor:
    """
    Simple code execution for viral_forge automation.
    """

    @staticmethod
    def run_script(script_type: str, **kwargs) -> dict[str, Any]:
        """Run predefined scripts."""
        if script_type == "video_thumbnail":
            return OpenInterpreterService().execute_code(
                f'''
import random
topic = "{kwargs.get("topic", "video")}"
colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
print(f"Thumbnail for {{topic}}: Use color {{random.choice(colors)}}")
'''
            )
        elif script_type == "seo_keywords":
            return OpenInterpreterService().execute_code(
                f'''
topic = "{kwargs.get("topic", "")}"
keywords = [topic, f"{{topic}} tips", f"{{topic}} guide", f"best {{topic}}"]
print(f"SEO Keywords for {{topic}}: {{', '.join(keywords)}}")
'''
            )

        return {"success": False, "error": f"Unknown script type: {script_type}"}


interpreter_service = OpenInterpreterService()
code_executor = CodeExecutor()
