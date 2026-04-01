"""
Higgsfield AI API Client
Generate AI videos and images via Higgsfield (cloud.higgsfield.ai)
"""
import os, time, requests, json
from typing import Optional, Dict, Any, List

# API Configuration
HF_API_BASE = "https://platform.higgsfield.ai"
IMAGE_GEN_ENDPOINT = "/image/generation"
VIDEO_GEN_ENDPOINT = "/video/generation"
DEFAULT_MODEL = "dop"

# Load API credentials from config
try:
    from config import HIGGSFIELD_API_KEY_ID, HIGGSFIELD_API_KEY_SECRET
    DEFAULT_API_KEY_ID = HIGGSFIELD_API_KEY_ID
    DEFAULT_API_KEY_SECRET = HIGGSFIELD_API_KEY_SECRET
except ImportError:
    DEFAULT_API_KEY_ID = ""
    DEFAULT_API_KEY_SECRET = ""


class HiggsfieldClient:
    """Client for Higgsfield AI generation API."""

    def __init__(self, api_key: Optional[str] = None, api_key_id: Optional[str] = None):
        self.api_key = api_key or os.environ.get("HIGGSFIELD_API_KEY", "") or DEFAULT_API_KEY_SECRET
        self.api_key_id = api_key_id or os.environ.get("HIGGSFIELD_API_KEY_ID", "") or DEFAULT_API_KEY_ID
        if not self.api_key:
            raise ValueError("Higgsfield API key required. Set HIGGSFIELD_API_KEY env var.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    # ─── Text-to-Image ────────────────────────────────────────────────────────
    def text_to_image(self, prompt: str, model: str = "flux",
                      width: int = 1024, height: int = 1024,
                      steps: int = 50, negative_prompt: str = "",
                      style: str = "natural") -> Dict[str, Any]:
        """
        Generate image from text prompt.
        Returns dict with generation_id for polling.
        """
        payload = {
            "task": "text-to-image",
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "negative_prompt": negative_prompt,
            "style": style
        }
        resp = requests.post(
            f"{HF_API_BASE}/generations",
            headers=self.headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Image-to-Video ───────────────────────────────────────────────────────
    def image_to_video(self, image_url: str, prompt: str = "",
                       model: str = "image-to-video",
                       duration_seconds: int = 4,
                       resolution: str = "720p",
                       motion_intensity: float = 1.0,
                       enable_effects: bool = True) -> Dict[str, Any]:
        """
        Generate video from an image.
        animation_style_id can be one of the pre-built effects from Segmind docs.
        """
        payload = {
            "task": "image-to-video",
            "model": model,
            "image_url": image_url,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
            "resolution": resolution,
            "motion_intensity": motion_intensity,
            "enable_effects": enable_effects
        }
        resp = requests.post(
            f"{HF_API_BASE}/generations",
            headers=self.headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Text-to-Video ────────────────────────────────────────────────────────
    def text_to_video(self, prompt: str,
                      model: str = "text-to-video",
                      duration_seconds: int = 4,
                      resolution: str = "720p") -> Dict[str, Any]:
        """Generate video directly from text prompt."""
        payload = {
            "task": "text-to-video",
            "model": model,
            "prompt": prompt,
            "duration_seconds": duration_seconds,
            "resolution": resolution
        }
        resp = requests.post(
            f"{HF_API_BASE}/generations",
            headers=self.headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Video-to-Video ────────────────────────────────────────────────────────
    def video_to_video(self, video_url: str, prompt: str = "",
                       style: str = "cinematic",
                       strength: float = 0.7) -> Dict[str, Any]:
        """Apply AI style transfer to existing video."""
        payload = {
            "task": "video-to-video",
            "model": "video-to-video",
            "video_url": video_url,
            "prompt": prompt,
            "style": style,
            "strength": strength
        }
        resp = requests.post(
            f"{HF_API_BASE}/generations",
            headers=self.headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    # ─── Status Polling ────────────────────────────────────────────────────────
    def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Poll for generation status."""
        resp = requests.get(
            f"{HF_API_BASE}/generations/{generation_id}",
            headers=self.headers, timeout=15
        )
        resp.raise_for_status()
        return resp.json()

    def wait_for_completion(self, generation_id: str,
                            poll_interval: float = 3.0,
                            timeout: float = 120.0) -> Dict[str, Any]:
        """Poll until generation is complete."""
        start = time.time()
        while True:
            if time.time() - start > timeout:
                raise TimeoutError(f"Generation {generation_id} timed out after {timeout}s")
            result = self.get_generation_status(generation_id)
            status = result.get("status", "")
            if status == "completed":
                return result
            elif status == "failed":
                raise RuntimeError(f"Generation failed: {result.get('error', 'unknown')}")
            time.sleep(poll_interval)

    # ─── Wait & Download helper ────────────────────────────────────────────────
    def generate_and_wait(self, generation_fn, *args,
                          poll_interval: float = 3.0,
                          timeout: float = 120.0) -> Dict[str, Any]:
        """Call a generate method, then wait for completion and return result."""
        init_result = generation_fn(*args)
        gen_id = init_result.get("id")
        if not gen_id:
            return init_result
        return self.wait_for_completion(gen_id, poll_interval, timeout)

    # ─── Cancel ───────────────────────────────────────────────────────────────
    def cancel_generation(self, generation_id: str) -> bool:
        """Cancel a pending generation."""
        resp = requests.delete(
            f"{HF_API_BASE}/generations/{generation_id}",
            headers=self.headers, timeout=10
        )
        return resp.status_code in (200, 204)


# ─── Animation Style Presets (from Segmind/Higgsfield docs) ─────────────────
ANIMATION_STYLES = {
    "360_orbit":        "ea035f68-b350-40f1-b7f4-7dff999fdd67",
    "3d_rotation":      "2bae49e6-ffe7-42a8-a73f-d44632c4acaa",
    "abstract":         "7f8971a6-9e96-45b6-a05a-8f5c99b1e13d",
    "action_run":       "dc8d7d9c-ae0c-45fc-b780-7d470b171b45",
    "agent_reveal":     "65b0a5a3-953d-471c-86d5-967ab44d0dab",
    "arc_left":         "c5881721-05b1-47d9-94d6-0203863114e1",
    "arc_right":        "a85cb3f2-f2be-4ee2-b3b9-808fc6a81acc",
}

VIDEO_QUALITY_PRESETS = {
    "draft":    {"resolution": "480p",  "duration": 4},
    "standard": {"resolution": "720p",  "duration": 4},
    "hd":       {"resolution": "1080p", "duration": 6},
    "4k":       {"resolution": "4k",    "duration": 6},
}
