import time
import requests
import json
import os
import subprocess
import sys
import base64
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
API_URL = "https://obdulia-mouill-ryann.ngrok-free.dev"
OUTPUT_DIR = "downloads/storyboard"

STORYBOARD = [
    {
        "character_name": "Davido",
        "prompt": "8k close-up high-fidelity portrait of Davido, the Nigerian Afrobeat superstar, short fade haircut, diamond earrings and large diamond chains, expressive eyes, distinctive nose bridge, cinematic stage lighting, f/1.8, high skin texture, photorealistic, cinematic atmosphere, sharp focus, 35mm lens",
        "frames": 121, "steps": 8, "upscale_factor": 8, "enhance_face": True, "likeness_strength": 1.5
    },
    {
        "character_name": "Davido",
        "prompt": "Cinematic medium shot of the musician Davido passionately singing into a microphone on a stage, highly detailed, expressive face, 8k resolution, photorealistic",
        "frames": 121, "steps": 8, "upscale_factor": 8, "enhance_face": True, "likeness_strength": 1.5
    },
    {
        "character_name": "Davido",
        "prompt": "Over the shoulder tracking shot of Davido pointing and singing directly to Donald Trump, who is standing in the front row watching closely, dynamic motion, 8k, photorealistic",
        "frames": 121, "steps": 8, "upscale_factor": 8, "enhance_face": True, "likeness_strength": 1.5
    },
    {
        "character_name": "Hillary Clinton",
        "prompt": "Cinematic reaction shot of Hillary Clinton standing in the crowd, her hands covering her mouth in extreme surprise and shock, eyes wide, dynamic lighting, 8k resolution, ultra-sharp focus",
        "frames": 121, "steps": 8, "upscale_factor": 8, "enhance_face": True, "likeness_strength": 1.5
    },
    {
        "character_name": "Davido",
        "prompt": "8k close-up of Davido smiling, warm studio lighting, highly detailed diamond jewelry glinting, 50mm lens, shallow depth of field, masterpiece portrait, photorealistic skin pores and textures",
        "frames": 121, "steps": 8, "upscale_factor": 8, "enhance_face": True, "likeness_strength": 1.5
    },
    {
        "character_name": "Davido",
        "prompt": "8k side profile of Davido looking thoughtful, dramatic noir lighting, high contrast, sharp facial contours, short fade haircut, diamond earring visible, ultra-realistic textures, cinematic film still",
        "frames": 121, "steps": 8, "upscale_factor": 8, "enhance_face": True, "likeness_strength": 1.5
    }
]

def fetch_likeness_image(character_name):
    print(f"🔍 Sourcing HD Reference Image for '{character_name}'...")
    fallback_map = {
        "Davido": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Davido_2022.jpg/800px-Davido_2022.jpg", 
        "Donald Trump": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Donald_Trump_official_portrait.jpg/1200px-Donald_Trump_official_portrait.jpg",
        "Hillary Clinton": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Hillary_Clinton_official_portrait.jpg/1200px-Hillary_Clinton_official_portrait.jpg"
    }
    img_url = fallback_map.get(character_name, "")
    print(f"   => Downloading portrait: {img_url}")
    try:
        r = requests.get(img_url, timeout=10)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
    except: pass
    return ""

def generate_shot(scene_data):
    print(f"\n🎬 Requesting Shot: '{scene_data['prompt'][:60]}...'")
    try:
        r = requests.post(f"{API_URL}/generate", json=scene_data, timeout=60)
        if r.status_code == 200:
            job_id = r.json()["job_id"]
            print(f"   => 🟢 Job Started: {job_id}")
            return job_id
        else:
            print(f"   => ❌ Error starting job: HTTP {r.status_code} - {r.text}")
    except Exception as e:
        print(f"   => ❌ API Request failed: {e}")
    return None

def poll_and_download(job_id, output_path):
    print(f"   ⏳ Waiting for {job_id} to render and stabilize...")
    download_url = f"{API_URL}/download/{job_id}"
    while True:
        try:
            r = requests.get(download_url, stream=True, timeout=10)
            if r.status_code == 200:
                print(f"   📥 Downloading {job_id}...")
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
                print(f"   ✅ Saved clip: {output_path}")
                return True
            time.sleep(15)
            sys.stdout.write(".")
            sys.stdout.flush()
        except: time.sleep(15)

def assemble_master(video_files, final_output):
    print(f"\n🎞️ Assembling {len(video_files)} sequential shots into Master Sequence...")
    list_file = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(list_file, "w") as f:
        for vf in video_files: f.write(f"file '{os.path.abspath(vf)}'\n")
    
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", final_output]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"🌟 Master Sequence Completed Successfully: {final_output}")
    except: print("❌ Error during multi-shot assembly.")

def main():
    print("============== VIRAL FORGE: STORYBOARD COMPOSER (BYPASS) ==============")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    completed_clips = []
    
    for i, scene in enumerate(STORYBOARD):
        print(f"\n--- Processing Scene {i+1}/{len(STORYBOARD)} ---")
        if "character_name" in scene:
            b64 = fetch_likeness_image(scene["character_name"])
            if b64: scene["image_base64"] = b64
        
        job_id = generate_shot(scene)
        if job_id:
            out_path = os.path.join(OUTPUT_DIR, f"scene_{i+1:02d}_{job_id}.mp4")
            if poll_and_download(job_id, out_path): completed_clips.append(out_path)
            
    if len(completed_clips) > 1:
        assemble_master(completed_clips, os.path.join(OUTPUT_DIR, "FINAL_MASTER_30s.mp4"))

if __name__ == "__main__":
    main()
