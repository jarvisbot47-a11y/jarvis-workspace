"""
Higgsfield Browser Automation
Uses Playwright to control the Higgsfield web interface for AI video generation.
Supports: Image-to-Video, Text-to-Video generation with browser-based UI.
"""
import os, time, tempfile, hashlib, requests
from pathlib import Path
from typing import Optional, Dict, Any, List

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

# ─── Configuration ────────────────────────────────────────────────────────────
HIGGSFIELD_URL = "https://higgsfield.ai"
HIGGSFIELD_GENERATE_URL = "https://higgsfield.ai/generate"
HIGGSFIELD_CREATE_VIDEO_URL = "https://higgsfield.ai/create/video"
HIGGSFIELD_LOGIN_URL = "https://higgsfield.ai/login"

# API credentials from config
try:
    from config import HIGGSFIELD_API_KEY_ID, HIGGSFIELD_API_KEY_SECRET
except ImportError:
    HIGGSFIELD_API_KEY_ID = "b8f2acb8-deb4-4095-b37a-f24627b45f2a"
    HIGGSFIELD_API_KEY_SECRET = "44775ce5c419d544b85ff653538763171fca28aac63393638a899d52a2dfab37"

# Default output directory
DEFAULT_OUTPUT_DIR = "/mnt/media-drive/MystikSingh/Content"
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)


class HiggsfieldAutomation:
    """
    Browser automation for Higgsfield AI video generation.
    
    Usage:
        hf = HiggsfieldAutomation(headless=False)
        hf.login()
        video_path = hf.generate_image_to_video(
            image_path="/path/to/image.jpg",
            prompt="Cinematic drone shot through city at night",
            duration=5
        )
        hf.close()
    """

    def __init__(self,
                 headless: bool = False,
                 output_dir: str = DEFAULT_OUTPUT_DIR,
                 browser_channel: str = "chromium",
                 user_data_dir: Optional[str] = None):
        """
        Initialize Higgsfield browser automation.
        
        Args:
            headless: Run browser in headless mode (no visible window)
            output_dir: Directory to save generated videos
            browser_channel: Browser channel ('chromium', 'chrome', 'msedge')
            user_data_dir: Path to browser profile (for persistent login)
        """
        self.headless = headless
        self.output_dir = output_dir
        self.browser_channel = browser_channel
        self.user_data_dir = user_data_dir
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        
        os.makedirs(self.output_dir, exist_ok=True)

    # ─── Browser Lifecycle ────────────────────────────────────────────────────

    def start(self) -> bool:
        """Launch browser and return success status."""
        try:
            self.playwright = sync_playwright().start()
            
            if self.user_data_dir and os.path.exists(self.user_data_dir):
                # Use persistent context with user profile (keeps cookies/login)
                self.context = self.playwright.chromium.launch_persistent_context(
                    self.user_data_dir,
                    channel=self.browser_channel,
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                    ],
                    viewport={"width": 1280, "height": 800},
                )
            else:
                # Launch with temporary context
                self.browser = self.playwright.chromium.launch(
                    channel=self.browser_channel,
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                    ],
                )
                self.context = self.browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
                )
            
            self.page = self.context.new_page()
            return True
        except Exception as e:
            print(f"Failed to start browser: {e}")
            return False

    def close(self) -> None:
        """Close browser and playwright."""
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
        self.is_logged_in = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    # ─── Navigation & Login ──────────────────────────────────────────────────

    def navigate_to(self, url: str, wait_time: float = 2.0) -> bool:
        """Navigate to a URL and wait for load."""
        if not self.page:
            return False
        try:
            # Use domcontentloaded since Higgsfield uses streaming/chunked responses
            # that prevent networkidle from completing
            self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            self.page.wait_for_timeout(wait_time * 1000)
            return True
        except Exception as e:
            print(f"Navigation failed: {e}")
            return False

    def check_login_status(self) -> bool:
        """Check if currently logged in to Higgsfield."""
        if not self.page:
            return False
        try:
            # If URL contains 'login', not logged in
            if 'login' in self.page.url.lower():
                return False
            # Look for user avatar or account-related elements
            self.page.wait_for_timeout(2000)
            # Check for logout/user button
            try:
                self.page.query_selector('[data-testid="user-menu"], [aria-label="Account"], button:has-text("Account")')
                return True
            except:
                pass
            # Check page content for login-related text
            content = self.page.content()
            if 'login' in self.page.url.lower() or 'sign in' in content.lower():
                return False
            return True
        except Exception:
            return False

    def login(self) -> bool:
        """
        Log in to Higgsfield using API key credentials.
        Navigates to login page and fills API key if available.
        """
        if not self.page and not self.start():
            return False

        print(f"Navigating to Higgsfield login: {HIGGSFIELD_LOGIN_URL}")
        self.navigate_to(HIGGSFIELD_LOGIN_URL, wait_time=3)
        
        # Check if already logged in
        if self.check_login_status():
            print("Already logged in!")
            self.is_logged_in = True
            return True

        print("Attempting to log in...")
        logged_in = False

        try:
            # Look for API key input field
            api_key_input = None
            try:
                api_key_input = self.page.wait_for_selector(
                    'input[placeholder*="API"], input[placeholder*="Key"], input[name*="api"], input[id*="api"]',
                    timeout=5000
                )
            except:
                pass
            
            if api_key_input:
                print("Found API key field, filling credentials...")
                api_key_input.fill(HIGGSFIELD_API_KEY_SECRET)
                self.page.wait_for_timeout(1000)
                
                # Look for email/API ID field
                try:
                    id_input = self.page.wait_for_selector(
                        'input[placeholder*="ID"], input[name*="id"], input[id*="id"]',
                        timeout=3000
                    )
                    id_input.fill(HIGGSFIELD_API_KEY_ID)
                except:
                    pass
                
                # Click submit
                try:
                    submit_btn = self.page.wait_for_selector(
                        'button[type="submit"], button:has-text("Login"), button:has-text("Sign In"), button:has-text("Continue")',
                        timeout=5000
                    )
                    submit_btn.click()
                    self.page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"Submit click failed: {e}")
            
            # Check login status again
            if self.check_login_status():
                print("Login successful!")
                self.is_logged_in = True
                logged_in = True
            else:
                print("Could not auto-login. Please login manually in the browser.")
                # Wait for manual login
                self._wait_for_manual_login()

        except Exception as e:
            print(f"Login error: {e}")
            self._wait_for_manual_login()

        return logged_in

    def _wait_for_manual_login(self, timeout: float = 120.0) -> bool:
        """Wait for user to manually log in."""
        print(f"Waiting up to {timeout}s for manual login...")
        start = time.time()
        while time.time() - start < timeout:
            if self.check_login_status():
                self.is_logged_in = True
                print("Manual login detected!")
                return True
            self.page.wait_for_timeout(3000)
        print("Manual login timed out.")
        return False

    def ensure_logged_in(self) -> bool:
        """Ensure we're logged in, attempt login if not."""
        if self.check_login_status():
            return True
        return self.login()

    # ─── Image to Video Generation ────────────────────────────────────────────

    def generate_image_to_video(
        self,
        image_path: str,
        prompt: str,
        duration: int = 5,
        output_filename: Optional[str] = None,
        wait_for_completion: bool = True,
        poll_interval: float = 5.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Generate video from image using Higgsfield web UI.
        
        Args:
            image_path: Path to source image file
            prompt: Text prompt describing desired motion
            duration: Video duration in seconds (5 or 10)
            output_filename: Custom output filename (auto-generated if None)
            wait_for_completion: Wait for generation to complete
            poll_interval: How often to poll for completion
            timeout: Max seconds to wait for completion
            
        Returns:
            Dict with: success, video_path, error, generation_id
        """
        result = {
            "success": False,
            "video_path": None,
            "error": None,
            "generation_id": None,
            "download_url": None,
        }

        if not self.page:
            if not self.start():
                result["error"] = "Failed to start browser"
                return result
            self.ensure_logged_in()

        try:
            # Navigate to the create/video page (video generation UI)
            print(f"Navigating to Higgsfield create/video page...")
            if not self.navigate_to(HIGGSFIELD_CREATE_VIDEO_URL, wait_time=3):
                # Fallback to main page then click Video tab
                if not self.navigate_to(HIGGSFIELD_GENERATE_URL, wait_time=3):
                    result["error"] = "Failed to navigate to Higgsfield"
                    return result
                if not self._navigate_to_video_page():
                    result["error"] = "Failed to navigate to video page"
                    return result

            # Upload image
            if not self._upload_image(image_path):
                result["error"] = "Failed to upload image"
                return result

            # Enter prompt
            self._enter_prompt(prompt)

            # Click generate
            generation_id = self._click_generate()
            if not generation_id:
                result["error"] = "Failed to initiate generation"
                return result
            result["generation_id"] = generation_id

            if wait_for_completion:
                print("Waiting for generation to complete...")
                video_info = self._wait_for_video(wait_time=poll_interval, timeout=timeout)
                if video_info:
                    # Download video
                    video_path = self._download_video(
                        video_info["download_url"],
                        output_filename or video_info.get("filename")
                    )
                    if video_path:
                        result["success"] = True
                        result["video_path"] = video_path
                        result["download_url"] = video_info["download_url"]
                    else:
                        result["error"] = "Video was ready but download failed"
                else:
                    result["error"] = "Generation did not complete within timeout"
            else:
                result["success"] = True
                result["video_path"] = None

        except Exception as e:
            result["error"] = str(e)

        return result


    def _navigate_to_video_page(self) -> bool:
        """Navigate to the video creation page /create/video."""
        try:
            # Navigate directly to the video creation URL
            if not self.navigate_to(HIGGSFIELD_CREATE_VIDEO_URL, wait_time=3):
                # Fallback: navigate to main page and click Video tab
                if not self.navigate_to(HIGGSFIELD_GENERATE_URL, wait_time=3):
                    return False
                self.page.evaluate("""
                    () => {
                        const buttons = document.querySelectorAll('button');
                        for (const b of buttons) {
                            if (b.textContent.trim() === 'Video') {
                                b.click();
                                return;
                            }
                        }
                    }
                """)
            
            print("On video creation page")
            
            # Wait for file inputs to appear (they're loaded dynamically)
            import time
            for _ in range(12):  # up to 6 seconds
                fi_count = self.page.evaluate(
                    "() => document.querySelectorAll('input[type=file]').length"
                )
                if fi_count > 0:
                    print(f"File inputs appeared: {fi_count}")
                    break
                self.page.wait_for_timeout(500)
            
            self.page.wait_for_timeout(500)  # Extra buffer
            return True
        except Exception as e:
            print(f"Video page navigation error: {e}")
            return False

    def _upload_image(self, image_path: str) -> bool:
        """Upload image file using the hidden file input on Higgsfield."""
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False

        try:
            # File inputs are hidden with sr-only class, use JS to find and set files
            # Higgsfield uses: input[type=file][accept*="image"]
            try:
                file_input = self.page.wait_for_selector(
                    'input[type="file"][accept*="image"]',
                    timeout=5000
                )
                if file_input:
                    file_input.set_input_files(image_path)
                    print(f"Uploaded image via Playwright: {image_path}")
                    self.page.wait_for_timeout(2500)
                    return True
            except Exception as e:
                print(f"Playwright selector failed: {e}")

            # Fallback: try any file input
            try:
                file_input = self.page.wait_for_selector(
                    'input[type="file"]',
                    timeout=3000
                )
                if file_input:
                    file_input.set_input_files(image_path)
                    print(f"Uploaded image via fallback: {image_path}")
                    self.page.wait_for_timeout(2500)
                    return True
            except:
                pass

            print("Could not find file input element")
            self.screenshot("upload_debug.png")
            return False

        except Exception as e:
            print(f"Upload error: {e}")
            self.screenshot("upload_error.png")
            return False

    def _enter_prompt(self, prompt: str) -> bool:
        """Enter the generation prompt using contenteditable on Higgsfield."""
        try:
            # Use JS to enter text - this is the most reliable method for contenteditable
            escaped_prompt = prompt.replace("'", "\'").replace('"', '\"').replace('\n', '\\n')
            
            success = self.page.evaluate(f"""
                () => {{
                    const editors = document.querySelectorAll('[contenteditable]');
                    for (const ed of editors) {{
                        if (ed.getAttribute('contenteditable') === 'true') {{
                            ed.focus();
                            ed.innerHTML = '';
                            document.execCommand('insertText', false, '{escaped_prompt}');
                            ed.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)
            
            if success:
                print(f"Entered prompt: {prompt[:50]}...")
                self.page.wait_for_timeout(500)
                return True
            
            print("Could not find prompt contenteditable")
            return False

        except Exception as e:
            print(f"Prompt entry error: {e}")
            return False

    def _select_duration(self, duration: int = 5) -> bool:
        """Select the video duration on /create/video page."""
        try:
            duration_str = f"{duration}s"
            
            # Click the duration button on the /create/video page
            result = self.page.evaluate(f"""
                () => {{
                    const buttons = document.querySelectorAll('button');
                    for (const b of buttons) {{
                        if (b.textContent.trim() === '{duration_str}') {{
                            b.click();
                            return 'clicked';
                        }}
                    }}
                    return null;
                }}
            """)
            
            if result:
                print(f"Selected {duration_str} duration via JS")
                self.page.wait_for_timeout(300)
                return True
            
            print(f"Could not select duration {duration_str} - using default")
            return False

        except Exception as e:
            print(f"Duration selection error: {e}")
            return False

    def _click_generate(self) -> Optional[str]:
        """Click the 'Generate' button on the video creation page."""
        try:
            # Use JS to find and click "Generate" button (primary action button)
            result = self.page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    for (const b of buttons) {
                        if (b.textContent.includes('Generate') && !b.textContent.includes('generating')) {
                            b.click();
                            return 'clicked-generate';
                        }
                    }
                    return null;
                }
            """)
            
            if result:
                print(f"Clicked '{result}' via JS")
                self.page.wait_for_timeout(3000)
                return "browser-generated"
            
            # Fallback: try "Start generating"
            result2 = self.page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    for (const b of buttons) {
                        if (b.textContent.includes('Start generating')) {
                            b.click();
                            return 'clicked-start';
                        }
                    }
                    return null;
                }
            """)
            
            if result2:
                print(f"Clicked 'Start generating' via JS")
                self.page.wait_for_timeout(3000)
                return "browser-generated"
            
            self.screenshot("generate_debug.png")
            return None

        except Exception as e:
            print(f"Generate click error: {e}")
            self.screenshot("generate_error.png")
            return None

    def _wait_for_video(self, wait_time: float = 5.0, timeout: float = 300.0) -> Optional[Dict[str, str]]:
        """
        Wait for generated video and return download info.
        Polls page for video element or download link.
        """
        start = time.time()
        last_check = 0
        
        while time.time() - start < timeout:
            elapsed = time.time() - start
            
            # Check for video element
            try:
                video_el = self.page.wait_for_selector(
                    'video[src], video source[src]',
                    timeout=2000
                )
                if video_el:
                    src = video_el.get_attribute('src') or video_el.query_selector('source').get_attribute('src')
                    if src:
                        print(f"Found video element with src: {src[:80]}...")
                        filename = self._generate_filename("mp4")
                        return {"download_url": src, "filename": filename}
            except:
                pass

            # Check for download link
            try:
                download_links = [
                    'a[href*=".mp4"]', 'a[href*="download"]', 'a[download]',
                    '[class*="download"] a', '[class*="output"] a',
                ]
                for selector in download_links:
                    links = self.page.query_selector_all(selector)
                    for link in links:
                        href = link.get_attribute('href') or ""
                        if href and ('.mp4' in href or 'video' in href or 'download' in href):
                            # Get the actual download URL
                            if href.startswith('//'):
                                href = 'https:' + href
                            elif href.startswith('/'):
                                href = 'https://higgsfield.ai' + href
                            filename = self._generate_filename("mp4")
                            print(f"Found download link: {href[:80]}...")
                            return {"download_url": href, "filename": filename}
            except:
                pass

            # Check for "completed" status text
            try:
                completed_selectors = [
                    '[class*="completed"]', '[class*="success"]',
                    '[class*="ready"]', 'text="Completed"',
                    'text="Done"', 'text="Download"',
                ]
                for sel in completed_selectors:
                    try:
                        el = self.page.query_selector(sel)
                        if el and el.is_visible():
                            href = el.get_attribute('href') if el.tag_name == 'a' else None
                            if href:
                                filename = self._generate_filename("mp4")
                                return {"download_url": href, "filename": filename}
                    except:
                        pass
            except:
                pass

            # Progress indicator (don't spam logs)
            if elapsed - last_check >= 10:
                print(f"  ... still waiting ({int(elapsed)}s elapsed)")
                last_check = elapsed
            
            self.page.wait_for_timeout(wait_time * 1000)

        print("Timeout waiting for video")
        return None

    def _generate_filename(self, ext: str = "mp4") -> str:
        """Generate a unique filename for output."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        rand = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return f"higgsfield_{ts}_{rand}.{ext}"

    def _download_video(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """Download video from URL to output directory."""
        if not url:
            return None
        
        filename = filename or self._generate_filename("mp4")
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            # Handle relative URLs
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = 'https://higgsfield.ai' + url
            
            print(f"Downloading video to: {output_path}")
            
            # Use requests for simple downloads
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=120, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded: {output_path}")
                return output_path
            else:
                print(f"Download failed: HTTP {response.status_code}")
                # Try Playwright's approach
                return self._download_via_browser(url, output_path)
                
        except Exception as e:
            print(f"Download error: {e}")
            # Fallback to browser download
            return self._download_via_browser(url, output_path)

    def _download_via_browser(self, url: str, output_path: str) -> Optional[str]:
        """Use browser to download file."""
        if not self.page:
            return None
        try:
            # Navigate to URL to trigger download or open video
            if url.startswith('/'):
                url = 'https://higgsfield.ai' + url
            self.page.goto(url, timeout=30000)
            self.page.wait_for_timeout(3000)
            
            # If we're on a video page, try to get the source
            video_els = self.page.query_selector_all('video')
            for video in video_els:
                src = video.get_attribute('src')
                if src and '.mp4' in src:
                    return self._download_video(src, output_path)
            
            return output_path if os.path.exists(output_path) else None
        except Exception as e:
            print(f"Browser download failed: {e}")
            return None

    # ─── Text to Video Generation ─────────────────────────────────────────────

    def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        output_filename: Optional[str] = None,
        wait_for_completion: bool = True,
        poll_interval: float = 5.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt using Higgsfield web UI.
        Uses the /create/video page - no image upload needed.
        """
        result = {
            "success": False,
            "video_path": None,
            "error": None,
            "generation_id": None,
            "download_url": None,
        }

        if not self.page:
            if not self.start():
                result["error"] = "Failed to start browser"
                return result
            self.ensure_logged_in()

        try:
            # Navigate to the video creation page
            print(f"Navigating to Higgsfield create/video page...")
            if not self.navigate_to(HIGGSFIELD_CREATE_VIDEO_URL, wait_time=3):
                result["error"] = "Failed to navigate to video page"
                return result

            # Enter prompt
            self._enter_prompt(prompt)

            # Select duration
            self._select_duration(duration)

            # Click generate
            generation_id = self._click_generate()
            if not generation_id:
                result["error"] = "Failed to initiate generation"
                return result
            result["generation_id"] = generation_id

            if wait_for_completion:
                print("Waiting for generation to complete...")
                video_info = self._wait_for_video(wait_time=poll_interval, timeout=timeout)
                if video_info:
                    video_path = self._download_video(
                        video_info["download_url"],
                        output_filename or video_info.get("filename")
                    )
                    if video_path:
                        result["success"] = True
                        result["video_path"] = video_path
                        result["download_url"] = video_info["download_url"]
                    else:
                        result["error"] = "Video was ready but download failed"
                else:
                    result["error"] = "Generation did not complete within timeout"
            else:
                result["success"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    # ─── Screenshot/Debug ──────────────────────────────────────────────────────

    def screenshot(self, filename: str) -> Optional[str]:
        """Take a screenshot and save to output dir."""
        if not self.page:
            return None
        try:
            path = os.path.join(self.output_dir, filename)
            self.page.screenshot(path=path, full_page=False)
            print(f"Screenshot saved: {path}")
            return path
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None

    def get_page_info(self) -> Dict[str, Any]:
        """Get current page URL, title, and visible text for debugging."""
        if not self.page:
            return {}
        try:
            return {
                "url": self.page.url,
                "title": self.page.title(),
                "html_preview": self.page.content()[:500],
            }
        except Exception:
            return {}


# ─── Convenience Functions ───────────────────────────────────────────────────

def generate_video(
    prompt: str,
    image_path: Optional[str] = None,
    duration: int = 5,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    headless: bool = False,
    wait: bool = True,
) -> Dict[str, Any]:
    """
    One-shot convenience function for video generation.
    """
    with HiggsfieldAutomation(headless=headless, output_dir=output_dir) as hf:
        hf.login()
        if image_path and os.path.exists(image_path):
            return hf.generate_image_to_video(
                image_path=image_path,
                prompt=prompt,
                duration=duration,
                wait_for_completion=wait,
            )
        else:
            return hf.generate_text_to_video(
                prompt=prompt,
                duration=duration,
                wait_for_completion=wait,
            )


def test_connection() -> bool:
    """Test if Higgsfield is accessible."""
    try:
        resp = requests.get(HIGGSFIELD_URL, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
