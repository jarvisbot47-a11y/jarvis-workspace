#!/usr/bin/env python3
"""
Test Higgsfield Video Generation with saved session
"""
import os
import json
from playwright.sync_api import sync_playwright

COOKIE_FILE = os.path.join(os.path.dirname(__file__), 'higgsfield_cookies.json')

def test_full_generation():
    print("="*60)
    print("HIGGSFIELD VIDEO GENERATION TEST")
    print("="*60)
    
    # Load cookies
    with open(COOKIE_FILE, 'r') as f:
        cookies = json.load(f)
    print(f"Loaded {len(cookies)} cookies")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        
        print("Navigating to Higgsfield...")
        page.goto('https://higgsfield.ai/create/video', timeout=60000)
        page.wait_for_timeout(5000)
        
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")
        
        # Take initial screenshot
        page.screenshot(path='/tmp/higgsfield_step1.png')
        
        # Find and click "Start From: Image" if available
        print("\nLooking for Image option...")
        try:
            # Look for Image tab/button
            image_btns = page.query_selector_all('button, div[role="button"], [tabindex]')
            for btn in image_btns[:20]:
                text = btn.inner_text()[:50] if btn.inner_text() else ''
                if 'image' in text.lower():
                    print(f"  Found: {text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Try to find the file input for image upload
        print("\nLooking for file upload input...")
        inputs = page.query_selector_all('input[type="file"]')
        print(f"  Found {len(inputs)} file inputs")
        for inp in inputs:
            accept = inp.get_attribute('accept') or ''
            print(f"    accept={accept}")
        
        # Try to find the text prompt input
        print("\nLooking for text prompt input...")
        textareas = page.query_selector_all('textarea')
        text_inputs = page.query_selector_all('input[type="text"]')
        editable_divs = page.query_selector_all('[contenteditable="true"]')
        
        print(f"  textareas: {len(textareas)}")
        print(f"  text inputs: {len(text_inputs)}")
        print(f"  contenteditable: {len(editable_divs)}")
        
        # Take screenshot of current state
        page.screenshot(path='/tmp/higgsfield_ui.png')
        print("\nScreenshot saved to /tmp/higgsfield_ui.png")
        print("Open this image to see the current UI state")
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print("""
Next steps:
1. Find the image upload input
2. Upload a test image
3. Enter a prompt
4. Click Generate
5. Wait for video to be generated
6. Download the video
        """)
        
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    test_full_generation()
