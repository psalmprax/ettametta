#!/usr/bin/env python3
"""
Gumroad Product Setup Automation
Automates: Login → Create Product → Upload Files → Set Details → Preview
"""

import os
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Paths
PRODUCTS_DIR = Path(__file__).parent.parent
SCREENSHOTS_DIR = PRODUCTS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

class GumroadSetup:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
    def start_browser(self):
        """Start Playwright browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        # Use persistent context for cookies
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()
        
    def screenshot(self, name):
        """Save screenshot"""
        path = SCREENSHOTS_DIR / f"{name}.png"
        self.page.screenshot(path=str(path))
        print(f"  📸 Screenshot saved: {path}")
        return path
        
    def login(self, email=None, password=None):
        """Login to Gumroad"""
        print("\n🔐 Logging into Gumroad...")
        self.page.goto('https://gumroad.com/login')
        self.page.wait_for_load_state('networkidle')
        self.screenshot('01-login-page')
        
        if email and password:
            # Automated login
            self.page.fill('input[name="email"]', email)
            self.page.fill('input[name="password"]', password)
            self.page.click('button[type="submit"]')
            self.page.wait_for_url('**/dashboard**', timeout=30000)
            print("  ✅ Logged in successfully")
        else:
            # Manual login - wait for user
            print("\n  ⏳ Please login manually in the browser window...")
            print("  Press Enter here when logged in...")
            input()
            self.page.wait_for_url('**/dashboard**', timeout=120000)
            print("  ✅ Login detected")
            
        self.screenshot('02-dashboard')
        
    def create_product(self, product_dir):
        """Create a new product on Gumroad"""
        product_path = PRODUCTS_DIR / product_dir
        
        # Load metadata
        with open(product_path / 'metadata.json', 'r') as f:
            metadata = json.load(f)
        
        print(f"\n📦 Creating product: {metadata['name']}")
        
        # Navigate to new product page
        self.page.goto('https://gumroad.com/products/new')
        self.page.wait_for_load_state('networkidle')
        self.screenshot('03-new-product-page')
        
        # Fill product name
        self.page.fill('input[name="product[name]"]', metadata['name'])
        print(f"  ✓ Name: {metadata['name']}")
        
        # Set price
        price_input = self.page.locator('input[name="product[price]"]')
        if price_input.count() > 0:
            price_input.fill(str(int(metadata['price'] * 100)))  # Gumroad uses cents
            print(f"  ✓ Price: ${metadata['price']}")
        
        # Set URL slug
        if 'slug' in metadata:
            slug_input = self.page.locator('input[name="product[slug]"]')
            if slug_input.count() > 0:
                slug_input.fill(metadata['slug'])
                print(f"  ✓ Slug: {metadata['slug']}")
        
        self.screenshot('04-product-filled')
        
    def upload_file(self, file_path, file_type='product'):
        """Upload product file"""
        print(f"\n📁 Uploading {file_type}: {file_path}")
        
        # Find file input
        file_input = self.page.locator('input[type="file"]').first
        file_input.set_input_files(str(file_path))
        
        # Wait for upload to complete
        self.page.wait_for_timeout(3000)
        self.screenshot(f'05-upload-{file_type}')
        print(f"  ✅ File uploaded")
        
    def upload_cover(self, image_path):
        """Upload cover image"""
        print(f"\n🖼️  Uploading cover image...")
        
        # Look for cover/image upload section
        cover_section = self.page.locator('text=Cover image').or_(self.page.locator('text=Upload image'))
        if cover_section.count() > 0:
            file_input = cover_section.locator('..').locator('input[type="file"]').first
            file_input.set_input_files(str(image_path))
            self.page.wait_for_timeout(3000)
            self.screenshot('06-cover-uploaded')
            print(f"  ✅ Cover image uploaded")
        else:
            print("  ⚠️  Cover upload section not found, trying file input...")
            file_inputs = self.page.locator('input[type="file"]')
            if file_inputs.count() > 1:
                file_inputs.nth(1).set_input_files(str(image_path))
                self.page.wait_for_timeout(3000)
                print(f"  ✅ Cover image uploaded (fallback)")
                
    def set_description(self, description_text):
        """Set product description"""
        print(f"\n📝 Setting description...")
        
        # Gumroad uses a rich text editor - find the contenteditable div
        editor = self.page.locator('[contenteditable="true"]').or_(
            self.page.locator('.ProseMirror')
        ).or_(
            self.page.locator('div[role="textbox"]')
        )
        
        if editor.count() > 0:
            editor.first.click()
            # Clear existing content
            self.page.keyboard.press('Control+A')
            self.page.keyboard.press('Delete')
            # Type description
            editor.first.fill(description_text)
            self.screenshot('07-description-set')
            print(f"  ✅ Description set ({len(description_text)} chars)")
        else:
            print("  ⚠️  Editor not found, trying textarea...")
            textarea = self.page.locator('textarea').first
            if textarea.count() > 0:
                textarea.fill(description_text)
                print(f"  ✅ Description set (textarea)")
                
    def add_tags(self, tags):
        """Add product tags"""
        print(f"\n🏷️  Adding tags...")
        
        tag_input = self.page.locator('input[placeholder*="tag"]').or_(
            self.page.locator('input[name*="tag"]')
        )
        
        if tag_input.count() > 0:
            for tag in tags:
                tag_input.first.fill(tag)
                self.page.keyboard.press('Enter')
                self.page.wait_for_timeout(500)
            self.screenshot('08-tags-added')
            print(f"  ✅ Tags added: {', '.join(tags)}")
            
    def preview_product(self):
        """Preview the product"""
        print(f"\n👀 Previewing product...")
        
        # Look for preview button
        preview_btn = self.page.locator('text=Preview').or_(
            self.page.locator('button:has-text("Preview")')
        )
        
        if preview_btn.count() > 0:
            preview_btn.first.click()
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_timeout(2000)
            self.screenshot('09-preview')
            print(f"  ✅ Preview opened")
            return True
        else:
            print("  ⚠️  Preview button not found")
            return False
            
    def save_product(self):
        """Save/publish the product"""
        print(f"\n💾 Saving product...")
        
        save_btn = self.page.locator('button:has-text("Save")').or_(
            self.page.locator('button:has-text("Publish")')
        ).or_(
            self.page.locator('input[type="submit"]')
        )
        
        if save_btn.count() > 0:
            save_btn.first.click()
            self.page.wait_for_load_state('networkidle')
            self.page.wait_for_timeout(3000)
            self.screenshot('10-saved')
            
            # Get product URL if available
            url = self.page.url
            print(f"  ✅ Product saved: {url}")
            return url
        else:
            print("  ⚠️  Save button not found")
            return None
            
    def close(self):
        """Close browser"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


def setup_product(product_dir, email=None, password=None, headless=False):
    """Main function to set up a product on Gumroad"""
    
    product_path = PRODUCTS_DIR / product_dir
    
    if not product_path.exists():
        print(f"❌ Product not found: {product_dir}")
        return False
        
    if not (product_path / 'metadata.json').exists():
        print(f"❌ No metadata.json found in {product_dir}")
        return False
        
    # Load metadata
    with open(product_path / 'metadata.json', 'r') as f:
        metadata = json.load(f)
    
    # Find product file
    product_file = None
    for ext in ['.pdf', '.md', '.zip', '.txt']:
        candidates = list(product_path.glob(f'*{ext}'))
        if candidates:
            product_file = candidates[0]
            break
            
    # Find cover image
    cover_image = None
    for ext in ['.png', '.jpg', '.jpeg']:
        candidates = list(product_path.glob(f'*{ext}'))
        candidates += list((product_path / 'assets').glob(f'*{ext}')) if (product_path / 'assets').exists() else []
        if candidates:
            cover_image = candidates[0]
            break
    
    # Find description
    description = None
    for name in ['gumroad_description_clean.txt', 'gumroad_description.txt']:
        desc_path = product_path / name
        if desc_path.exists():
            description = desc_path.read_text()
            break
    
    print("=" * 50)
    print(f"🎯 Product Setup: {metadata['name']}")
    print("=" * 50)
    print(f"  Price: ${metadata.get('price', 'N/A')}")
    print(f"  Product file: {product_file}")
    print(f"  Cover image: {cover_image}")
    print(f"  Description: {len(description) if description else 0} chars")
    print(f"  Tags: {metadata.get('tags', [])}")
    
    # Start automation
    gumroad = GumroadSetup(headless=headless)
    
    try:
        gumroad.start_browser()
        gumroad.login(email, password)
        gumroad.create_product(product_dir)
        
        if cover_image:
            gumroad.upload_cover(cover_image)
            
        if product_file:
            gumroad.upload_file(product_file, 'product')
            
        if description:
            gumroad.set_description(description)
            
        if 'tags' in metadata:
            gumroad.add_tags(metadata['tags'])
            
        gumroad.preview_product()
        
        # Uncomment to auto-save:
        # url = gumroad.save_product()
        
        print("\n" + "=" * 50)
        print("✅ Product setup complete!")
        print(f"📸 Screenshots saved to: {SCREENSHOTS_DIR}")
        print("=" * 50)
        
        # Keep browser open for review
        print("\nPress Enter to close browser...")
        input()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        gumroad.screenshot('error')
        raise
    finally:
        gumroad.close()
        
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Gumroad product')
    parser.add_argument('product_dir', help='Product directory name')
    parser.add_argument('--email', help='Gumroad email')
    parser.add_argument('--password', help='Gumroad password')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    setup_product(
        args.product_dir,
        email=args.email,
        password=args.password,
        headless=args.headless
    )
