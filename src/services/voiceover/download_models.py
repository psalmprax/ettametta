import os
import subprocess
from pathlib import Path

def download_models():
    model_dir = Path("models/fish-speech-1.5")
    if model_dir.exists() and any(model_dir.iterdir()):
        print(f"✅ Models already exist in {model_dir}. Skipping download.")
        return

    print("🚀 Models missing. Starting automated download from HuggingFace...")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Using huggingface-cli to download the specific model
    try:
        subprocess.run([
            "huggingface-cli", "download", 
            "fishaudio/fish-speech-1.5", 
            "--local-dir", str(model_dir),
            "--local-dir-use-symlinks", "False"
        ], check=True)
        print("✅ Model download complete.")
    except Exception as e:
        print(f"❌ Failed to download models: {e}")
        # Fallback to wget or manual instruction if cli fails
        print("Manual download required: https://huggingface.co/fishaudio/fish-speech-1.5")

if __name__ == "__main__":
    download_models()
