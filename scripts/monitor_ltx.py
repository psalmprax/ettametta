import requests
import os
import sys

# Sourced from environment
RENDER_NODE_URL = os.getenv("RENDER_NODE_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

def send_telegram_alert(message):
    if not BOT_TOKEN or not ADMIN_ID:
        print("⚠️ Telegram credentials missing. Skipping alert.")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": f"🚨 LTX-2 SYSTEM ALERT 🚨\n\n{message}",
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Failed to send Telegram alert: {e}")

def check_ltx_health():
    if not RENDER_NODE_URL:
        print("❌ Error: RENDER_NODE_URL not set.")
        return False
    
    print(f"🔍 Checking LTX Node: {RENDER_NODE_URL}...")
    try:
        response = requests.get(RENDER_NODE_URL, timeout=10)
        if response.status_code < 500:
            return True
        else:
            send_telegram_alert(f"Node returned status {response.status_code}. It might be struggling.")
            return False
    except Exception as e:
        send_telegram_alert(f"Node is DOWN!\nError: {e}\n👉 [Restart Colab](https://colab.research.google.com/)")
        return False

if __name__ == "__main__":
    is_up = check_ltx_health()
    sys.exit(0 if is_up else 1)
