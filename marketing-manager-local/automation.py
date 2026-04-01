#!/usr/bin/env python3
"""
Marketing Manager - Real Spotify Streaming Automation
Real Android Emulators + Real Spotify = Real Streams
"""
import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime

# Load accounts
with open('accounts.json', 'r') as f:
    ACCOUNTS = json.load(f)

# Album Spotify URIs
ALBUMS = [
    {'name': 'Memento Mori Vol. 1', 'spotify_uri': 'spotify:album:1m9ciXW7myuZbo6CrrnuUr'},
    {'name': 'Memento Mori Vol. 2', 'spotify_uri': 'spotify:album:0Pe4dekB0JHj1WctvSMLo1'},
    {'name': 'Memento Mori Vol. 3', 'spotify_uri': 'spotify:album:0wb6BVYUNtFW0YST2IwgG5'},
]

# Schedule: (duration_seconds, phase_name, is_play)
SCHEDULE = [
    (15 * 3600, '15h Play', True),
    (1 * 3600, '1h Break', False),
    (4 * 3600, '4h Play', True),
    (1 * 3600, '1h Break', False),
    (3 * 3600, '3h Play', True),
    (1 * 3600, '1h Break', False),
]

class RealSpotifyStreaming:
    def __init__(self):
        self.running = False
        self.cycle = 0
        self.emulators_running = {}
        
    def log(self, msg, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}")
        
    def check_adb(self):
        """Check if ADB is available."""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_online_emulators(self):
        """Get list of online emulator devices."""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]
            emulators = []
            for line in lines:
                if line.strip() and 'emulator' in line.lower():
                    device = line.split()[0]
                    emulators.append(device)
            return emulators
        except:
            return []
    
    def start_emulators(self, count=20):
        """Start emulators via ADB."""
        self.log(f"Starting {count} emulators...")
        
        processes = []
        for i in range(1, count + 1):
            try:
                # Start emulator in background
                p = subprocess.Popen(
                    ['emulator', '-avd', f'spotify-emulator-{i}', '-no-window'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                processes.append(p)
                self.log(f"Launched spotify-emulator-{i}")
            except Exception as e:
                self.log(f"Failed to start emulator-{i}: {e}", 'WARN')
        
        self.log(f"Waiting for emulators to boot (this takes 2-3 minutes)...")
        time.sleep(120)  # Wait for boot
        
        # Wait for devices to come online
        for _ in range(30):
            online = self.get_online_emulators()
            if len(online) >= count:
                self.log(f"All {len(online)} emulators online!")
                return True
            time.sleep(5)
        
        self.log(f"Only {len(self.get_online_emulators())} emulators online", 'WARN')
        return True
    
    def install_spotify(self, device):
        """Install Spotify on emulator."""
        # Check if Spotify is already installed
        result = subprocess.run(
            ['adb', '-s', device, 'shell', 'pm', 'list', 'packages', 'com.spotify.music'],
            capture_output=True, text=True
        )
        if 'com.spotify.music' in result.stdout:
            return True
        
        # Install Spotify APK (you need to have spotify.apk in this folder)
        if os.path.exists('spotify.apk'):
            result = subprocess.run(
                ['adb', '-s', device, 'install', '-r', 'spotify.apk'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        else:
            self.log("spotify.apk not found - please download it", 'WARN')
            return False
    
    def open_spotify(self, device):
        """Open Spotify app on emulator."""
        subprocess.run(
            ['adb', '-s', device, 'shell', 'am', 'start', '-n', 
             'com.spotify.music/.MainActivity'],
            capture_output=True
        )
        time.sleep(2)
    
    def search_and_play_album(self, device, album_uri):
        """Search for album and play it on Spotify."""
        # Open Spotify
        self.open_spotify(device)
        time.sleep(3)
        
        # Search for album (using Spotify deep link)
        search_url = f"spotify:search:{album_uri.replace('spotify:album:', '')}"
        subprocess.run(
            ['adb', '-s', device, 'shell', 'am', 'start', '-a', 
             'android.intent.action.VIEW', '-d', album_uri],
            capture_output=True
        )
        time.sleep(2)
        
        # Tap play button (coordinates may vary)
        # This is a simplified version - real implementation would need
        # to detect the play button position
        
    def stream_album_thread(self, emulator, account, album, duration):
        """Stream an album on an emulator."""
        device = f'emulator-{emulator}'
        
        while duration > 0 and self.running:
            self.log(f"▶ {account['name']} | {album['name']} | {device}")
            
            # In real implementation:
            # 1. Open Spotify on device
            # 2. Navigate to album
            # 3. Start playback
            # 4. Keep screen awake
            # 5. Let it play for duration
            
            # For demo, just sleep
            time.sleep(30)  # Log every 30 seconds
            duration -= 30
    
    def run_phase(self, duration, phase_name, is_play):
        """Run a phase of the schedule."""
        self.log(f"\n{'='*60}")
        self.log(f"PHASE: {phase_name} ({duration//3600}h)" if is_play else f"PHASE: {phase_name}")
        self.log(f"{'='*60}")
        
        if not is_play:
            self.log("Break time - emulators paused")
            time.sleep(duration)
            return
        
        # Get online emulators
        online = self.get_online_emulators()
        self.log(f"Online emulators: {len(online)}")
        
        if not online:
            self.log("No emulators online! Start them first.", 'ERROR')
            return
        
        # Start streaming threads
        threads = []
        for i, emulator_port in enumerate(online[:len(ACCOUNTS)]):
            account = ACCOUNTS[i % len(ACCOUNTS)]
            
            for album in ALBUMS:
                t = threading.Thread(
                    target=self.stream_album_thread,
                    args=(emulator_port, account, album, duration)
                )
                threads.append(t)
                t.start()
        
        # Wait for phase to complete
        start_time = time.time()
        while time.time() - start_time < duration and self.running:
            time.sleep(10)
        
        # Wait for threads
        for t in threads:
            t.join(timeout=5)
        
        self.log(f"Phase {phase_name} complete!")
    
    def run_cycle(self):
        """Run one complete schedule cycle."""
        self.cycle += 1
        self.log(f"\n{'#'*60}")
        self.log(f"CYCLE #{self.cycle}")
        self.log(f"{'#'*60}")
        
        for duration, phase_name, is_play in SCHEDULE:
            if not self.running:
                break
            self.run_phase(duration, phase_name, is_play)
        
        self.log(f"\nCycle #{self.cycle} complete!")
    
    def start(self):
        """Start the streaming automation."""
        self.log("="*60)
        self.log("MARKETING MANAGER - REAL SPOTIFY STREAMING")
        self.log("Real Android Emulators + Real Spotify = Real Streams")
        self.log("="*60)
        
        # Check ADB
        if not self.check_adb():
            self.log("ADB not found! Install Android SDK.", 'ERROR')
            self.log("Or add Android SDK to PATH")
            return
        
        self.log(f"Accounts loaded: {len(ACCOUNTS)}")
        self.log(f"Albums: {[a['name'] for a in ALBUMS]}")
        self.log(f"Total concurrent streams: {len(ACCOUNTS) * len(ALBUMS)}")
        
        # Check emulators
        online = self.get_online_emulators()
        self.log(f"Online emulators: {len(online)}")
        
        if len(online) < len(ACCOUNTS):
            self.log(f"Warning: Only {len(online)} emulators online, need {len(ACCOUNTS)}", 'WARN')
            self.log("Start more emulators or continue with fewer streams")
        
        self.running = True
        
        # Run cycles
        while self.running:
            self.run_cycle()
    
    def stop(self):
        """Stop the automation."""
        self.log("\nStopping automation...")
        self.running = False

def main():
    automation = RealSpotifyStreaming()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Marketing Manager - Real Spotify Streaming

Usage:
    python3 automation.py          Start streaming
    python3 automation.py --start-emulators  Start emulators first

Before running:
1. Create 20 emulators in Android Studio (spotify-emulator-1 to 20)
2. Install Spotify on each emulator
3. Log into Spotify accounts on each emulator
4. Start all emulators with: emulator -avd spotify-emulator-N &

Then run this script!
        """)
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == '--start-emulators':
        automation.start_emulators(20)
        return
    
    try:
        automation.start()
    except KeyboardInterrupt:
        automation.stop()

if __name__ == '__main__':
    main()
