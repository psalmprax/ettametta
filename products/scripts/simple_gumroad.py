#!/usr/bin/env python3
"""
Simple Gumroad Setup - Opens browser for manual login, then automates product creation
"""

import json
import sys
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
    print(f"📝 Desc: {len(description) if description else 0} chars")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # Open Gumroad login
        page.goto('https://gumroad.com/login')
        print("\n🔐 Please login to Gumroad in the browser window...")
        print("   (Waiting for you to complete login)")
        
        # Wait for dashboard
        try:
            page.wait_for_url('**/dashboard**', timeout=180000)  # 3 min timeout
            print("✅ Login detected!")
        except:
            print("⏱️  Timeout - please login faster next time")
            browser.close()
            return
        
        # Navigate to new product
        page.goto('https://gumroad.com/products/new')
        page.wait_for_load_state('networkidle')
        print("📦 Opening new product page...")
        
        # Fill product name
        try:
            name_input = page.locator('input[name="product[name]"]')
            if name_input.count() > 0:
                name_input.fill(metadata['name'])
                print(f"  ✓ Name: {metadata['name']}")
        except Exception as e:
            print(f"  ⚠️ Name error: {e}")
        
        # Set price (Gumroad uses cents)
        try:
            price_input = page.locator('input[name="product[price]"]')
            if price_input.count() > 0:
                price_input.fill(str(int(metadata['price'] * 100)))
                print(f"  ✓ Price: ${metadata['price']}")
        except Exception as e:
            print(f"  ⚠️ Price error: {e}")
        
        # Take screenshot
        page.screenshot(path=str(product_path / 'assets' / 'gumroad-form-filled.png'))
        print("📸 Screenshot saved: assets/gumroad-form-filled.png")
        
        print("\n" + "=" * 50)
        print("✅ Browser opened with form pre-filled!")
        print("=" * 50)
        print("\nNext steps in browser:")
        print("  1. Upload cover image")
        print("  2. Upload product file")
        print("  3. Paste description")
        print("  4. Add tags")
        print("  5. Click Save/Publish")
        print("\nPress Enter here when done, or Ctrl+C to exit...")
        
        try:
            input()
        except KeyboardInterrupt:
            pass
        
        browser.close()
        print("✅ Done!")

if __name__ == '__main__':
    main()
