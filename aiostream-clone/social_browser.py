"""
Social Media Browser Module using Playwright
Persistent browser contexts for Instagram, Facebook, TikTok, YouTube
"""
import os, json, sqlite3, time, shutil
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import sys
sys_path = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(sys_path, "mystik_promotion.db")

# Browser profile storage
BROWSER_PROFILES_DIR = os.path.join(sys_path, "browser_profiles")
os.makedirs(BROWSER_PROFILES_DIR, exist_ok=True)


class SocialBrowserProfile:
    """
    A Playwright browser context for a specific social media platform.
    Saves cookies and state so you log in once and stay logged in.
    """

    PLATFORMS = ["instagram", "facebook", "tiktok", "youtube", "twitter"]

    def __init__(self, platform: str, profile_name: str = "default"):
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install")
        if platform not in self.PLATFORMS:
            raise ValueError(f"Platform must be one of: {self.PLATFORMS}")

        self.platform = platform
        self.profile_name = profile_name
        self.profile_dir = os.path.join(BROWSER_PROFILES_DIR, f"{platform}_{profile_name}")
        os.makedirs(self.profile_dir, exist_ok=True)

        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._headless = False

    # ─── Lifecycle ─────────────────────────────────────────────────────────

    def launch(self, headless: bool = False) -> "SocialBrowserProfile":
        """Launch browser with persistent context."""
        self._headless = headless
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            self.profile_dir,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/Los_Angeles",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        # Load cookies if saved
        cookies_path = self._cookies_path()
        if os.path.exists(cookies_path):
            with open(cookies_path, "r") as f:
                cookies = json.load(f)
            try:
                self._context.add_cookies(cookies)
            except Exception:
                pass  # Cookies may be stale; re-login
        return self

    def new_page(self) -> Page:
        """Open a new page in the existing context."""
        if not self._context:
            raise RuntimeError("Browser not launched. Call launch() first.")
        self._page = self._context.new_page()
        return self._page

    def save_cookies(self) -> None:
        """Persist current cookies to disk."""
        if not self._context:
            return
        cookies = self._context.cookies()
        with open(self._cookies_path(), "w") as f:
            json.dump(cookies, f)

    def close(self) -> None:
        """Save cookies and close browser."""
        self.save_cookies()
        self._update_db_status("logged_in")
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        self._context = None
        self._playwright = None

    def _cookies_path(self) -> str:
        return os.path.join(self.profile_dir, "cookies.json")

    # ─── Platform-specific login ────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        """Check if the profile is currently logged in via cookies."""
        if not os.path.exists(self._cookies_path()):
            return False
        return True

    def check_login_status(self) -> bool:
        """Navigate to platform and check if logged in."""
        if not self._context:
            self.launch()
        page = self.new_page()
        checks = {
            "instagram": "https://www.instagram.com/",
            "facebook":   "https://www.facebook.com/",
            "tiktok":     "https://www.tiktok.com/",
            "youtube":    "https://www.youtube.com/",
            "twitter":    "https://twitter.com/",
        }
        url = checks.get(self.platform, "")
        page.goto(url, wait_until="networkidle", timeout=30000)
        time.sleep(2)
        # Look for login indicator
        if self.platform == "instagram":
            logged_in = "sessionid" in page.context.cookies() or \
                        page.query_selector('a[href="/accounts/login/"]') is None
        elif self.platform == "facebook":
            logged_in = page.query_selector('[data-pagelet="RootFeed"]') is not None or \
                        page.query_selector('form[action*="login"]') is None
        elif self.platform == "tiktok":
            logged_in = page.query_selector('[data-e2e="profile-card"]') is not None or \
                        "For You" in page.content()
        elif self.platform == "youtube":
            logged_in = page.query_selector('# yt-chip-bar') is not None or \
                        page.query_selector('a[href="/login"]') is None
        elif self.platform == "twitter":
            logged_in = page.query_selector('[data-testid="primaryColumn"]') is not None
        else:
            logged_in = False
        page.close()
        return logged_in

    # ─── Database integration ────────────────────────────────────────────────

    def _update_db_status(self, status: str) -> None:
        """Save profile status to database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO social_browser_profiles
            (platform, profile_name, status, last_used)
            VALUES (?, ?, ?, ?)
        """, (self.platform, self.profile_name, status, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    # ─── Page helpers ────────────────────────────────────────────────────────

    def goto(self, url: str, wait: str = "networkidle", timeout: int = 30000) -> Page:
        """Navigate page to URL."""
        if not self._page:
            self.new_page()
        self._page.goto(url, wait_until=wait, timeout=timeout)
        return self._page

    def screenshot(self, path: str) -> str:
        """Take screenshot of current page."""
        if self._page:
            self._page.screenshot(path=path, full_page=False)
        return path

    def wait_for_selector(self, selector: str, timeout: int = 15000):
        """Wait for element."""
        if self._page:
            self._page.wait_for_selector(selector, timeout=timeout)

    def click(self, selector: str) -> None:
        if self._page:
            self._page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        if self._page:
            self._page.fill(selector, value)

    def text_content(self, selector: str) -> Optional[str]:
        if self._page:
            return self._page.text_content(selector)
        return None

    def query_selector(self, selector: str):
        if self._page:
            return self._page.query_selector(selector)
        return None

    def query_selector_all(self, selector: str):
        if not self._page:
            return []
        return self._page.query_selector_all(selector)


# ─── Global browser manager ──────────────────────────────────────────────────

_browsers: Dict[str, SocialBrowserProfile] = {}


def get_browser(platform: str, profile_name: str = "default",
                 headless: bool = False) -> SocialBrowserProfile:
    """Get or create a browser profile (singleton per platform/name)."""
    key = f"{platform}:{profile_name}"
    if key not in _browsers:
        _browsers[key] = SocialBrowserProfile(platform, profile_name)
        _browsers[key].launch(headless=headless)
    return _browsers[key]


def close_browser(platform: str, profile_name: str = "default") -> None:
    """Close and remove a browser profile."""
    key = f"{platform}:{profile_name}"
    if key in _browsers:
        _browsers[key].close()
        del _browsers[key]


def close_all_browsers() -> None:
    """Close all open browser profiles."""
    for key in list(_browsers.keys()):
        _browsers[key].close()
    _browsers.clear()


# ─── Social post helper ──────────────────────────────────────────────────────

class SocialPost:
    """
    Represents a social media post for automated publishing.
    Works with the browser to upload content.
    """

    def __init__(self, platform: str, content_path: str,
                 caption: str = "", schedule_time: Optional[datetime] = None):
        self.platform = platform
        self.content_path = content_path
        self.caption = caption
        self.schedule_time = schedule_time
        self.status = "pending"

    def post_now(self, browser: Optional[SocialBrowserProfile] = None) -> Dict[str, Any]:
        """Post immediately using browser."""
        if not browser:
            browser = get_browser(self.platform)
        return _post_to_platform(browser, self.content_path, self.caption)

    def save_to_db(self) -> int:
        """Save post to database for scheduling."""
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO scheduled_posts
            (platform, content_path, caption, scheduled_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            self.platform, self.content_path, self.caption,
            self.schedule_time.isoformat() if self.schedule_time else None,
            self.status, datetime.now().isoformat()
        ))
        conn.commit()
        post_id = cur.lastrowid
        conn.close()
        return post_id


def _post_to_platform(browser: SocialBrowserProfile,
                      content_path: str,
                      caption: str) -> Dict[str, Any]:
    """
    Post content using Playwright browser automation.
    This is a framework - actual selectors need per-platform verification.
    """
    page = browser.new_page()
    result = {"success": False, "platform": browser.platform}

    try:
        if browser.platform == "instagram":
            # Navigate to create post
            page.goto("https://www.instagram.com/", wait_until="networkidle")
            time.sleep(1)
            # Click create new post button
            page.click('svg[aria-label="New post"]', timeout=5000)
            time.sleep(2)
            # Upload file
            page.set_input_files('input[type="file"]', content_path, timeout=5000)
            time.sleep(3)
            result["success"] = True
            result["message"] = "Instagram post dialog opened"

        elif browser.platform == "tiktok":
            page.goto("https://www.tiktok.com/upload", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            page.set_input_files('input[type="file"]', content_path, timeout=10000)
            time.sleep(2)
            result["success"] = True
            result["message"] = "TikTok upload started"

        elif browser.platform == "facebook":
            page.goto("https://www.facebook.com/", wait_until="networkidle")
            time.sleep(2)
            # Click create post box
            page.click('[data-pagelet="ego_feed"] [role="button"]', timeout=5000)
            time.sleep(1)
            result["success"] = True
            result["message"] = "Facebook post dialog opened"

        elif browser.platform == "youtube":
            page.goto("https://studio.youtube.com/", wait_until="networkidle", timeout=30000)
            time.sleep(2)
            result["success"] = True
            result["message"] = "YouTube Studio loaded - manual upload recommended"

        else:
            result["message"] = f"Platform {browser.platform} not yet implemented"

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    return result
