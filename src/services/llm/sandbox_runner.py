#!/usr/bin/env python3
"""
Secure Sandbox Runner - AST-Based Validation & Docker Isolation
============================================================
Replaces unsafe regex validation with AST parsing for 'Elite' tier security.
Supports Docker isolation with subprocess fallback.
"""

import sys
import json
import os
import tempfile
import subprocess
import ast
import shutil
from typing import Any

# Blocked modules that should NEVER be imported or used
BLOCKED_MODULES = {
    "os", "subprocess", "sys", "shutil", "socket", "requests", "urllib",
    "http", "ftplib", "telnetlib", "pty", "tty", "termios", "fcntl",
    "resource", "pwd", "grp", "crypt", "spwd", "posix", "threading", 
    "multiprocessing", "importlib", "builtins"
}

# Forbidden function calls for security
FORBIDDEN_CALLS = {
    "exec", "eval", "compile", "__import__", "open", "getattr", "setattr",
    "delattr", "hasattr", "globals", "locals", "vars", "breakpoint", "help"
}

class SecurityTransformer(ast.NodeVisitor):
    """
    AST Walker to detect malicious patterns that regex might miss.
    """
    def __init__(self):
        self.errors = []

    def visit_Import(self, node):
        for name in node.names:
            if name.name.split('.')[0] in BLOCKED_MODULES:
                self.errors.append(f"Forbidden import: {name.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split('.')[0] in BLOCKED_MODULES:
            self.errors.append(f"Forbidden import from: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                self.errors.append(f"Forbidden function call: {node.func.id}()")
        elif isinstance(node.func, ast.Attribute):
            # Block suspicious attribute access like os.system
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in BLOCKED_MODULES:
                    self.errors.append(f"Forbidden module access: {node.func.value.id}.{node.func.attr}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Prevent access to dunder methods/attributes
        if node.attr.startswith("__") and node.attr != "__init__":
            self.errors.append(f"Forbidden attribute access: {node.attr}")
        self.generic_visit(node)

def validate_code(code: str) -> tuple[bool, str]:
    """
    Performs 'Elite' tier security validation using AST.
    """
    try:
        tree = ast.parse(code)
        transformer = SecurityTransformer()
        transformer.visit(tree)
        
        if transformer.errors:
            return False, "; ".join(transformer.errors)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax Error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Validation Error: {str(e)}"

def run_subprocess(code: str, timeout: int = 30) -> dict[str, Any]:
    """Fallback runner if Docker is unavailable."""
    is_safe, reason = validate_code(code)
    if not is_safe:
        return {"success": False, "output": "", "error": reason, "blocked": True}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code + "\n")
        temp_path = f.name

    try:
        env = os.environ.copy()
        env.update({"PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        for key in ["PYTHONPATH", "LD_PRELOAD", "LD_LIBRARY_PATH"]:
            env.pop(key, None)

        result = subprocess.run(
            [sys.executable, "-u", temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd="/tmp"
        )
        
        os.unlink(temp_path)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        os.unlink(temp_path)
        return {"success": False, "output": "", "error": f"Execution timeout ({timeout}s)"}
    except Exception as e:
        if os.path.exists(temp_path): os.unlink(temp_path)
        return {"success": False, "output": "", "error": str(e)}

def run_docker(code: str, timeout: int = 30) -> dict[str, Any]:
    """Preferred Docker-based sandbox isolation."""
    DOCKER_IMAGE = "ettametta-sandbox"
    
    if not shutil.which("docker"):
        return {"success": False, "error": "Docker not available", "fallback": True}

    is_safe, reason = validate_code(code)
    if not is_safe:
        return {"success": False, "output": "", "error": reason, "blocked": True}

    try:
        # Run container with heavy restrictions
        result = subprocess.run(
            [
                "docker", "run", "--rm", "--network", "none",
                "--memory", "256m", "--cpus", "0.5",
                "--pids-limit", "50", "--read-only",
                "--tmpfs", "/tmp:rw,size=64m",
                "-i", DOCKER_IMAGE
            ],
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Container timeout ({timeout}s)"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e), "fallback": True}

def run_sandboxed(code: str, timeout: int = 30) -> dict[str, Any]:
    """Main entry point for secure code execution."""
    docker_enabled = os.getenv("SANDBOX_DOCKER", "true").lower() == "true"
    
    if docker_enabled:
        result = run_docker(code, timeout)
        if not result.get("fallback"):
            return result
            
    return run_subprocess(code, timeout)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No code provided"}))
        sys.exit(1)

    code_input = sys.argv[1]
    timeout_input = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(json.dumps(run_sandboxed(code_input, timeout_input)))
