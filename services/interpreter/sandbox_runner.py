import sys
import json
import traceback
import io
import signal

def run_sandboxed(code, timeout=30):
    # Setup internal alarm for timeout enforcement
    def handler(signum, frame):
        raise TimeoutError(f"Execution exceeded internal sandbox limit of {timeout}s")
    
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)

    try:
        # Setup restricted globals
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
        # You can add common math/data libs here if needed, but not os/sys/subprocess
    }

    # Capture output
    output_buffer = io.StringIO()
    
    def sandboxed_print(*args, **kwargs):
        kwargs["file"] = output_buffer
        print(*args, **kwargs)

    safe_globals["print"] = sandboxed_print

    try:
        # Execute code
        exec(code, safe_globals, {})
        signal.alarm(0) # Disable alarm
        return {
            "success": True,
            "output": output_buffer.getvalue(),
            "error": ""
        }
    except Exception as e:
        signal.alarm(0) # Disable alarm
        return {
            "success": False,
            "output": output_buffer.getvalue(),
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No code provided"}))
        sys.exit(1)
    
    code_to_run = sys.argv[1]
    timeout_val = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    result = run_sandboxed(code_to_run, timeout=timeout_val)
    print(json.dumps(result))
