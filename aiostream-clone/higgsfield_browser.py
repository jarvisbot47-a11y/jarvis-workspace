#!/usr/bin/env python3
"""
Higgsfield Browser Automation
Uses the user's actual Chrome browser (logged into Higgsfield)
"""
import os
import sys
import time
import base64
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except:
    print("Playwright not installed. Run: pip install playwright")
    PLAYWRIGHT_OK = False

# Chrome profile path
CHROME_PROFILE_PATH = os.path.expanduser("~/.config/google-chrome")
CHROME_PROFILE_DIR = "Default"

class HiggsfieldBrowserAutomation:
    def __init__(self):
        self.browser_context = None
        self.page = None
        
    def launch_browser(self):
        """Launch Chrome with user's actual profile."""
        if not PLAYWRIGHT_OK:
            return False
            
        with sync_playwright() as p:
            # Launch Chrome with user's actual profile
            context = p.chromium.launch_persistent_context(
                CHROME_PROFILE_PATH,
                channel="chromium",
                headless=False,  # Visible so user can interact
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )
            
            self.browser_context = context
            
            # Create a new page
            page = context.new_page()
            self.page = page
            
            return True
    
    def open_higgsfield(self):
        """Open Higgsfield in the browser."""
        if not self.page:
            return False
            
        print("Opening Higgsfield...")
        self.page.goto("https://higgsfield.ai", timeout=60000)
        self.page.wait_for_timeout(3000)
        
        # Check if logged in
        if "login" in self.page.url.lower():
            print("⚠️ Not logged in! Please log into Higgsfield in the browser window")
            print("Then press Enter here...")
            input("Press Enter after logging in...")
        
        return True
    
    def generate_image_to_video(self, image_path: str, prompt: str, duration: int = 5):
        """Generate video from image using Higgsfield web interface."""
        if not self.page:
            return None, "Browser not initialized"
            
        try:
            # Navigate to image-to-video generation
            print(f"Navigating to image-to-video...")
            self.page.goto("https://higgsfield.ai/image-to-video", timeout=60000)
            self.page.wait_for_timeout(3000)
            
            # Upload image if file path provided
            if image_path and os.path.exists(image_path):
                print(f"Uploading image: {image_path}")
                file_input = self.page.wait_for_selector('input[type="file"]', timeout=5000)
                file_input.set_input_files(image_path)
                self.page.wait_for_timeout(2000)
            
            # Enter prompt
            print(f"Entering prompt: {prompt}")
            prompt_input = self.page.wait_for_selector('textarea, input[type="text"]', timeout=5000)
            prompt_input.fill(prompt)
            
            # Select duration
            if duration == 5:
                # Click 5s button if available
                try:
                    self.page.click('text="5s"')
                except:
                    pass
            
            # Click generate
            print("Clicking generate...")
            try:
                self.page.click('button:has-text("Generate")')
            except:
                try:
                    self.page.click('button[type="submit"]')
                except:
                    return None, "Could not find generate button"
            
            # Wait for generation
            print("Waiting for generation (may take 30-60 seconds)...")
            self.page.wait_for_timeout(60000)
            
            # Look for download link
            try:
                download_btn = self.page.wait_for_selector('a[href*=".mp4"], a[href*="download"]', timeout=10000)
                video_url = download_btn.get_attribute('href')
                return video_url, None
            except:
                pass
            
            # Try to find video in page
            video_elements = self.page.query_selector_all('video')
            if video_elements:
                video_src = video_elements[0].get_attribute('src')
                return video_src, None
                
            return None, "Could not find generated video"
            
        except Exception as e:
            return None, str(e)
    
    def save_video(self, video_url: str, save_path: str) -> bool:
        """Download the generated video."""
        if not video_url:
            return False
            
        try:
            import requests
            response = requests.get(video_url)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"Video saved to: {save_path}")
                return True
        except Exception as e:
            print(f"Save failed: {e}")
        return False
    
    def close(self):
        """Close browser."""
        if self.browser_context:
            self.browser_context.close()

def main():
    print("="*60)
    print("HIGGSFIELD BROWSER AUTOMATION")
    print("="*60)
    
    automation = HiggsfieldBrowserAutomation()
    
    print("\nLaunching Chrome with your profile...")
    if not automation.launch_browser():
        print("Failed to launch browser")
        return
    
    print("\nOpening Higgsfield...")
    automation.open_higgsfield()
    
    print("\n" + "="*60)
    print("BROWSER AUTOMATION READY")
    print("="*60)
    print("""
Options:
1. Use automation.generate_image_to_video() to generate
2. Or use Higgsfield manually in the browser window
3. Close this script when done
""")
    
    # Keep running so user can interact
    input("Press Enter to close browser...")
    automation.close()

if __name__ == "__main__":
    main()
