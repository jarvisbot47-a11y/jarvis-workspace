#!/usr/bin/env python3
"""
Higgsfield Login Script
Run this ONCE to log into Higgsfield with Google
Session cookies will be saved for future use
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

COOKIE_FILE = os.path.join(os.path.dirname(__file__), 'higgsfield_cookies.json')

def main():
    print("="*60)
    print("HIGGSFIELD LOGIN")
    print("="*60)
    print()
    print("This will open a browser window.")
    print("1. Go to https://higgsfield.ai")
    print("2. Click 'Sign in with Google'")
    print("3. Complete the login")
    print("4. Come back here and press Enter")
    print()
    input("Press Enter when logged in...")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Go to Higgsfield
        page.goto("https://higgsfield.ai", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Save cookies if logged in
        if "login" not in page.url.lower():
            print("✅ Logged in! Saving session...")
            
            # Save cookies
            cookies = page.context.cookies()
            with open(COOKIE_FILE, 'w') as f:
                import json
                json.dump(cookies, f)
            
            print(f"✅ Session saved to {COOKIE_FILE}")
            print(f"   {len(cookies)} cookies saved")
        else:
            print("❌ Not logged in. Please try again.")
        
        input("Press Enter to close browser...")
        browser.close()

if __name__ == "__main__":
    main()
