import os
import sys
import argparse
import subprocess
import time
import httpx

def run_command(cmd, env=None):
    print(f"🚀 [Orchestrator] Running: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line.strip())
    process.wait()
    if process.returncode != 0:
        raise Exception(f"❌ Command failed with exit code {process.returncode}")

def main():
    parser = argparse.ArgumentParser(description="Agnostic E2E Node Integration Orchestrator")
    parser.add_argument("--ip", required=True, help="Target Node IP")
    parser.add_argument("--port", type=str, default="22", help="SSH Port")
    parser.add_argument("--user", default="root", help="SSH User")
    parser.add_argument("--key", default="/home/psalmprax/Music/id_rsa", help="SSH Key Path")
    parser.add_argument("--gateway", default="http://localhost:8133", help="AI Gateway URL")
    parser.add_argument("--admin-token", required=True, help="Gateway Admin Token")
    parser.add_argument("--cluster-secret", required=True, help="AI Cluster Secret")

    args = parser.parse_args()

    # 1. Provisioning
    print(f"\n--- Phase 1: Agnostic Deployment to {args.ip}:{args.port} ---")
    deploy_script = os.path.join(os.getcwd(), "remote_ai_setup", "deploy_to_gpu_server.sh")
    
    env = os.environ.copy()
    env["SSH_KEY"] = args.key
    env["AI_GATEWAY_URL"] = args.gateway
    env["AI_CLUSTER_SECRET"] = args.cluster_secret
    
    try:
        run_command(["/bin/bash", deploy_script, args.ip, args.port, args.user], env=env)
    except Exception as e:
        print(f"❌ Provisioning failed: {e}")
        sys.exit(1)

    # 2. Wait for health
    print(f"\n--- Phase 2: Verifying Node Health at http://{args.ip}:8122 ---")
    node_health_url = f"http://{args.ip}:8122/health"
    max_retries = 15
    healthy = False
    
    for i in range(max_retries):
        try:
            print(f"🏥 Checking health ({i+1}/{max_retries})...")
            resp = httpx.get(node_health_url, timeout=10.0, headers={"X-Worker-Token": args.cluster_secret})
            if resp.status_code == 200:
                print(f"✅ Node is healthy: {resp.json().get('status', 'OK')}")
                healthy = True
                break
        except Exception as e:
            print(f"⏳ Waiting for startup... ({e})")
        time.sleep(10)
    
    if not healthy:
        print("❌ Node failed to become healthy in time.")
        sys.exit(1)

    # 3. Registration
    print("\n--- Phase 3: Cluster Registration ---")
    registration_url = f"{args.gateway}/register"
    node_url = f"http://{args.ip}:8122"
    
    try:
        with httpx.Client() as client:
            resp = client.post(
                registration_url, 
                json={"url": node_url}, 
                headers={"X-Admin-Token": args.admin_token},
                timeout=10.0
            )
            if resp.status_code == 200:
                print(f"✅ Successfully registered {node_url} in cluster.")
            else:
                print(f"❌ Registration failed: {resp.status_code} - {resp.text}")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        sys.exit(1)

    # 4. Final E2E Verification
    print("\n--- Phase 4: Cluster-Wide Verification ---")
    try:
        with httpx.Client() as client:
            resp = client.get(f"{args.gateway}/health")
            if resp.status_code == 200:
                data = resp.json()
                print(f"📦 Cluster Size: {data.get('cluster_size')}")
                found = any(n["url"] == node_url and n["status"] == "READY" for n in data.get("nodes", []))
                if found:
                    print(f"🎉 E2E Verification Successful: Node {node_url} is READY in cluster topology.")
                else:
                    print(f"⚠️ Node {node_url} registered but status is not READY yet. Check logs.")
            else:
                print(f"❌ Gateway health check failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error during cluster verification: {e}")

if __name__ == "__main__":
    main()
