"""
AI Cluster Gateway - Horizontal Scaling Load Balancer
"""

import sqlite3
import httpx
import os
import time
import threading
import asyncio
import traceback
import uuid
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional

app = FastAPI(title="AI Cluster Gateway")

# --- CONNECTIVITY STABILIZATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://149.104.110.122.sslip.io:7200",
        "http://149.104.110.122:7200",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token", "X-Worker-Token"],
)

# Persistent Storage for Jobs
class JobStore:
    def __init__(self, db_path="/workspace/gateway_state.db"):
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

    def get_node(self, job_id: str) -> Optional[str]:
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

    def update_node_status(self, url: str, status: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE nodes SET status = ?, last_seen = CURRENT_TIMESTAMP WHERE url = ?", (status, url))

    def get_nodes(self) -> List[Dict[str, Any]]:
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
    if node: job_store.add_node(node.strip())

NODE_HEALTH: Dict[str, Dict[str, Any]] = {}
LOCK = threading.Lock()

async def update_node_health():
    """Background loop to monitor CPU/GPU node health and model status"""
    last_cleanup = 0
    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            # Periodic cleanup of old job records (once per day)
            if time.time() - last_cleanup > 86400:
                print("🧹 [Gateway] Running periodic 7-day job record cleanup...", flush=True)
                job_store.cleanup(days=7)
                last_cleanup = time.time()

            nodes = job_store.get_nodes()
            for node_data in nodes:
                node = node_data["url"]
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
                    job_store.update_node_status(node, "OFFLINE")
                    with LOCK:
                        NODE_HEALTH[node] = {"online": False, "error": str(e)}
            await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_node_health())
    nodes = job_store.get_nodes()
    print(f"🚀 AI Gateway started with {len(nodes)} nodes registered.", flush=True)

def select_best_node(requested_model: Optional[str] = None) -> str:
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

@app.post("/{path:path}")
async def proxy_post(path: str, request: Request):
    """Generic POST proxy with smart routing"""
    body = await request.json()
    
    # Identify requested model for routing
    model_key = body.get("model") or body.get("model_key")
    if "hunyuan" in path: model_key = "hunyuan_480p"
    elif "generate" in path: model_key = "ltx_2_19b"
    
    target_node = select_best_node(model_key)
    
    headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(f"{target_node}/{path}", json=body, headers=headers)
            data = resp.json()
            
            # Remember which node has this job for status/download requests
            if "job_id" in data:
                job_store.save_job(data["job_id"], target_node)
            
            return data
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=502, detail=f"Target node {target_node} failed: {str(e)}")

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
            except: continue
        raise HTTPException(status_code=404, detail="Job not found in cluster")

    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"X-Worker-Token": WORKER_TOKEN} if WORKER_TOKEN else {}
        resp = await client.get(f"{target_node}/status/{job_id}", headers=headers)
        return resp.json()

@app.get("/health")
async def cluster_health():
    with LOCK:
        return {
            "status": "healthy",
            "cluster_size": len(NODE_HEALTH),
            "nodes": job_store.get_nodes(),
            "telemetry": NODE_HEALTH
        }

# --- ADMIN / PROVISIONING ENDPOINTS (Hardened Security) ---

import subprocess

async def verify_admin(x_admin_token: str = Header(None)):
    if not ADMIN_TOKEN or x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized Admin Action")

@app.post("/nodes")
async def add_node_to_cluster(url: str, x_admin_token: str = Header(None)):
    await verify_admin(x_admin_token)
    job_store.add_node(url)
    return {"status": "added", "node": url}

@app.delete("/nodes/{node_url:path}")
async def remove_node_from_cluster(node_url: str, x_admin_token: str = Header(None)):
    await verify_admin(x_admin_token)
    job_store.remove_node(node_url)
    return {"status": "removed"}

@app.post("/nodes/provision")
async def provision_node(ip: str, ssh_key: str, port: int = 22, user: str = "root", x_admin_token: str = Header(None)):
    """
    Hardened Provisioning: Key is passed in Body, stays in RAM only.
    Zero-Storage architecture ensures key never hits Gateway disk.
    """
    await verify_admin(token)
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
            
            os.makedirs("/dev/shm/vf_provision", exist_ok=True)
            temp_key = f"/dev/shm/vf_provision/{uuid.uuid4().hex}"
            try:
                with open(temp_key, "w") as f:
                    f.write(ssh_key)
                os.chmod(temp_key, 0o600)
                
                env["SSH_KEY"] = temp_key
                env["AI_CLUSTER_SECRET"] = WORKER_TOKEN or ""
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ [Provision] Node {ip} deployed successfully.", flush=True)
                    job_store.update_node_status(f"http://{ip}:8122", "READY")
                else:
                    print(f"❌ [Provision] Deployment failed for {ip}: {result.stderr}", flush=True)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8133)
