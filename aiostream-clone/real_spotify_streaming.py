#!/usr/bin/env python3
"""
Real Spotify Streaming - Marketing Manager
Real Chrome browsers, real Spotify accounts, real streams
Schedule: 15h play -> 1h break -> 4h play -> 1h break -> 3h play -> 1h break -> repeat
"""
import os
import sys
import json
import time
import threading
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except:
    PLAYWRIGHT_AVAILABLE = False

# Configuration
ALBUMS = [
    {'name': 'Memento Mori Vol. 1', 'url': 'https://open.spotify.com/album/1m9ciXW7myuZbo6CrrnuUr'},
    {'name': 'Memento Mori Vol. 2', 'url': 'https://open.spotify.com/album/0Pe4dekB0JHj1WctvSMLo1'},
    {'name': 'Memento Mori Vol. 3', 'url': 'https://open.spotify.com/album/0wb6BVYUNtFW0YST2IwgG5'},
]

SCHEDULE = [
    (15 * 3600, '15h Play'),
    (1 * 3600, '1h Break'),
    (4 * 3600, '4h Play'),
    (1 * 3600, '1h Break'),
    (3 * 3600, '3h Play'),
    (1 * 3600, '1h Break'),
]

# 20 Spotify accounts
ACCOUNTS = [
    {'id': 1, 'email': 'sonic001@gmail.com', 'password': 'UO%9xpyKHgqS85x#', 'name': 'Listener 01'},
    {'id': 2, 'email': 'play002@gmail.com', 'password': 'wY9B@LosMsrFZUkM', 'name': 'Listener 02'},
    {'id': 3, 'email': 'music003@yahoo.com', 'password': 'oqp!ejRGU0RikKLD', 'name': 'Listener 03'},
    {'id': 4, 'email': 'vibe004@yahoo.com', 'password': '7tx#09Grq#Y4Z!A4', 'name': 'Listener 04'},
    {'id': 5, 'email': 'music005@gmail.com', 'password': 'g%jpKFosRrMGBPjG', 'name': 'Listener 05'},
    {'id': 6, 'email': 'play006@yahoo.com', 'password': 'UBOo55WurYkDyOcb', 'name': 'Listener 06'},
    {'id': 7, 'email': 'audio007@outlook.com', 'password': 'vS1LtqUXRwj!KpML', 'name': 'Listener 07'},
    {'id': 8, 'email': 'wave008@yahoo.com', 'password': 'Y5Ik%N4%xdPvHSMQ', 'name': 'Listener 08'},
    {'id': 9, 'email': 'rhythm009@gmail.com', 'password': 'BC09bqGHgqsIQtzn', 'name': 'Listener 09'},
    {'id': 10, 'email': 'rhythm010@gmail.com', 'password': '19MqJ9RdAZJ7ZCY0', 'name': 'Listener 10'},
    {'id': 11, 'email': 'beat011@yahoo.com', 'password': 'fff$UN53M%v$dzht', 'name': 'Listener 11'},
    {'id': 12, 'email': 'audio012@outlook.com', 'password': '2WLLZ1kbAg5LEG3D', 'name': 'Listener 12'},
    {'id': 13, 'email': 'audio013@gmail.com', 'password': 'BIuRo9uRuDVgf0Mv', 'name': 'Listener 13'},
    {'id': 14, 'email': 'vibe014@yahoo.com', 'password': 'aIAD1gTlv1R4!lG5', 'name': 'Listener 14'},
    {'id': 15, 'email': 'sonic015@gmail.com', 'password': 'zzP4eu2c1fLi15@6', 'name': 'Listener 15'},
    {'id': 16, 'email': 'wave016@outlook.com', 'password': 'B3BW@47%I#joq%PX', 'name': 'Listener 16'},
    {'id': 17, 'email': 'play017@outlook.com', 'password': 'X#%AN#yNx4v#aKqz', 'name': 'Listener 17'},
    {'id': 18, 'email': 'beat018@yahoo.com', 'password': 'yajcyJW1n!ZYQWzC', 'name': 'Listener 18'},
    {'id': 19, 'email': 'vibe019@hotmail.com', 'password': '9cpqqrP3LiAmmiWL', 'name': 'Listener 19'},
    {'id': 20, 'email': 'music020@hotmail.com', 'password': '%JP@GUUzZw08lGEw', 'name': 'Listener 20'},
]

class RealSpotifyStreaming:
    def __init__(self):
        self.running = False
        self.cycle = 0
        self.started_at = None
        
    def log(self, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {msg}")
        
    def stream_account_album(self, account, album, duration_secs):
        """Stream Spotify album using Playwright."""
        if not PLAYWRIGHT_AVAILABLE:
            self.log(f"❌ Playwright not available")
            return
            
        try:
            email = account['email']
            password = account['password']
            display = account['name']
            
            self.log(f"▶ [{display}] Starting Chrome for {album['name']}")
            
            with sync_playwright() as p:
                # Launch Chrome with anti-detect
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-gpu',
                        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    ]
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                )
                
                page = context.new_page()
                
                # Go to Spotify login
                page.goto('https://open.spotify.com/login', timeout=30000)
                time.sleep(2)
                
                # Login
                try:
                    page.fill('input[name="username"]', email, timeout=5000)
                except:
                    try:
                        page.fill('#login-username', email, timeout=5000)
                    except:
                        pass
                        
                time.sleep(1)
                
                try:
                    page.fill('input[name="password"]', password, timeout=5000)
                except:
                    try:
                        page.fill('#login-password', password, timeout=5000)
                    except:
                        pass
                        
                time.sleep(1)
                
                try:
                    page.click('button[type="submit"]', timeout=5000)
                except:
                    try:
                        page.click('#login-button', timeout=5000)
                    except:
                        pass
                        
                time.sleep(5)
                
                # Go to album
                self.log(f"▶ [{display}] Playing {album['name']}")
                page.goto(album['url'], timeout=30000)
                time.sleep(5)
                
                # Click play
                try:
                    page.click('[aria-label="Play"]', timeout=5000)
                except:
                    try:
                        page.click('button[data-testid="play-button"]', timeout=5000)
                    except:
                        pass
                
                # Stream for duration
                elapsed = 0
                interval = 60
                
                while elapsed < duration_secs and self.running:
                    time.sleep(interval)
                    elapsed += interval
                    remaining = (duration_secs - elapsed) // 60
                    self.log(f"▶ [{display}] {album['name']} - {elapsed//60}m elapsed, {remaining}m remaining")
                
                browser.close()
                
        except Exception as e:
            self.log(f"❌ [{account['name']}] Error: {e}")
    
    def run_phase(self, duration_secs, phase_name, is_play):
        """Run a schedule phase."""
        self.log(f"\n{'='*70}")
        self.log(f"⏰ PHASE: {phase_name} ({duration_secs//3600}h)")
        self.log(f"{'='*70}")
        
        if not is_play:
            self.log("💤 Break time")
            time.sleep(duration_secs)
            return
        
        # Start all threads
        threads = []
        for account in ACCOUNTS:
            for album in ALBUMS:
                t = threading.Thread(
                    target=self.stream_account_album,
                    args=(account, album, duration_secs)
                )
                threads.append(t)
                t.start()
                time.sleep(0.3)  # Stagger starts
        
        # Wait for phase
        start_time = time.time()
        while time.time() - start_time < duration_secs and self.running:
            time.sleep(10)
        
        self.log(f"✅ Phase {phase_name} complete")
    
    def run_cycle(self):
        """Run one schedule cycle."""
        self.cycle += 1
        self.log(f"\n{'#'*70}")
        self.log(f"🔄 CYCLE #{self.cycle}")
        self.log(f"{'#'*70}")
        
        for duration, name in SCHEDULE:
            if not self.running:
                break
            is_play = 'Break' not in name
            self.run_phase(duration, name, is_play)
    
    def start(self):
        """Start streaming."""
        self.log("="*70)
        self.log("🎙️ REAL SPOTIFY STREAMING - MARKETING MANAGER")
        self.log("   Real Chrome browsers, real Spotify accounts, real streams")
        self.log("="*70)
        self.log(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🎵 Albums: {', '.join(a['name'] for a in ALBUMS)}")
        self.log(f"👥 Accounts: {len(ACCOUNTS)}")
        self.log(f"📊 Total streams: {len(ACCOUNTS) * len(ALBUMS)}")
        self.log(f"⏰ Schedule: 15h→1h→4h→1h→3h→1h (repeat)")
        self.log("="*70)
        
        self.running = True
        self.started_at = datetime.now()
        
        while self.running:
            self.run_cycle()
    
    def stop(self):
        self.log("\n🛑 Stopping...")
        self.running = False

def main():
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright not installed. Run: pip install playwright")
        return
        
    streaming = RealSpotifyStreaming()
    
    try:
        streaming.start()
    except KeyboardInterrupt:
        streaming.stop()

if __name__ == '__main__':
    main()
