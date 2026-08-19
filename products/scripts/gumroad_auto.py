#!/usr/bin/env python3
"""
Gumroad Setup - Opens browser with anti-detection, manual login
"""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PRODUCTS_DIR = Path(__file__).parent.parent

def main():
    product_dir = sys.argv[1] if len(sys.argv) > 1 else "prompts/ai-prompts-business"
    product_path = PRODUCTS_DIR / product_dir
    
    with open(product_path / 'metadata.json', 'r') as f:
        metadata = json.load(f)
    
    # Find files
    product_file = next((product_path / f for f in product_path.iterdir() if f.suffix in ['.pdf', '.md', '.zip', '.txt'] and 'v2' not in f.name), None)
    cover_image = next((f for f in product_path.glob('assets/*.png') if 'cover' in f.name.lower()), None)
    description = next((product_path / name for name in ['gumroad_description_clean.txt', 'gumroad_description.txt'] if (product_path / name).exists()), None)
    if description:
        description = description.read_text()
    
    print(f"🎯 {metadata['name']} | ${metadata.get('price', 'N/A')}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Remove webdriver flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
        """)
        
        page = context.new_page()
        page.goto('https://gumroad.com/login')
        
        print("\n🔐 Login to Gumroad in the browser, then press Enter here...")
        input()
        
        page.goto('https://gumroad.com/products/new')
        page.wait_for_load_state('networkidle')
        
        # Fill name
        try:
            page.locator('input[name="product[name]"]').fill(metadata['name'])
            print(f"✓ Name filled")
        except: pass
        
        # Fill price
        try:
            page.locator('input[name="product[price]"]').fill(str(int(metadata['price'] * 100)))
            print(f"✓ Price filled")
        except: pass
        
        print(f"\n✅ Browser ready!")
        print(f"📁 Cover: {cover_image}")
        print(f"📁 File: {product_file}")
        print(f"📝 Desc: {len(description) if description else 0} chars")
        print("\nComplete in browser, then press Enter...")
        input()
        browser.close()

if __name__ == '__main__':
    main()
