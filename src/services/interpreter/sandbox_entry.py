#!/usr/bin/env python3
"""
Sandbox Entry Point - Runs inside Docker container
===================================
Receives code via stdin, executes safely, returns JSON to stdout.
"""

import sys
import json
import io
import traceback

# Capture stdout
old_stdout = sys.stdout
sys.stdout = io.StringIO()

# Blocked modules (defense in depth)
BLOCKED_MODULES = frozenset(
    [
        "os",
        "sys",
        "subprocess",
        "socket",
        " threading",
        "multiprocessing",
        "requests",
        "urllib",
        "http",
        "ftplib",
        "telnetlib",
        "pty",
        "tty",
        "termios",
        "fcntl",
        "resource",
        "pwd",
        "grp",
        "crypt",
        "spwd",
    ]
)


def execute(code: str) -> dict:
    """Execute code in restricted environment."""
    try:
        # Execute in restricted globals
        restricted_globals = {
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
                "zip": zip,
                "map": map,
                "filter": sorted,
                "min": min,
                "max": max,
                "sum": sum,
                "abs": abs,
                "round": round,
                "enumerate": enumerate,
                "isinstance": isinstance,
                "type": type,
            }
        }

        # Add safe builtins
        restricted_builtins["__builtins__"]["print"] = lambda *args, **kwargs: print(
            *args, **kwargs
        )

        # Execute
        exec(code, restricted_globals, {})

        output = sys.stdout.getvalue()
        return {"success": True, "output": output, "error": ""}

    except Exception as e:
        return {"success": False, "output": sys.stdout.getvalue(), "error": str(e)}


if __name__ == "__main__":
    # Read code from stdin
    code = sys.stdin.read()

    result = execute(code)
    print(json.dumps(result), file=old_stdout)
