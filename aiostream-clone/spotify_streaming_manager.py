#!/usr/bin/env python3
"""
Real Spotify Streaming Manager - Marketing Manager
Uses Playwright to control real Chrome browsers with real Spotify Premium accounts.
Streams Mystik's albums on all accounts with anti-detection.
"""
import os, sys, json, time, threading, random, sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, List

sys_path = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(sys_path, "mystik_promotion.db")

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ─── Album URLs ────────────────────────────────────────────────────────────────
ALBUMS = [
    {'name': 'Memento Mori Vol. 1', 'url': 'https://open.spotify.com/album/1m9ciXW7myuZbo6CrrnuUr'},
    {'name': 'Memento Mori Vol. 2', 'url': 'https://open.spotify.com/album/0Pe4dekB0JHj1WctvSMLo1'},
    {'name': 'Memento Mori Vol. 3', 'url': 'https://open.spotify.com/album/0wb6BVYUNtFW0YST2IwgG5'},
]

SCHEDULE = [
    (15 * 3600, '15h Play', True),
    (1 * 3600,  '1h Break',  False),
    (4 * 3600,  '4h Play',  True),
    (1 * 3600,  '1h Break',  False),
    (3 * 3600,  '3h Play',  True),
    (1 * 3600,  '1h Break',  False),
]

# ─── DB helpers ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(account_id: int, album_url: str, event_type: str,
                 description: str, success: int = 1, **kwargs):
    """Log real streaming activity to the database."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO activity_logs
            (event_type, platform, account_id, description, streams_delta,
             listeners_delta, success, duration_ms, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type, 'Spotify', account_id, description,
            kwargs.get('streams_delta', 1),
            kwargs.get('listeners_delta', 0),
            success,
            kwargs.get('duration_ms', 0),
            json.dumps(kwargs.get('metadata', {})),
            datetime.now().isoformat()
        ))
        conn.commit()
    except Exception:
        pass  # Don't crash streaming over DB logging
    finally:
        conn.close()


def update_account_stats(account_id: int, streams_delta: int = 0):
    """Update account total play counts in DB."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE streaming_accounts
            SET total_plays = total_plays + ?,
                last_active = ?
            WHERE id = ?
        """, (streams_delta, datetime.now().isoformat(), account_id))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


# ─── Single-account streaming ──────────────────────────────────────────────────
class SpotifyStreamer:
    """
    Streams Spotify on one account using Playwright.
    Logs in → navigates album → clicks play → maintains stream for duration.
    """

    def __init__(self, account: dict, album: dict,
                 profile: Optional[dict] = None,
                 proxy: Optional[dict] = None,
                 headless: bool = True):
        self.account = account
        self.album = album
        self.profile = profile or {}
        self.proxy = proxy
        self.headless = headless
        self.running = False
        self.elapsed = 0
        self.log_file = os.path.join(sys_path, 'logs', 'streaming.log')

        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def _log(self, msg: str):
        ts = datetime.now().strftime('%H:%M:%S')
        line = f"[{ts}] [{self.account.get('display_name','?')}] [{self.album['name']}] {msg}"
        print(f"  {line}")
        try:
            with open(self.log_file, 'a') as f:
                f.write(line + '\n')
        except Exception:
            pass

    def _get_fingerprint_headers(self) -> dict:
        """Build anti-detect browser context."""
        ua = self.profile.get('user_agent') or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        viewport = {
            'width': self.profile.get('screen_width', 1920),
            'height': self.profile.get('screen_height', 1080),
        }
        ctx_options = {
            'viewport': viewport,
            'user_agent': ua,
            'locale': 'en-US',
            'timezone_id': self.profile.get('timezone', 'America/Los_Angeles'),
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }

        # Proxy support
        if self.proxy and self.proxy.get('proxy_url'):
            proxy_url = self.proxy['proxy_url']
            if not proxy_url.startswith('http'):
                proxy_url = f"http://{proxy_url}"
            ctx_options['proxy'] = {'server': proxy_url}

        return ctx_options

    def _do_login(self, page) -> bool:
        """Attempt to log into Spotify. Returns True if successful."""
        email = self.account.get('email') or self.account.get('username')
        password = self.account.get('password')

        if not email or not password:
            self._log("No credentials available")
            return False

        try:
            page.goto('https://open.spotify.com/login', wait_until='domcontentloaded', timeout=30000)
            time.sleep(random.uniform(1.5, 3.0))

            # Fill username - try multiple selectors
            filled = False
            for selector in ['#login-username', 'input[name="username"]', '[data-testid="login-username"]']:
                try:
                    page.fill(selector, email, timeout=3000)
                    filled = True
                    break
                except Exception:
                    continue

            if not filled:
                self._log(f"Could not fill username field")
                return False

            time.sleep(random.uniform(0.5, 1.5))

            # Fill password
            for selector in ['#login-password', 'input[name="password"]', '[data-testid="login-password"]']:
                try:
                    page.fill(selector, password, timeout=3000)
                    break
                except Exception:
                    continue

            time.sleep(random.uniform(0.3, 0.8))

            # Submit
            for selector in ['#login-button', 'button[type="submit"]', '[data-testid="login-button"]']:
                try:
                    page.click(selector, timeout=3000)
                    break
                except Exception:
                    continue

            # Wait for redirect to home
            time.sleep(random.uniform(4.0, 7.0))

            # Check if logged in (URL changed from /login)
            if '/login' in page.url:
                self._log(f"Login may have failed - still on login page")
                return False

            self._log(f"Logged in as {email}")
            return True

        except Exception as e:
            self._log(f"Login error: {e}")
            return False

    def _play_album(self, page) -> bool:
        """Navigate to album and click play."""
        try:
            album_url = self.album['url']
            self._log(f"Navigating to {album_url}")
            page.goto(album_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(random.uniform(3.0, 5.0))

            # Scroll slightly to reveal play button
            page.evaluate('window.scrollBy(0, 200)')
            time.sleep(1.0)

            # Click play - try multiple selectors
            played = False
            for selector in [
                '[aria-label="Play"]',
                '[data-testid="play-button"]',
                'button[data-testid="play-button"]',
                '.ButtonInner-sc-1g9xqth-0',
            ]:
                try:
                    page.click(selector, timeout=3000)
                    played = True
                    break
                except Exception:
                    continue

            if played:
                self._log(f"Playback started")
                return True
            else:
                self._log(f"Could not find play button")
                return False

        except Exception as e:
            self._log(f"Play error: {e}")
            return False

    def _keep_alive(self, page, duration_secs: int) -> int:
        """
        Keep the stream alive for `duration_secs`.
        Periodically checks if page is still active, scrolls slightly.
        Returns actual seconds streamed.
        """
        self.running = True
        self.elapsed = 0
        interval = 60  # Check every 60 seconds
        streamed_secs = 0

        while self.elapsed < duration_secs and self.running:
            time.sleep(min(interval, duration_secs - self.elapsed))
            if not self.running:
                break

            self.elapsed += interval
            streamed_secs = min(self.elapsed, duration_secs)

            # Verify page still has Spotify content
            try:
                title = page.title()
                if 'Spotify' not in title and len(title) > 0:
                    self._log(f"Warning: unexpected page title '{title}'")

                # Occasional subtle interaction to mimic human
                if random.random() < 0.1:  # 10% chance each check
                    page.evaluate('window.scrollBy(0, -100)')
                    time.sleep(0.5)
                    page.evaluate('window.scrollBy(0, 100)')

            except Exception:
                self._log("Page may have closed")
                break

            mins_done = self.elapsed // 60
            mins_left = (duration_secs - self.elapsed) // 60
            self._log(f"Streaming: {mins_done}m done, ~{mins_left}m remaining")

        return streamed_secs

    def stream(self, duration_secs: int) -> Dict[str, Any]:
        """
        Full streaming cycle: launch browser → login → play → stream → close.
        Returns result dict.
        """
        result = {'success': False, 'account_id': self.account.get('id'),
                  'album': self.album['name'], 'streamed_secs': 0, 'error': None}

        if not PLAYWRIGHT_AVAILABLE:
            result['error'] = 'Playwright not installed'
            return result

        browser = None
        try:
            self._log(f"Starting stream for {duration_secs}s")

            ctx_options = self._do_login(page=None)  # placeholder until context created
            ctx_options = self._get_fingerprint_headers()

            with sync_playwright() as p:
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu',
                    '--disable-battery',
                    '--disable-software-rasterizer',
                    '--disable-web-security',
                ]

                browser = p.chromium.launch(
                    headless=self.headless,
                    args=browser_args
                )

                context = browser.new_context(**ctx_options)
                page = context.new_page()

                # Login
                if not self._do_login(page):
                    # Try cookies approach if login failed
                    pass

                # Play album
                if not self._play_album(page):
                    result['error'] = 'Could not start playback'
                    browser.close()
                    return result

                # Keep stream alive
                streamed = self._keep_alive(page, duration_secs)
                result['streamed_secs'] = streamed
                result['success'] = streamed > 0

                # Log to DB
                if result['success']:
                    log_activity(
                        self.account.get('id'), self.album['url'],
                        'play:spotify',
                        f'Streamed {self.album["name"]} for {streamed}s',
                        success=1,
                        streams_delta=1,
                        duration_ms=streamed * 1000,
                        metadata={'album': self.album['name'], 'account': self.account.get('email')}
                    )
                    update_account_stats(self.account.get('id'), streams_delta=1)

                browser.close()

        except Exception as e:
            result['error'] = str(e)
            self._log(f"Error: {e}")

        finally:
            try:
                if browser:
                    browser.close()
            except Exception:
                pass

        return result


# ─── Global Streaming Manager ─────────────────────────────────────────────────
class StreamingManager:
    """
    Singleton manager for all real Spotify streaming operations.
    Loads accounts from DB and orchestrates concurrent real streams.
    Controlled via Flask app routes.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.running = False
        self.paused = False
        self.current_phase = 'stopped'
        self.cycle = 0
        self.started_at = None
        self.phase_start = None
        self.threads: List[threading.Thread] = []
        self._stop_event = threading.Event()

    def load_accounts(self) -> List[dict]:
        """Load active Spotify accounts from database."""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM streaming_accounts
            WHERE platform = 'Spotify' AND status = 'active'
            ORDER BY id
        """)
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def load_profiles(self) -> List[dict]:
        """Load anti-detect profiles."""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM anti_detect_profiles WHERE is_default = 0 OR is_default IS NULL")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def load_proxies(self) -> List[dict]:
        """Load active proxies."""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM proxies WHERE is_active = 1")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def log(self, msg: str):
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{ts}] [Manager] {msg}")

    def start_phase(self, duration_secs: int, phase_name: str, do_play: bool):
        """Start a schedule phase across all accounts."""
        if not do_play:
            self.log(f"⏸️  BREAK: {phase_name}")
            self.current_phase = f"Break: {phase_name}"
            time.sleep(duration_secs)
            return

        accounts = self.load_accounts()
        profiles = self.load_profiles()
        proxies = self.load_proxies()

        if not accounts:
            self.log("⚠️  No active Spotify accounts found in database!")
            return

        self.log(f"▶  PHASE START: {phase_name} ({len(accounts)} accounts × {len(ALBUMS)} albums)")
        self.current_phase = phase_name
        self.phase_start = time.time()

        # Launch streams for every account × album combo
        self.threads = []
        for account in accounts:
            profile = random.choice(profiles) if profiles else None
            proxy = random.choice(proxies) if proxies else None

            for album in ALBUMS:
                streamer = SpotifyStreamer(
                    account=account,
                    album=album,
                    profile=profile,
                    proxy=proxy,
                    headless=True,
                )

                t = threading.Thread(
                    target=self._run_stream,
                    args=(streamer, duration_secs),
                    daemon=True,
                )
                self.threads.append(t)
                t.start()

                # Stagger starts to avoid simultaneous logins
                time.sleep(random.uniform(0.5, 2.0))

        # Wait for phase to complete
        elapsed = 0
        while elapsed < duration_secs:
            if self._stop_event.is_set():
                self.log("🛑 Stop requested")
                break
            time.sleep(10)
            elapsed = int(time.time() - self.phase_start)

        # Wait for threads
        for t in self.threads:
            t.join(timeout=30)

        self.log(f"✅ Phase complete: {phase_name}")

    def _run_stream(self, streamer: SpotifyStreamer, duration_secs: int):
        """Thread target for a single stream."""
        try:
            streamer.stream(duration_secs)
        except Exception as e:
            streamer._log(f"Thread error: {e}")

    def run_cycle(self):
        """Run one full schedule cycle."""
        self.cycle += 1
        cycle_started = datetime.now()
        self.log(f"\n{'#'*70}")
        self.log(f"🔄 CYCLE #{self.cycle} started at {cycle_started.strftime('%H:%M')}")
        self.log(f"{'#'*70}")

        for duration, name, do_play in SCHEDULE:
            if self._stop_event.is_set():
                break
            self.start_phase(duration, name, do_play)

        self.log(f"✅ Cycle #{self.cycle} complete")

    def start(self, background: bool = True):
        """Start streaming automation."""
        if self.running:
            self.log("Already running")
            return

        self.running = True
        self.paused = False
        self._stop_event.clear()
        self.started_at = datetime.now()
        self.cycle = 0

        self.log("="*70)
        self.log("🎙️  REAL SPOTIFY STREAMING STARTED")
        self.log(f"   Albums: {[a['name'] for a in ALBUMS]}")
        self.log(f"   Schedule: 15h→1h→4h→1h→3h→1h (repeat)")
        self.log("="*70)

        if background:
            t = threading.Thread(target=self._run_loop, daemon=True)
            t.start()
        else:
            self._run_loop()

    def _run_loop(self):
        """Main loop - runs cycles until stopped."""
        while self.running and not self._stop_event.is_set():
            try:
                self.run_cycle()
            except Exception as e:
                self.log(f"⚠️  Cycle error: {e}")
                time.sleep(30)

    def stop(self):
        """Stop all streaming."""
        self.log("🛑 Stop requested...")
        self.running = False
        self._stop_event.set()
        # Stop all active streamers
        for t in self.threads:
            try:
                t.join(timeout=2)
            except Exception:
                pass
        self.current_phase = 'stopped'
        self.log("✅ Stopped")

    def pause(self):
        self.paused = True
        self.current_phase = 'paused'

    def resume(self):
        self.paused = False

    def get_status(self) -> Dict[str, Any]:
        """Get current streaming status."""
        uptime = 0
        if self.started_at:
            uptime = int((datetime.now() - self.started_at).total_seconds())

        accounts = self.load_accounts()

        return {
            'running': self.running,
            'paused': self.paused,
            'current_phase': self.current_phase,
            'cycle': self.cycle,
            'uptime_secs': uptime,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'accounts_loaded': len(accounts),
            'total_streams': len(accounts) * len(ALBUMS),
            'albums': [a['name'] for a in ALBUMS],
        }

    def test_single_stream(self, account_id: int, album_url: str,
                           duration_secs: int = 30) -> Dict[str, Any]:
        """
        Test a single stream on one account for `duration_secs`.
        Used to verify setup before starting full automation.
        """
        accounts = self.load_accounts()
        account = next((a for a in accounts if a['id'] == account_id), None)
        if not account:
            return {'success': False, 'error': f'Account {account_id} not found'}

        album = next((a for a in ALBUMS if a['url'] == album_url), None)
        if not album:
            return {'success': False, 'error': f'Album URL not found'}

        profiles = self.load_profiles()
        proxies = self.load_proxies()

        streamer = SpotifyStreamer(
            account=account,
            album=album,
            profile=random.choice(profiles) if profiles else None,
            proxy=random.choice(proxies) if proxies else None,
            headless=False,  # Visible for testing
        )

        return streamer.stream(duration_secs)


# ─── Global singleton ──────────────────────────────────────────────────────────
_manager = None

def get_streaming_manager() -> StreamingManager:
    global _manager
    if _manager is None:
        _manager = StreamingManager()
    return _manager
