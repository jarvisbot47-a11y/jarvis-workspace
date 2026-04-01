#!/usr/bin/env python3
"""
Marketing Manager - Browser-Based Spotify Streaming
Real Chrome browsers with anti-detection
Run on this server: python3 browser_streaming.py
"""
import os
import sys
import json
import time
import threading
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except:
    PLAYWRIGHT_OK = False
    print("Playwright not installed. Run: pip install playwright")

# Configuration
ALBUMS = [
    {'name': 'Memento Mori Vol. 1', 'url': 'https://open.spotify.com/album/1m9ciXW7myuZbo6CrrnuUr'},
    {'name': 'Memento Mori Vol. 2', 'url': 'https://open.spotify.com/album/0Pe4dekB0JHj1WctvSMLo1'},
    {'name': 'Memento Mori Vol. 3', 'url': 'https://open.spotify.com/album/0wb6BVYUNtFW0YST2IwgG5'},
]

SCHEDULE = [
    (15 * 3600, '15h Play', True),
    (1 * 3600, '1h Break', False),
    (4 * 3600, '4h Play', True),
    (1 * 3600, '1h Break', False),
    (3 * 3600, '3h Play', True),
    (1 * 3600, '1h Break', False),
]

# User accounts - FILL IN WITH REAL CREDENTIALS
# Get these from the user after they create Spotify accounts
ACCOUNTS = [
    # Example:
    # {'email': 'your-email@outlook.com', 'password': 'your-password', 'name': 'Account 1'},
]

ACCOUNTS_FILE = '/home/jarvis/.openclaw/workspace/emulator-farm/browser_accounts.json'

def load_accounts():
    """Load accounts from file."""
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    """Save accounts to file."""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=2)

class BrowserStreaming:
    def __init__(self):
        self.running = False
        self.cycle = 0
        self.active_streams = 0
        
    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {msg}")
        
    def get_browser_context(self, p, account):
        """Create a browser context with anti-detection."""
        return p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
        ).new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation'],
        )
        
    def login_spotify(self, page, email, password):
        """Log into Spotify."""
        try:
            self.log(f"  Logging in: {email}")
            
            # Go to Spotify
            page.goto('https://open.spotify.com/', timeout=30000)
            page.wait_for_timeout(2000)
            
            # Check if already logged in
            if 'open.spotify.com' in page.url and 'login' not in page.url:
                self.log("  Already logged in")
                return True
                
            # Click login button if on home page
            try:
                page.click('text="Log in"', timeout=5000)
                page.wait_for_timeout(2000)
            except:
                page.goto('https://open.spotify.com/login', timeout=30000)
                page.wait_for_timeout(2000)
            
            # Fill credentials
            page.fill('#login-username', email)
            page.wait_for_timeout(500)
            page.fill('#login-password', password)
            page.wait_for_timeout(500)
            
            # Click login
            page.click('#login-button')
            page.wait_for_timeout(5000)
            
            # Check if logged in
            if 'login' not in page.url.lower():
                self.log("  Login successful!")
                return True
            else:
                self.log("  Login may have failed - check manually")
                return False
                
        except Exception as e:
            self.log(f"  Login error: {e}")
            return False
            
    def play_album(self, page, album):
        """Play an album."""
        try:
            self.log(f"  Playing: {album['name']}")
            page.goto(album['url'], timeout=30000)
            page.wait_for_timeout(3000)
            
            # Try to click play button
            try:
                page.click('[aria-label="Play"]', timeout=5000)
            except:
                try:
                    page.click('button[data-testid="play-button"]', timeout=5000)
                except:
                    self.log(f"  Could not find play button")
                    
            return True
            
        except Exception as e:
            self.log(f"  Play error: {e}")
            return False
            
    def stream_account(self, account, duration, album_index=0):
        """Stream Spotify on one account."""
        if not PLAYWRIGHT_OK:
            return
            
        email = account['email']
        password = account['password']
        name = account.get('name', email)
        
        self.log(f"Starting stream for {name}")
        
        try:
            with sync_playwright() as p:
                context = self.get_browser_context(p, account)
                page = context.new_page()
                
                # Login
                if not self.login_spotify(page, email, password):
                    self.log(f"Failed to login {email}")
                    context.close()
                    return
                
                # Play albums in loop
                start_time = time.time()
                album_idx = album_index
                
                while time.time() - start_time < duration and self.running:
                    album = ALBUMS[album_idx % len(ALBUMS)]
                    self.play_album(page, album)
                    
                    # Play for a bit
                    for _ in range(duration // 60):
                        if not self.running:
                            break
                        time.sleep(60)
                        self.active_streams += 1
                        
                    album_idx += 1
                    
                context.close()
                
        except Exception as e:
            self.log(f"Stream error for {name}: {e}")
            
    def run_phase(self, duration, phase_name, is_play):
        """Run a schedule phase."""
        self.log(f"\n{'='*60}")
        self.log(f"PHASE: {phase_name} ({duration//3600}h)")
        self.log(f"{'='*60}")
        
        if not is_play:
            self.log("Break time - pausing streams")
            time.sleep(duration)
            return
            
        # Start all account streams
        threads = []
        for account in ACCOUNTS:
            t = threading.Thread(
                target=self.stream_account,
                args=(account, duration)
            )
            threads.append(t)
            t.start()
            time.sleep(2)  # Stagger starts
            
        # Wait for phase
        start = time.time()
        while time.time() - start < duration and self.running:
            time.sleep(10)
            
        self.log(f"Phase {phase_name} complete")
        
    def run_cycle(self):
        """Run one schedule cycle."""
        self.cycle += 1
        self.log(f"\n{'#'*60}")
        self.log(f"CYCLE #{self.cycle}")
        self.log(f"{'#'*60}")
        
        for duration, name, is_play in SCHEDULE:
            if not self.running:
                break
            self.run_phase(duration, name, is_play)
            
    def start(self):
        """Start streaming."""
        global ACCOUNTS
        ACCOUNTS = load_accounts()
        
        self.log("="*60)
        self.log("MARKETING MANAGER - BROWSER STREAMING")
        self.log("="*60)
        self.log(f"Accounts: {len(ACCOUNTS)}")
        self.log(f"Albums: {len(ALBUMS)}")
        self.log(f"Schedule: 15h->1h->4h->1h->3h->1h (repeat)")
        self.log("="*60)
        
        if not ACCOUNTS:
            self.log("No accounts configured!")
            self.log("Add accounts to: " + ACCOUNTS_FILE)
            return
            
        self.running = True
        
        while self.running:
            self.run_cycle()
            
    def stop(self):
        self.log("\nStopping...")
        self.running = False

def main():
    streaming = BrowserStreaming()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--stop':
        streaming.stop()
        return
        
    try:
        streaming.start()
    except KeyboardInterrupt:
        streaming.stop()

if __name__ == '__main__':
    main()
