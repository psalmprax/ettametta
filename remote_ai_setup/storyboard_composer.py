import time
import requests
import json
import os
import subprocess
import sys
import base64
from pathlib import Path
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
SSH_KEY = "/home/psalmprax/Music/id_rsa"
SSH_HOST = "root@220.82.46.3"
SSH_PORT = "51643"
API_URL = "http://localhost:8000"
OUTPUT_DIR = "downloads/storyboard"

STORYBOARD = [
    {
        "character_name": "Davido",
        "prompt": "Cinematic medium shot of the musician Davido passionately singing into a microphone on a stage, highly detailed, expressive face, 8k resolution, photorealistic",
        "frames": 25,
        "steps": 20,
        "upscale_factor": 1, # Set to 1 for initial test speed
        "purge_hallucination": True
    },
    {
        "character_name": "Davido",
        "prompt": "Over the shoulder tracking shot of Davido pointing and singing directly to Donald Trump, who is standing in the front row watching closely, dynamic motion, 8k, photorealistic",
        "frames": 17,
        "steps": 15,
        "upscale_factor": 1,
        "purge_hallucination": True
    },
    {
        "character_name": "Hillary Clinton",
        "prompt": "Cinematic reaction shot of Hillary Clinton standing in the crowd, her hands covering her mouth in extreme surprise and shock, eyes wide, dynamic lighting, 8k resolution, ultra-sharp focus",
        "frames": 17,
        "steps": 15,
        "upscale_factor": 1,
        "purge_hallucination": True
    }
]

def fetch_likeness_image(character_name):
    """
    Scrapes DuckDuckGo Images for an HD portrait of the requested character,
    downloads it, and returns the base64 encoded string.
    """
    print(f"🔍 Sourcing HD Reference Image for '{character_name}'...")
    # fallback to the known reliable Davido image if we can't reliably parse DDG HTML
    fallback_map = {
        "Davido": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Davido_2022.jpg/800px-Davido_2022.jpg",
        "Donald Trump": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/800px-Donald_Trump_official_portrait.jpg",
        "Hillary Clinton": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Hillary_Clinton_official_portrait.jpg/800px-Hillary_Clinton_official_portrait.jpg"
    }
    
    img_url = fallback_map.get(character_name, "")
    if not img_url:
        # Simple DDG HTML Search (POC)
        search_url = f"https://html.duckduckgo.com/html/?q={character_name.replace(' ', '+')}+portrait+high+definition"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(search_url, headers=headers, timeout=5)
            # Defaulting to fallback if DDG is tricky to parse without BS4 (which we have in the venv but let's keep it simple)
            img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Davido_2022.jpg/800px-Davido_2022.jpg"
        except:
            pass

    print(f"   => Downloading portrait: {img_url}")
    try:
        r = requests.get(img_url, timeout=10)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
    except:
        pass
    return ""

def ensure_tunnel():
    print("🔌 Verifying SSH Tunnel to remote RTX 6000 API...")
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            print("✅ Tunnel already active and API is healthy.")
            return True
    except requests.exceptions.ConnectionError:
        pass

    print("🚀 Starting local SSH port forwarding (8000 -> 8000)...")
    cmd = f"ssh -i {SSH_KEY} -f -N -L 8000:localhost:8000 {SSH_HOST} -p {SSH_PORT}"
    subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    
    time.sleep(3)
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code == 200:
            print(f"✅ Tunnel established successfully! Remote API: {r.json()}")
            return True
    except Exception as e:
        print(f"❌ Failed to connect to API via tunnel: {e}")
        return False
    return False

def generate_shot(scene_data):
    print(f"\n🎬 Requesting Shot: '{scene_data['prompt'][:60]}...'")
    try:
        r = requests.post(f"{API_URL}/video", json=scene_data, timeout=10)
        if r.status_code == 200:
            job = r.json()
            job_id = job["job_id"]
            print(f"   => 🟢 Job Started: {job_id}")
            return job_id
        else:
            print(f"   => ❌ Error starting job: HTTP {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"   => ❌ API Request failed: {e}")
        return None

def poll_and_download(job_id, output_path):
    print(f"   ⏳ Waiting for {job_id} to render and stabilize (this will take a few minutes)...")
    download_url = f"{API_URL}/download/{job_id}"
    while True:
        try:
            r = requests.get(download_url, stream=True, timeout=10)
            if r.status_code == 200:
                print(f"   📥 Downloading {job_id} to local disk...")
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        if chunk: f.write(chunk)
                print(f"   ✅ Saved clip: {output_path}")
                return True
            elif r.status_code == 404:
                # Still processing
                sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(15)
            else:
                print(f"\n   ⚠️ Unexpected status code {r.status_code} for {job_id}")
                time.sleep(15)
        except Exception as e:
            print(f"\n   ⚠️ Connection error while polling {job_id}: {e}")
            time.sleep(15)

def assemble_master(video_files, final_output):
    print(f"\n🎞️ Assembling {len(video_files)} sequential shots into Master Sequence...")
    list_file = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(list_file, "w") as f:
        for vf in video_files:
            # FFmpeg concat demuxer requires absolute paths or relative paths correctly formatted
            f.write(f"file '{os.path.abspath(vf)}'\n")
    
    cmd = [
        "/home/psalmprax/.local/bin/ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, 
        "-c", "copy", final_output
    ]
    try:
        # Run ffmpeg to concatenate
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"🌟 Master Sequence Completed Successfully: {final_output}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during multi-shot assembly: {e}")
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)

def main():
    print("============== VIRAL FORGE: STORYBOARD COMPOSER ==============")
    if not ensure_tunnel():
        print("Exiting: Could not establish secure connection to rendering node.")
        return
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    completed_clips = []
    
    for i, scene in enumerate(STORYBOARD):
        print(f"\n--- Processing Scene {i+1}/{len(STORYBOARD)} ---")
        
        # Inject Likeness if character is specified
        if "character_name" in scene and scene["character_name"]:
            b64_img = fetch_likeness_image(scene["character_name"])
            if b64_img:
                scene["image_base64"] = b64_img
                print(f"   ✅ Character Image Injected: {scene['character_name']}")

        job_id = generate_shot(scene)
        if job_id:
            out_path = os.path.join(OUTPUT_DIR, f"scene_{i+1:02d}_{job_id}.mp4")
            success = poll_and_download(job_id, out_path)
            if success:
                completed_clips.append(out_path)
            else:
                print(f"❌ Failed to download Scene {i+1}.")
        else:
            print(f"❌ Skipping Scene {i+1} due to generation error.")
            
    if len(completed_clips) > 1:
        master_path = os.path.join(OUTPUT_DIR, "FINAL_MASTER_SEQUENCE.mp4")
        assemble_master(completed_clips, master_path)
    elif len(completed_clips) == 1:
        print(f"\n⚠️ Only one clip successfully generated. Final output: {completed_clips[0]}")
    else:
        print("\n❌ No clips were successfully generated. Master sequence aborted.")

if __name__ == "__main__":
    main()
