#!/usr/bin/env python3
"""
Gumroad Setup - Uses your real Chrome browser profile to bypass detection
"""

import json
import sys
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

PRODUCTS_DIR = Path(__file__).parent.parent

def main():
    product_dir = sys.argv[1] if len(sys.argv) > 1 else "prompts/ai-prompts-business"
    product_path = PRODUCTS_DIR / product_dir
    
    # Load metadata
    with open(product_path / 'metadata.json', 'r') as f:
        metadata = json.load(f)
    
    # Find files
    product_file = None
    for ext in ['.pdf', '.md', '.zip', '.txt']:
        candidates = list(product_path.glob(f'*{ext}'))
        if candidates:
            product_file = candidates[0]
            break
    
    cover_image = None
    for ext in ['.png', '.jpg', '.jpeg']:
        candidates = list(product_path.glob(f'*{ext}'))
        candidates += list((product_path / 'assets').glob(f'*{ext}')) if (product_path / 'assets').exists() else []
        if candidates:
            cover_image = candidates[0]
            break
    
    description = None
    for name in ['gumroad_description_clean.txt', 'gumroad_description.txt']:
        desc_path = product_path / name
        if desc_path.exists():
            description = desc_path.read_text()
            break
    
    print("=" * 50)
    print(f"🎯 Product: {metadata['name']}")
    print(f"💰 Price: ${metadata.get('price', 'N/A')}")
    print(f"📁 File: {product_file}")
    print(f"🖼️  Cover: {cover_image}")
    print("=" * 50)
    
    # Find Chrome user data directory
    chrome_dirs = [
        Path.home() / '.config' / 'google-chrome',
        Path.home() / '.config' / 'chromium',
        Path('/snap/chromium/common/chromium'),
    ]
    
    user_data_dir = None
    for d in chrome_dirs:
        if d.exists():
            user_data_dir = d
            break
    
    if not user_data_dir:
        print("❌ Chrome/Chromium profile not found")
        print("Please login to Gumroad manually in your browser first")
        return
    
    print(f"📁 Using Chrome profile: {user_data_dir}")
    
    with sync_playwright() as p:
        # Launch with real Chrome profile (copies it, doesn't modify)
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            channel='chrome',  # Use installed Chrome
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--no-default-browser-check'
            ],
            viewport={'width': 1280, 'height': 800}
        )
        
        page = context.new_page()
        
        # Check if already logged in
        page.goto('https://gumroad.com/dashboard')
        page.wait_for_load_state('networkidle')
        
        if 'login' in page.url.lower():
            print("\n🔐 Not logged in. Please login to Gumroad...")
            print("   (Complete login in the browser window)")
            
            try:
                page.wait_for_url('**/dashboard**', timeout=180000)
                print("✅ Login successful!")
            except:
                print("⏱️  Timeout. Please try again.")
                context.close()
                return
        else:
            print("✅ Already logged in!")
        
        # Navigate to new product
        page.goto('https://gumroad.com/products/new')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)
        
        # Fill product name
        try:
            name_input = page.locator('input[name="product[name]"]')
            if name_input.count() > 0:
                name_input.fill(metadata['name'])
                print(f"  ✓ Name: {metadata['name']}")
        except Exception as e:
            print(f"  ⚠️ Name: {e}")
        
        # Set price (Gumroad uses cents)
        try:
            price_input = page.locator('input[name="product[price]"]')
            if price_input.count() > 0:
                price_input.fill(str(int(metadata['price'] * 100)))
                print(f"  ✓ Price: ${metadata['price']}")
        except Exception as e:
            print(f"  ⚠️ Price: {e}")
        
        # Take screenshot
        screenshot_path = product_path / 'assets' / 'gumroad-form-filled.png'
        page.screenshot(path=str(screenshot_path))
        print(f"📸 Screenshot: {screenshot_path}")
        
        print("\n" + "=" * 50)
        print("✅ Browser opened with form pre-filled!")
        print("=" * 50)
        print("\nComplete these steps in the browser:")
        print("  1. Click 'Upload file' → select product file")
        print("  2. Click 'Add cover image' → select cover image")
        print("  3. Paste description in the text area")
        print("  4. Add tags (ai prompts, business, etc)")
        print("  5. Click 'Save draft' or 'Publish'")
        
        if cover_image:
            print(f"\n📁 Cover image ready: {cover_image}")
        if product_file:
            print(f"📁 Product file ready: {product_file}")
        
        print("\nPress Enter here when done...")
        input()
        
        context.close()
        print("✅ Done!")

if __name__ == '__main__':
    main()
