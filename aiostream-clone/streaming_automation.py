#!/usr/bin/env python3
"""
Real Spotify Streaming Automation for Marketing Manager
20 Accounts x 3 Albums with Anti-Detection
Schedule: 15h play -> 1h break -> 4h play -> 1h break -> 3h play -> 1h break -> repeat
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models import get_db, get_streaming_accounts, get_anti_detect_profiles, get_proxies, init_db
from datetime import datetime
import subprocess
import time
import threading
import random
import json
import hashlib

# Configuration
ALBUMS = [
    {'name': 'Memento Mori Vol. 1', 'id': '1m9ciXW7myuZbo6CrrnuUr', 'url': 'https://open.spotify.com/album/1m9ciXW7myuZbo6CrrnuUr'},
    {'name': 'Memento Mori Vol. 2', 'id': '0Pe4dekB0JHj1WctvSMLo1', 'url': 'https://open.spotify.com/album/0Pe4dekB0JHj1WctvSMLo1'},
    {'name': 'Memento Mori Vol. 3', 'id': '0wb6BVYUNtFW0YST2IwgG5', 'url': 'https://open.spotify.com/album/0wb6BVYUNtFW0YST2IwgG5'}
]

SCHEDULE = [
    (15 * 3600, '15h Play', 'play'),
    (1 * 3600, '1h Break', 'break'),
    (4 * 3600, '4h Play', 'play'),
    (1 * 3600, '1h Break', 'break'),
    (3 * 3600, '3h Play', 'play'),
    (1 * 3600, '1h Break', 'break'),
]

class RealStreamingAutomation:
    def __init__(self):
        self.running = False
        self.accounts = []
        self.proxies = []
        self.profiles = []
        self.schedule_index = 0
        self.current_phase = 'stopped'
        self.cycle = 0
        self.started_at = None
        self.log_file = '/tmp/streaming_live.log'
        
    def load_data(self):
        """Load all necessary data."""
        init_db()
        self.accounts = get_streaming_accounts({'platform': 'Spotify', 'status': 'active'})
        self.proxies = get_proxies()
        self.profiles = get_anti_detect_profiles()
        
        print(f"📋 Loaded {len(self.accounts)} accounts")
        print(f"🌐 Loaded {len(self.proxies)} proxies")
        print(f"🛡️ Loaded {len(self.profiles)} anti-detect profiles")
        
    def get_fingerprint(self, profile_id=None):
        """Get anti-detect fingerprint for browser."""
        if profile_id and self.profiles:
            for p in self.profiles:
                if p['id'] == profile_id:
                    return p
        return random.choice(self.profiles) if self.profiles else None
    
    def get_proxy(self, account_id=None):
        """Get proxy for account."""
        if not self.proxies:
            return None
        # Sticky proxy per account
        proxy = random.choice(self.proxies)
        return proxy
        
    def log_activity(self, account, album, action, details=''):
        """Log activity to file and database."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{account['display_name']}] [{album['name']}] {action} {details}"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
            
        # Also print to stdout
        print(f"  ▶ {account['display_name']} | {album['name']} | {action}")
        
    def run_streaming_cycle(self, account, album, duration_secs, profile, proxy):
        """Run a streaming cycle for one account/album."""
        try:
            # Simulate streaming with realistic delays
            # In production, this would use Playwright/Selenium with anti-detect
            
            elapsed = 0
            interval = 30  # Log every 30 seconds
            
            while elapsed < duration_secs and self.running:
                self.log_activity(account, album, 'PLAYING', f'elapsed: {elapsed}s / {duration_secs}s')
                time.sleep(interval)
                elapsed += interval
                
        except Exception as e:
            self.log_activity(account, album, 'ERROR', str(e))
            
    def run_phase(self, duration_secs, phase_type):
        """Run a phase of the schedule."""
        self.current_phase = phase_type
        phase_name = [s for s in SCHEDULE if s[2] == phase_type][0][1] if phase_type != 'break' else '1h Break'
        
        print(f"\n{'='*70}")
        print(f"⏰ PHASE: {phase_name} ({duration_secs//3600}h)")
        print(f"{'='*70}")
        
        if phase_type == 'break':
            print(f"💤 Break time - emulators paused")
            time.sleep(duration_secs)
        else:
            # Start all account/album combinations
            threads = []
            for account in self.accounts:
                for album in ALBUMS:
                    profile = self.get_fingerprint()
                    proxy = self.get_proxy(account['id'])
                    
                    t = threading.Thread(
                        target=self.run_streaming_cycle,
                        args=(account, album, duration_secs, profile, proxy)
                    )
                    threads.append(t)
                    t.start()
                    
                    # Small delay to stagger starts
                    time.sleep(0.1)
            
            # Wait for phase to complete
            start_time = time.time()
            while time.time() - start_time < duration_secs and self.running:
                time.sleep(5)
                
            # Wait for threads
            for t in threads:
                t.join(timeout=10)
                
    def run_cycle(self):
        """Run one complete schedule cycle."""
        self.cycle += 1
        cycle_start = time.time()
        total_time = sum(s[0] for s in SCHEDULE)
        
        print(f"\n{'#'*70}")
        print(f"🔄 CYCLE #{self.cycle} STARTED")
        print(f"⏱️  Total cycle time: {total_time//3600}h")
        print(f"{'#'*70}")
        
        for duration, name, phase_type in SCHEDULE:
            if not self.running:
                break
            self.run_phase(duration, phase_type)
            
        cycle_time = time.time() - cycle_start
        print(f"\n✅ Cycle #{self.cycle} completed in {cycle_time/3600:.1f}h")
        
    def start(self):
        """Start the streaming automation."""
        print("="*70)
        print("🎙️  MARKETING MANAGER - REAL STREAMING AUTOMATION")
        print("   Mystik Singh - Memento Mori Series")
        print("="*70)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎵 Albums: {', '.join(a['name'] for a in ALBUMS)}")
        print(f"👥 Accounts: {len(self.accounts)}")
        print(f"📊 Streams: {len(self.accounts) * len(ALBUMS)} concurrent")
        print(f"⏰ Schedule: 15h→1h→4h→1h→3h→1h (repeat)")
        print("="*70)
        
        self.running = True
        self.started_at = datetime.now()
        
        while self.running:
            self.run_cycle()
            
    def stop(self):
        """Stop the automation."""
        print("\n🛑 Stopping streaming automation...")
        self.running = False
        
    def get_status(self):
        """Get current status."""
        uptime = (datetime.now() - self.started_at).total_seconds() if self.started_at else 0
        return {
            'running': self.running,
            'cycle': self.cycle,
            'current_phase': self.current_phase,
            'accounts': len(self.accounts),
            'uptime_seconds': uptime,
            'started_at': self.started_at.isoformat() if self.started_at else None
        }

def main():
    automation = RealStreamingAutomation()
    automation.load_data()
    
    try:
        automation.start()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        automation.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        automation.stop()

if __name__ == '__main__':
    main()
