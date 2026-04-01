#!/usr/bin/env python3
"""
Generate a test video using Higgsfield with saved session
"""
import os
import json
import time
from playwright.sync_api import sync_playwright

COOKIE_FILE = os.path.join(os.path.dirname(__file__), 'higgsfield_cookies.json')
TEST_IMAGE = '/tmp/test_album_art.jpg'
OUTPUT_DIR = '/mnt/media-drive/MystikSingh/General/Raw'

def generate_video(prompt, duration=5):
    print("="*60)
    print(f"GENERATING VIDEO: {prompt[:50]}...")
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
        page.wait_for_timeout(3000)
        
        print(f"URL: {page.url}")
        
        # Take screenshot of initial state
        page.screenshot(path='/tmp/higgsfield_1_initial.png')
        
        # Look for Start From options - need to click "Image" first
        print("\nLooking for Image option...")
        
        # Try to find and click the Image tab/button in "Start From" section
        try:
            # Look for elements with "Image" text
            image_elements = page.query_selector_all('*')
            for el in image_elements:
                try:
                    text = el.inner_text()[:100] if el.inner_text() else ''
                    if 'start from' in text.lower() and 'image' in text.lower():
                        print(f"  Found: {text[:80]}")
                        el.click()
                        break
                except:
                    pass
        except Exception as e:
            print(f"  Error looking for Image: {e}")
        
        page.wait_for_timeout(2000)
        page.screenshot(path='/tmp/higgsfield_2_after_image_click.png')
        
        # Find file input for image upload
        print("\nUploading image...")
        try:
            # Look for the file input
            file_input = page.wait_for_selector('input[type="file"]', timeout=5000)
            if file_input:
                file_input.set_input_files(TEST_IMAGE)
                print("  Image uploaded!")
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f"  Error uploading: {e}")
        
        page.screenshot(path='/tmp/higgsfield_3_after_upload.png')
        
        # Enter prompt text
        print("\nEntering prompt...")
        try:
            # Look for textarea or text input
            textarea = page.wait_for_selector('textarea', timeout=5000)
            if textarea:
                textarea.fill(prompt)
                print("  Prompt entered!")
        except Exception as e:
            print(f"  Error entering prompt: {e}")
        
        page.wait_for_timeout(1000)
        
        # Select duration (5s)
        print("\nSelecting 5s duration...")
        try:
            buttons = page.query_selector_all('button')
            for btn in buttons:
                text = btn.inner_text()[:20] if btn.inner_text() else ''
                if '5' in text and 's' in text:
                    print(f"  Clicking: {text}")
                    btn.click()
                    break
        except Exception as e:
            print(f"  Error selecting duration: {e}")
        
        page.wait_for_timeout(1000)
        
        # Click Generate
        print("\nClicking Generate...")
        try:
            buttons = page.query_selector_all('button')
            for btn in buttons:
                text = btn.inner_text()[:50] if btn.inner_text() else ''
                if 'generate' in text.lower():
                    print(f"  Clicking: {text[:40]}")
                    btn.click()
                    break
        except Exception as e:
            print(f"  Error clicking generate: {e}")
        
        page.screenshot(path='/tmp/higgsfield_4_generating.png')
        
        print("\n⏳ Waiting for generation (30-60 seconds)...")
        page.wait_for_timeout(60000)
        
        page.screenshot(path='/tmp/higgsfield_5_done.png')
        
        # Look for download link
        print("\nLooking for download...")
        try:
            # Look for video element or download link
            video = page.query_selector('video')
            if video:
                src = video.get_attribute('src')
                print(f"  Found video! src={src[:100] if src else 'None'}...")
            
            # Look for download buttons/links
            links = page.query_selector_all('a[href*=".mp4"], a[href*="download"]')
            for link in links[:5]:
                href = link.get_attribute('href') or ''
                text = link.inner_text()[:30] if link.inner_text() else ''
                print(f"  Link: {text[:30]} -> {href[:80]}")
        except Exception as e:
            print(f"  Error looking for download: {e}")
        
        print("\n" + "="*60)
        print("GENERATION COMPLETE")
        print("="*60)
        print("Screenshots saved:")
        print("  /tmp/higgsfield_1_initial.png")
        print("  /tmp/higgsfield_2_after_image_click.png")
        print("  /tmp/higgsfield_3_after_upload.png")
        print("  /tmp/higgsfield_4_generating.png")
        print("  /tmp/higgsfield_5_done.png")
        
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    prompt = "Cinematic slow motion drone shot through neon city lights at night, fog, dramatic lighting"
    generate_video(prompt, duration=5)
