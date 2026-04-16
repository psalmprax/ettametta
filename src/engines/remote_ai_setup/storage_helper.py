import os
import shutil
import sys

def find_best_storage():
    """
    Identifies the largest writable partition from common GPU server mount points.
    Returns the root path of the best storage location.
    """
    # Common mount points for specialized GPU storage (RunPod, Lambda, AutoDL, etc.)
    candidates = [
        "/workspace", 
        "/mnt/data", 
        "/data", 
        "/mnt/workspace",
        "/storage",
        os.path.expanduser("~") # Home directory as fallback
    ]
    
    best_path = "/"
    max_free = 0
    
    # Check candidates for max free space
    for path in candidates:
        if os.path.exists(path) and os.access(path, os.W_OK):
            try:
                usage = shutil.disk_usage(path)
                if usage.free > max_free:
                    max_free = usage.free
                    best_path = path
            except Exception:
                continue
    
    # Standardize result: ensure absolute path and no trailing slash
    final_path = os.path.abspath(best_path).rstrip('/')
    return final_path

if __name__ == "__main__":
    best_storage = find_best_storage()
    # Output only the path for easy shell consumption
    print(best_storage)
