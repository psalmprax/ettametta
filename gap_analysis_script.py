import os
import re
import glob
from collections import defaultdict

FRONTEND_DIR = "apps/dashboard/src"
BACKEND_DIR = "api/routes"

def get_backend_endpoints():
    endpoints = []
    # Match @router.get("/path"), @router.post("/path"), etc.
    pattern = re.compile(r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']')
    for root, _, files in os.walk(BACKEND_DIR):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for method, path in matches:
                        # Normalize path
                        base_path = path.split('{')[0].rstrip('/')
                        if not base_path:
                            base_path = '/'
                        endpoints.append({'method': method.upper(), 'path': path, 'base_path': base_path, 'file': file})
    return endpoints

def get_frontend_api_calls():
    calls = []
    # Match fetch(`...`) or axios.get(`...`) or similar
    pattern = re.compile(r'fetch\(\s*[`\'"](?:.*?\$\{API_BASE\}|API_BASE)[^\`\'"]*([^\`\'"?]+)[^\`\'"]*[`\'"]')
    # Also find withRealFallback calls
    fallback_pattern = re.compile(r'withRealFallback')
    for root, _, files in os.walk(FRONTEND_DIR):
        for file in files:
            if file.endswith(".tsx") or file.endswith(".ts"):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for match in matches:
                        calls.append({'path': match, 'file': file})
    return calls

def get_frontend_dummies():
    dummies = []
    # Look for onClick that just console logs or alert or has 'TODO' or 'Not implemented'
    pattern = re.compile(r'onClick=\{.*?(?:console\.log|alert|TODO|Not implemented).*?\}', re.DOTALL)
    for root, _, files in os.walk(FRONTEND_DIR):
        for file in files:
            if file.endswith(".tsx"):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for match in matches:
                        # limit length to avoid massive output
                        match_str = match.strip()[:100]
                        if len(match.strip()) > 100: match_str += "..."
                        dummies.append({'file': file, 'match': match_str})
    return dummies

backend = get_backend_endpoints()
frontend_calls = get_frontend_api_calls()
frontend_dummies = get_frontend_dummies()

print("==== BACKEND ENDPOINTS (Total: {}) ====".format(len(backend)))
# print([f"{e['method']} {e['path']}" for e in backend][:10]) # Too long to print all, just summaries later

backend_paths = set([e['base_path'] for e in backend])
frontend_paths = set()
for c in frontend_calls:
    # try to extract base path
    path = c['path']
    base = path.split('?')[0].split('$')[0].rstrip('/')
    if not base: base = '/'
    frontend_paths.add(base)

print("\n==== UNCOVERED BACKEND ENDPOINTS (No obvious frontend call) ====")
uncovered_backend = []
for b in backend:
    if not any(b['base_path'] in f for f in frontend_paths):
        uncovered_backend.append(f"{b['method']} {b['path']} (in {b['file']})")

for ub in uncovered_backend:
    print(ub)

print("\n==== DUMMY UI CLICKABLES ====")
for d in frontend_dummies:
    print(f"{d['file']}: {d['match']}")

print("\n==== FRONTEND CALLS TO NON-EXISTENT ENDPOINTS ====")
uncovered_frontend = []
for f in frontend_paths:
    if not any(f in b for b in backend_paths):
        uncovered_frontend.append(f)
for uf in uncovered_frontend:
    print(uf)

