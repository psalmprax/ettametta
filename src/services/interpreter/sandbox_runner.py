#!/usr/bin/env python3
"""
Secure Sandbox Runner - Subprocess-Based Isolation
================================================
Replaces unsafe exec() with proper subprocess execution.
Uses restricted environment and resource limits.
"""

import sys
import json
import os
import tempfile
import subprocess
import threading
import time
import shutil
import re
from pathlib import Path

# Paths that are BLOCKED from user code
BLOCKED_IMPORTS = [
    "os",  # File system access
    "subprocess",  # Command execution
    "sys",  # System info
    "shutil",  # File operations
    "socket",  # Network
    "requests",  # HTTP
    "urllib",  # Network
    "http",  # Network
    "ftplib",  # Network
    "telnetlib",  # Network
    "pty",  # Pseudo terminals
    "tty",  # Terminal
    "termios",  # Terminal
    "fcntl",  # File control
    "resource",  # Resource limits (would allow raising them)
    "pwd",  # Password database
    "grp",  # Group database
    "crypt",  # Password hashing
    "spwd",  # Shadow password
    "grp",  # Groups
]

# Blocked file paths for open()
BLOCKED_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/group",
    "/.ssh/",
    "/.aws/",
    ".env",
    "key",
    "password",
    "secret",
    " credential",
    "~/.bashrc",
    "~/.profile",
    "~/.bash_history",
]

# Blocked commands/patterns in code
BLOCKED_PATTERNS = [
    r"import\s+(os|subprocess|sys|socket|requests|urllib)",
    r"from\s+(os|subprocess|sys|socket)",
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__\s*\(",
    r"compile\s*\(",
    r"open\s*\([^)]",  # open() - restricted separately
    r"subprocess\.run",
    r"subprocess\.call",
    r"subprocess\.Popen",
    r"os\.system",
    r"os\.popen",
    r"os\.spawn",
    r"shell\s*=",
    r"\.write\(",
    r"\.read\(",
]


def validate_code(code: str) -> tuple[bool, str]:
    """
    Static analysis of code before execution.
    Returns (is_safe, reason).
    """
    # Check for blocked imports
    for blocked in BLOCKED_IMPORTS:
        pattern = rf"^\s*(import\s+{blocked}|from\s+{blocked}\s+import)"
        if re.search(pattern, code, re.MULTILINE):
            return False, f"Blocked import: {blocked}"

    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return False, f"Blocked pattern detected: {pattern}"

    # Check for suspicious open() calls
    if "open(" in code:
        # Extract paths from open() calls
        path_matches = re.findall(r'open\s*\(\s*["\']([^"\']+)["\']', code)
        for path in path_matches:
            for blocked in BLOCKED_PATHS:
                if blocked.lower() in path.lower():
                    return False, f"Blocked file path: {path}"

    return True, ""


def run_subprocess(code: str, timeout: int = 30) -> dict:
    """
    Execute code in a restricted subprocess.
    Returns {"success": bool, "output": str, "error": str}.
    """
    # Validate first
    is_safe, reason = validate_code(code)
    if not is_safe:
        return {"success": False, "output": "", "error": reason, "blocked": True}

    # Create temp file - code runs directly, output captured via subprocess
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code + "\n")
        f.flush()
        temp_path = f.name

    # Restrict environment
    env = os.environ.copy()
    env.update(
        {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            # Disable bytecode
        }
    )

    # Remove potentially dangerous env vars
    for key in ["PYTHONPATH", "LD_PRELOAD", "LD_LIBRARY_PATH"]:
        env.pop(key, None)

    try:
        # Try to use resource limits on Unix
        try:
            import resource

            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            # 256MB max memory
            resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, hard))
            use_limits = True
        except (ImportError, ValueError):
            use_limits = False

        # Run with subprocess
        result = subprocess.run(
            [sys.executable, "-u", temp_path],  # -u for unbuffered
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd="/tmp",  # Don't run in app directory
            # Restrict file creation
        )

        # Cleanup
        os.unlink(temp_path)

        if result.returncode == 0:
            output = result.stdout + result.stderr
            return {"success": True, "output": output, "error": ""}
        else:
            return {"success": False, "output": result.stdout, "error": result.stderr}

    except subprocess.TimeoutExpired:
        os.unlink(temp_path)
        return {
            "success": False,
            "output": "",
            "error": f"Execution timeout ({timeout}s)",
        }
    except Exception as e:
        try:
            os.unlink(temp_path)
        except:
            pass
        return {"success": False, "output": "", "error": str(e)}


# Docker configuration
DOCKER_IMAGE = "ettametta-sandbox"
DOCKER_ENABLED = os.getenv("SANDBOX_DOCKER", "true").lower() == "true"


def run_docker(code: str, timeout: int = 30) -> dict:
    """
    Run code inside Docker container (preferred).
    Falls back to subprocess if Docker unavailable.
    """
    try:
        # Check docker availability
        if not shutil.which("docker"):
            return {
                "success": False,
                "output": "",
                "error": "Docker not available",
                "fallback": True,
            }

        # Validate code first
        is_safe, reason = validate_code(code)
        if not is_safe:
            return {"success": False, "output": "", "error": reason, "blocked": True}

        # Pull image if needed (silent)
        try:
            subprocess.run(
                ["docker", "pull", DOCKER_IMAGE],
                capture_output=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": "",
                "error": f"Docker pull failed: {e}",
                "fallback": True,
            }

        # Run container with restrictions
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",  # No network
                "--memory",
                "256m",  # 256MB max
                "--cpus",
                "0.5",  # Half CPU
                "--pids-limit",
                "50",  # Max processes
                "--read-only",  # Read-only except /tmp
                "--tmpfs",
                "/tmp:rw,size=64m",  # Writable /tmp
                "-i",  # Interactive
                DOCKER_IMAGE,
            ],
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # Parse JSON output
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Timeout ({timeout}s)"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "fallback": True}


def run_sandboxed(code: str, timeout: int = 30) -> dict:
    """
    Main entry point - runs code with Docker or subprocess.
    Tries Docker first (more secure), falls back to subprocess.
    """
    # Try Docker if enabled
    if DOCKER_ENABLED:
        result = run_docker(code, timeout)
        if not result.get("fallback"):
            return result

    # Fallback to subprocess
    return run_subprocess(code, timeout)


# CLI entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No code provided"}))
        sys.exit(1)

    code_to_run = sys.argv[1]
    timeout_val = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    result = run_sandboxed(code_to_run, timeout=timeout_val)
    print(json.dumps(result))
