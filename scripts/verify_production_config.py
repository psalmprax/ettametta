import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.config import settings
from services.video_engine.processor import VideoProcessor

def verify_config():
    print("--- Configuration Verification ---")
    print(f"ENV: {settings.ENV}")
    print(f"PRODUCTION_DOMAIN: {settings.PRODUCTION_DOMAIN}")
    
    print("\n--- OAuth Redirect URIs ---")
    print(f"Google Callback: {settings.GOOGLE_REDIRECT_URI}")
    print(f"TikTok Callback: {settings.TIKTOK_REDIRECT_URI}")
    
    expected_google = f"{settings.PRODUCTION_DOMAIN}/publish/auth/youtube/callback"
    if settings.GOOGLE_REDIRECT_URI == expected_google:
        print("✅ Google Redirect URI matches expected pattern.")
    else:
        print(f"❌ Google Redirect URI Mismatch! Got: {settings.GOOGLE_REDIRECT_URI}")

def verify_font_logic():
    print("\n--- Video Engine Font Resolution ---")
    # Initialize processor (should trigger font check)
    processor = VideoProcessor(output_dir="tmp_verify")
    print(f"Resolved Font Path: {processor.font_path}")
    
    if os.path.exists(processor.font_path):
        print(f"✅ Font file exists at: {processor.font_path}")
    else:
        print(f"❌ Font file missing at: {processor.font_path}")

if __name__ == "__main__":
    verify_config()
    verify_font_logic()
