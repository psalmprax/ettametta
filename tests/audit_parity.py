import os
import re
from pathlib import Path

backend_dir = Path("src/api/routes")
frontend_dir = Path("apps/dashboard/src/app")

def get_backend_routes():
    routes = {}
    for file in backend_dir.glob("*.py"):
        with open(file, "r") as f:
            content = f.read()
            # Look for @router.post("/...") and @router.get("/...")
            matches = re.findall(r'@router\.(post|get|delete|put)\("([^"]+)"', content)
            prefix_match = re.search(r'router = APIRouter\(prefix="([^"]+)"', content)
            prefix = prefix_match.group(1) if prefix_match else ""
            
            for method, path in matches:
                full_path = f"{prefix}{path}"
                routes[full_path] = {
                    "method": method.upper(),
                    "file": str(file)
                }
    return routes

def get_frontend_calls():
    calls = set()
    for file in frontend_dir.rglob("*.tsx"):
        with open(file, "r") as f:
            content = f.read()
            # Look for fetch(`${API_BASE}/...`)
            matches = re.findall(r'fetch\(`\$\{API_BASE\}([^`]+)`', content)
            for path in matches:
                # Clean up variables in path like ${id}
                clean_path = re.sub(r'\$\{([^}]+)\}', '*', path)
                # Remove query params
                clean_path = clean_path.split("?")[0]
                calls.add(clean_path)
    return calls

if __name__ == "__main__":
    backend_routes = get_backend_routes()
    frontend_calls = get_frontend_calls()

    print(f"Total Backend Routes: {len(backend_routes)}")
    print(f"Total Unique Frontend API Calls: {len(frontend_calls)}")

    print("\n--- Orphaned Backend Routes (Unused in Frontend) ---")
    for route in sorted(backend_routes.keys()):
        # Check if route is in calls (handling path variables)
        is_used = False
        for call in frontend_calls:
            # Simple check: if backend route has a placeholder like {job_id}, we match it with *
            pattern = re.sub(r'\{[^}]+\}', '*', route)
            if pattern == call:
                is_used = True
                break
        
        if not is_used:
            print(f"[{backend_routes[route]['method']}] {route} ({backend_routes[route]['file']})")

    print("\n--- Missing Backend Routes (Frontend calls non-existent routes) ---")
    for call in sorted(frontend_calls):
        found = False
        for route in backend_routes.keys():
            pattern = re.sub(r'\{[^}]+\}', '*', route)
            if pattern == call:
                found = True
                break
        if not found:
            print(f"{call}")
