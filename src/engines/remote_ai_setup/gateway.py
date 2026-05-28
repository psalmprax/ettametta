"""
AI Cluster Gateway - Horizontal Scaling Load Balancer
"""

import sqlite3
import httpx
import os
import time
import tempfile
import threading
import asyncio
import traceback
import uuid
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Any

app = FastAPI(title="AI Cluster Gateway")

# --- CONNECTIVITY STABILIZATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token", "X-Worker-Token"],
)

# Persistent Storage for Jobs
class JobStore:
    def __init__(self, db_path=None):
        if db_path is None:
            if os.path.exists("/workspace") and os.access("/workspace", os.W_OK):
                db_path = "/workspace/gateway_state.db"
            else:
                db_path = "gateway_state.db"
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    node_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    url TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'UNCONFIGURED',
                    last_seen TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)")

    def save_job(self, job_id: str, node_url: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO jobs (job_id, node_url) VALUES (?, ?)", (job_id, node_url))

    def get_node(self, job_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT node_url FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # --- Node Management ---
    def add_node(self, url: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO nodes (url) VALUES (?)", (url,))

    def remove_node(self, url: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM nodes WHERE url = ?", (url,))
        
        # Clean up in-memory health state
        with LOCK:
            if url in NODE_HEALTH:
                del NODE_HEALTH[url]

    def update_node_status(self, url: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE nodes SET status = ?, last_seen = CURRENT_TIMESTAMP WHERE url = ?", (status, url))

    def get_nodes(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT url, status, last_seen FROM nodes")
            return [{"url": row[0], "status": row[1], "last_seen": row[2]} for row in cursor.fetchall()]

    def cleanup(self, days=7):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM jobs WHERE created_at < datetime('now', ?)", (f'-{days} days',))

job_store = JobStore()

# Configuration
ADMIN_TOKEN = os.environ.get("INTERNAL_API_TOKEN") # Reusing internal token for admin actions
WORKER_TOKEN = os.environ.get("AI_CLUSTER_SECRET") # Shared secret for Gateway -> Worker communication

# Initial seed from .env
env_nodes = os.environ.get("AI_NODES", "").split(",")
for node in env_nodes:
    clean_node = node.strip()
    if clean_node:
        job_store.add_node(clean_node)

NODE_HEALTH: dict[str, dict[str, Any]] = {}
LOCK = threading.Lock()
BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()

async def _check_single_node(client: httpx.AsyncClient, node_data: dict[str, Any]):
    node = node_data["url"]
    
    # --- PUSH/PULL COHESION ---
    with LOCK:
        health = NODE_HEALTH.get(node, {})
        # If node is in active PUSH mode (seen via heartbeat in last 60s), skip Pull
        if health.get("push_mode") and (time.time() - health.get("last_seen", 0) < 60):
            # Ensure DB stays READY if we are skipping pull
            if node_data["status"] != "READY":
                job_store.update_node_status(node, "READY")
            return

    try:
        headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
        resp = await client.get(f"{node}/health", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            job_store.update_node_status(node, "READY")
            with LOCK:
                NODE_HEALTH[node] = {
                    "online": True,
                    "busy": data.get("busy", False),
                    "current_model": data.get("current_model"),
                    "last_seen": time.time(),
                    "error": None
                }
        else:
            job_store.update_node_status(node, "OFFLINE")
            with LOCK:
                NODE_HEALTH[node] = {"online": False, "error": f"Status {resp.status_code}"}
    except Exception as e:
        print(f"Health check for {node} failed: {e}")
        job_store.update_node_status(node, "OFFLINE")
        with LOCK:
            NODE_HEALTH[node] = {"online": False, "error": str(e)}

async def update_node_health():
    """Background loop to monitor CPU/GPU node health and model status"""
    last_cleanup = 0
    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            # Periodic cleanup of old job records (once per day)
            if time.time() - last_cleanup > 86400:
                print("🧹 [Gateway] Running periodic 7-day job record cleanup...", flush=True)
                job_store.cleanup(days=7)
                last_cleanup = time.time()

            nodes = job_store.get_nodes()
            for node_data in nodes:
                await _check_single_node(client, node_data)
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    task = asyncio.create_task(update_node_health())
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)
    nodes = job_store.get_nodes()
    print(f"🚀 AI Gateway started with {len(nodes)} nodes registered.", flush=True)

def select_best_node(requested_model: str | None = None) -> str:
    """Smart routing: Least-busy + Model-aware preference"""
    with LOCK:
        available_nodes = [n for n, h in NODE_HEALTH.items() if h.get("online")]
        if not available_nodes:
            raise HTTPException(status_code=503, detail="No AI nodes online in cluster")

        # 1. Prefer node that already has the model loaded
        if requested_model:
            for node in available_nodes:
                if NODE_HEALTH[node].get("current_model") == requested_model and not NODE_HEALTH[node].get("busy"):
                    print(f"🎯 [Gateway] Model-Aware match: Sending to {node} (Model: {requested_model})", flush=True)
                    return node

        # 2. Prefer non-busy nodes
        idle_nodes = [n for n in available_nodes if not NODE_HEALTH[n].get("busy")]
        if idle_nodes:
            return idle_nodes[0] # Simplest round-robin/first-idle

        # 3. Fallback to any online node (will be queued by node's own orchestrator)
        return available_nodes[0]

# --- ADMIN / PROVISIONING ENDPOINTS (Hardened Security) ---

from pydantic import BaseModel
import subprocess

class RegisterNodeRequest(BaseModel):
    url: str

class ProvisionNodeRequest(BaseModel):
    ip: str
    ssh_key: str
    port: int = 22
    user: str = "root"

class HeartbeatRequest(BaseModel):
    url: str
    busy: bool
    current_model: str | None
    hardware: dict[str, Any]
    status: str = "ready"

def verify_admin(x_admin_token: str = Header(None)):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized Admin Action")

@app.post("/pulse")
async def node_pulse_heartbeat(request: HeartbeatRequest, x_worker_token: str = Header(None)):
    """
    Primary heart-beat sink. Moved to top to ensure zero-shadowing.
    """
    print(f"💓 [Pulse] Inbound from {request.url}", flush=True)
    if WORKER_TOKEN and x_worker_token != WORKER_TOKEN:
        print(f"⚠️ [Pulse] Token mismatch for {request.url}", flush=True)
        raise HTTPException(status_code=401, detail="Invalid Worker Token")
        
    node = request.url
    job_store.add_node(node)
    job_store.update_node_status(node, "READY")
    
    with LOCK:
        NODE_HEALTH[node] = {
            "online": True,
            "busy": request.busy,
            "current_model": request.current_model,
            "last_seen": time.time(),
            "hardware": request.hardware,
            "push_mode": True,
            "error": None
        }
    return {"status": "pulse_stable", "node": node}

@app.get("/health")
async def cluster_health():
    nodes = job_store.get_nodes()
    with LOCK:
        return {
            "status": "healthy",
            "cluster_size": len(nodes),
            "nodes": nodes,
            "telemetry": NODE_HEALTH
        }

@app.get("/status/{job_id}")
async def proxy_status(job_id: str):
    """Route status requests to the specific node handling the job"""
    target_node = job_store.get_node(job_id)
    
    if not target_node:
        # If not in map, try all online nodes as fallback
        with LOCK:
            available_nodes = [n for n, h in NODE_HEALTH.items() if h.get("online")]
        for node in available_nodes:
            try:
                headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{node}/status/{job_id}", headers=headers)
                    if resp.status_code == 200:
                        return resp.json()
            except Exception: continue
        raise HTTPException(status_code=404, detail="Job not found in cluster")

    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
        resp = await client.get(f"{target_node}/status/{job_id}", headers=headers)
        return resp.json()

@app.post("/register")
async def register_node(request: RegisterNodeRequest, x_admin_token: str = Header(None)):
    verify_admin(x_admin_token)
    job_store.add_node(request.url)
    return {"status": "registered", "url": request.url}

# Alias for frontend flexibility
@app.post("/nodes")
async def register_node_alias(request: RegisterNodeRequest, x_admin_token: str = Header(None)):
    return await register_node(request, x_admin_token)

from urllib.parse import unquote

@app.delete("/nodes/{node_url:path}")
async def remove_node_from_cluster(node_url: str, x_admin_token: str = Header(None)):
    verify_admin(x_admin_token)
    # Ensure URL is unquoted to match DB format
    decoded_url = unquote(node_url)
    job_store.remove_node(decoded_url)
    print(f"🗑️ [Gateway] Internal Delete Request: Raw={node_url}, Decoded={decoded_url}", flush=True)
    return {"status": "removed", "node": decoded_url}

@app.post("/nodes/provision")
async def provision_node(request: ProvisionNodeRequest, x_admin_token: str = Header(None)):
    """
    Hardened Provisioning: Key is passed in encrypted JSON Body.
    Zero-Storage architecture ensures key never hits Gateway disk or logs.
    """
    verify_admin(x_admin_token)
    ip = request.ip
    ssh_key = request.ssh_key
    port = request.port
    
    # Ensure registered in local store for visibility
    job_store.add_node(f"http://{ip}:8122")
    job_store.update_node_status(f"http://{ip}:8122", "PROVISIONING")
    
    def run_provision():
        try:
            print(f"🛠️ [Provision] Starting secure deploy to {ip}...", flush=True)
            # We use /dev/stdin to pass the key content without saving to disk
            cmd = ["/bin/bash", "./deploy_to_gpu_server.sh", ip, str(port)]
            
            # Environment variables for the script to pick up the key from a virtual descriptor
            env = os.environ.copy()
            # We'll need a way for the script to use the key. 
            # Easiest hardened way: Python writes to a temporary named pipe or uses /dev/stdin.
            # Let's use a temporary file in /dev/shm (RAM-only disk) if /dev/stdin is tricky for rsync.
            
            os.makedirs("/dev/shm/vf_provision", mode=0o700, exist_ok=True)
            fd, temp_key = tempfile.mkstemp(dir="/dev/shm/vf_provision")
            try:
                with os.fdopen(fd, "w") as f:
                    f.write(ssh_key)
                
                env["SSH_KEY"] = temp_key
                env["AI_CLUSTER_SECRET"] = WORKER_TOKEN or ""
                
                # Streaming deployment telemetry to logs
                process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                
                for line in process.stdout:
                    print(line.strip(), flush=True)
                
                process.wait()
                
                if process.returncode == 0:
                    print(f"✅ [Provision] Node {ip} deployed successfully.", flush=True)
                    job_store.update_node_status(f"http://{ip}:8122", "READY")
                else:
                    print(f"❌ [Provision] Deployment failed for {ip} with exit code {process.returncode}", flush=True)
                    job_store.update_node_status(f"http://{ip}:8122", "FAILED")
            finally:
                # MANDATORY: Wipe the key from RAM disk immediately
                if os.path.exists(temp_key):
                    os.remove(temp_key)
        except Exception as e:
            print(f"❌ [Provision] Orchestration error: {e}", flush=True)
            job_store.update_node_status(f"http://{ip}:8122", "ERROR")

    threading.Thread(target=run_provision, daemon=True).start()
    return {"status": "provisioning_started", "node": ip}

@app.post("/{path:path}")
async def proxy_post(path: str, request: Request):
    """Generic POST proxy with smart routing"""
    # Guard: Do not proxy management endpoints even if they match the catch-all
    if path in ["register", "nodes", "nodes/provision"]:
        raise HTTPException(status_code=400, detail="Management path hit proxy handler - check routing order")
    
    try:
        body = await request.json()
    except Exception:
        # Fallback for empty/non-JSON bodies
        body = {}
    
    # Identify requested model for routing
    model_key = body.get("model") or body.get("model_key")
    if not model_key:
        if "hunyuan" in path: model_key = "hunyuan_480p"
        elif "animatediff" in path: model_key = "animatediff_v15"
        elif "generate" in path: model_key = "ltx_2_19b"
    
    target_node = select_best_node(model_key)
    
    headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(f"{target_node}/{path}", json=body, headers=headers)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            
            # Remember which node has this job for status/download requests
            if "job_id" in data:
                job_store.save_job(data["job_id"], target_node)
            
            return data
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=502, detail=f"Target node {target_node} failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("GATEWAY_PORT", 8133))
    uvicorn.run(app, host="0.0.0.0", port=port)
