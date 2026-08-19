#!/usr/bin/env python3
"""
Quick Gumroad Setup - Uses saved cookies for fast login
Run once with --save-cookies, then subsequent runs auto-login
"""

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIES_FILE = Path.home() / '.gumroad_cookies.json'

def save_cookies():
    """Save Gumroad login cookies"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto('https://gumroad.com/login')
        print("\n⏳ Login to Gumroad, then press Enter here...")
        input()
        
        cookies = context.cookies()
        COOKIES_FILE.write_text(json.dumps(cookies, indent=2))
        print(f"✅ Cookies saved to {COOKIES_FILE}")
        
        browser.close()

def load_cookies():
    """Load saved cookies"""
    if not COOKIES_FILE.exists():
        return None
    return json.loads(COOKIES_FILE.read_text())

def quick_setup(product_dir):
    """Quick product setup using saved cookies"""
    from gumroad_setup import GumroadSetup, PRODUCTS_DIR
    
    cookies = load_cookies()
    if not cookies:
        print("❌ No saved cookies. Run with --save-cookies first")
        return
    
    gumroad = GumroadSetup(headless=False)
    gumroad.start_browser()
    gumroad.context.add_cookies(cookies)
    
    # Continue with setup...
    gumroad.page.goto('https://gumroad.com/dashboard')
    gumroad.page.wait_for_load_state('networkidle')
    
    if 'login' in gumroad.page.url:
        print("❌ Cookies expired. Run with --save-cookies again")
        gumroad.close()
        return
        
    print("✅ Logged in with saved cookies")
    gumroad.create_product(product_dir)
    # ... rest of setup
    
    input("Press Enter to close...")
    gumroad.close()

if __name__ == '__main__':
    import sys
    if '--save-cookies' in sys.argv:
        save_cookies()
    elif len(sys.argv) > 1:
        quick_setup(sys.argv[1])
    else:
        print("Usage:")
        print("  python quick_gumroad.py --save-cookies  # First time setup")
        print("  python quick_gumroad.py <product-dir>   # Setup product")
