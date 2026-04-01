"""
Content Creator Module - Main orchestration for music promo content automation
Integrates: Higgsfield AI, Whisper captions, FFmpeg video editor, Playwright browser
"""
import os, sqlite3, json, time, uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

sys_path = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(sys_path, "mystik_promotion.db")
MEDIA_DIR = os.path.join(sys_path, "media")
os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "raw"), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "edited"), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "exports"), exist_ok=True)

from higgsfield_client import HiggsfieldClient, ANIMATION_STYLES, VIDEO_QUALITY_PRESETS
from higgsfield_automation import HiggsfieldAutomation, DEFAULT_OUTPUT_DIR as HF_OUTPUT_DIR
from caption_generator import CaptionGenerator, transcribe_and_burn
from video_editor import VideoEditor, get_video_info, get_video_duration


# ─── Content Project ─────────────────────────────────────────────────────────

class ContentProject:
    """
    A content creation project - contains all assets and settings for a promo video.
    """

    def __init__(self, name: str, campaign_id: Optional[int] = None,
                 project_id: Optional[str] = None):
        self.id = project_id or str(uuid.uuid4())[:12]
        self.name = name
        self.campaign_id = campaign_id
        self.created_at = datetime.now().isoformat()
        self.status = "draft"

        # Assets
        self.source_image: Optional[str] = None
        self.source_video: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.album_art: Optional[str] = None

        # Settings
        self.output_format: str = "mp4"
        self.quality: str = "high"
        self.aspect_ratio: str = "9:16"  # 9:16 | 16:9 | 1:1
        self.platforms: List[str] = ["instagram", "tiktok"]
        self.color_grade: str = "cinematic"
        self.add_captions: bool = True
        self.caption_language: str = "en"
        self.watermark_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "name": self.name, "campaign_id": self.campaign_id,
            "created_at": self.created_at, "status": self.status,
            "source_image": self.source_image, "source_video": self.source_video,
            "audio_path": self.audio_path, "album_art": self.album_art,
            "output_format": self.output_format, "quality": self.quality,
            "aspect_ratio": self.aspect_ratio, "platforms": self.platforms,
            "color_grade": self.color_grade, "add_captions": self.add_captions,
            "caption_language": self.caption_language,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ContentProject":
        p = cls(name=data["name"], campaign_id=data.get("campaign_id"),
                project_id=data.get("id"))
        p.__dict__.update({k: v for k, v in data.items() if k not in ("id", "name")})
        return p


# ─── Content Creator ─────────────────────────────────────────────────────────

class ContentCreator:
    """
    Main content automation engine.
    Creates AI-generated videos, applies captions, formats for each platform.
    """

    def __init__(self, hf_api_key: Optional[str] = None):
        self.hf_key = hf_api_key or os.environ.get("HIGGSFIELD_API_KEY", "")
        self.hf_client: Optional[HiggsfieldClient] = None
        self._caption_gen: Optional[CaptionGenerator] = None

    # ─── Higgsfield AI ────────────────────────────────────────────────────────

    def init_higgsfield(self) -> None:
        """Initialize Higgsfield client."""
        if self.hf_key:
            self.hf_client = HiggsfieldClient(self.hf_key)

    # ─── Browser-based generation (PRIMARY - uses Playwright) ──────────────

    def generate_ai_video_browser(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        duration: int = 5,
        quality: str = "standard",
        style: Optional[str] = None,
        output_dir: Optional[str] = None,
        headless: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate AI video using Playwright browser automation.
        PRIMARY method - uses the Higgsfield web interface directly.
        Falls back to API if browser fails.
        
        Args:
            prompt: Description of desired video motion/scene
            image_path: Path to source image (for image-to-video), None for text-to-video
            duration: Video length in seconds (5 or 10)
            quality: Quality preset (draft|standard|hd|4k)
            style: Optional style hint
            output_dir: Where to save the video
            headless: Run browser without visible window
            
        Returns:
            Dict with success, video_path, error, generation_id
        """
        result = {"success": False, "video_path": None, "error": None, "generation_id": None}

        out_dir = output_dir or HF_OUTPUT_DIR
        
        try:
            with HiggsfieldAutomation(
                headless=headless,
                output_dir=out_dir,
            ) as hf:
                # Ensure logged in
                if not hf.ensure_logged_in():
                    result["error"] = "Not logged in to Higgsfield"
                    return result

                # Generate video
                if image_path and os.path.exists(image_path):
                    gen_result = hf.generate_image_to_video(
                        image_path=image_path,
                        prompt=prompt,
                        duration=duration,
                        wait_for_completion=True,
                        timeout=300.0,
                    )
                else:
                    gen_result = hf.generate_text_to_video(
                        prompt=prompt,
                        duration=duration,
                        wait_for_completion=True,
                        timeout=300.0,
                    )
                
                result.update(gen_result)

        except Exception as e:
            result["error"] = f"Browser automation error: {e}"

        return result

    def generate_ai_video(self,
                          prompt: str,
                          image_path: Optional[str] = None,
                          quality: str = "standard",
                          style: Optional[str] = None,
                          wait: bool = True,
                          use_browser: bool = True) -> Dict[str, Any]:
        """
        Generate AI video using Higgsfield.
        If image_path provided → image-to-video.
        Otherwise → text-to-video.
        
        Uses Playwright browser automation by default (use_browser=True).
        Set use_browser=False to use API-based generation.
        """
        # Default to browser-based generation
        if use_browser:
            duration_map = {"draft": 4, "standard": 4, "hd": 6, "4k": 6}
            duration = duration_map.get(quality, 5)
            return self.generate_ai_video_browser(
                prompt=prompt,
                image_path=image_path,
                duration=duration,
                quality=quality,
                style=style,
                headless=False,  # Visible for now
            )

        # API-based fallback
        if not self.hf_client:
            self.init_higgsfield()

        preset = VIDEO_QUALITY_PRESETS.get(quality, VIDEO_QUALITY_PRESETS["standard"])
        result = {"success": False}

        try:
            if image_path:
                # Image-to-video
                image_url = f"file://{os.path.abspath(image_path)}"
                init_result = self.hf_client.image_to_video(
                    image_url=image_url,
                    prompt=prompt,
                    duration_seconds=preset["duration"],
                    resolution=preset["resolution"],
                    motion_intensity=1.0 if style else 0.8,
                )
            else:
                # Text-to-video
                init_result = self.hf_client.text_to_video(
                    prompt=prompt,
                    duration_seconds=preset["duration"],
                    resolution=preset["resolution"],
                )

            gen_id = init_result.get("id")
            result["generation_id"] = gen_id

            if wait and gen_id:
                final = self.hf_client.wait_for_completion(gen_id, timeout=180)
                result.update({
                    "success": True,
                    "status": "completed",
                    "video_url": final.get("output", {}).get("url", ""),
                    "video_path": None,
                })
            else:
                result.update({"success": True, "status": "pending", "generation_id": gen_id})

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        return result

    def generate_ai_image(self, prompt: str,
                          size: tuple = (1024, 1024),
                          style: str = "natural",
                          negative_prompt: str = "") -> Dict[str, Any]:
        """Generate AI image for use as album art / thumbnail."""
        if not self.hf_client:
            self.init_higgsfield()

        result = {"success": False}
        try:
            init_result = self.hf_client.text_to_image(
                prompt=prompt, width=size[0], height=size[1],
                style=style, negative_prompt=negative_prompt
            )
            gen_id = init_result.get("id")
            if gen_id:
                final = self.hf_client.wait_for_completion(gen_id, timeout=120)
                result.update({
                    "success": True,
                    "status": "completed",
                    "image_url": final.get("output", {}).get("url", ""),
                    "generation_id": gen_id,
                })
            else:
                result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        return result

    # ─── Captions ────────────────────────────────────────────────────────────

    def get_caption_generator(self, model_size: str = "base") -> CaptionGenerator:
        """Get or create caption generator (reuses model)."""
        if self._caption_gen is None:
            self._caption_gen = CaptionGenerator(model_size=model_size)
        return self._caption_gen

    def add_captions_to_video(self,
                              video_path: str,
                              output_path: str,
                              model_size: str = "base",
                              language: str = "en",
                              position: str = "bottom") -> str:
        """
        Full pipeline: transcribe video → generate SRT → burn into video.
        Returns path to final captioned video.
        """
        return transcribe_and_burn(
            video_path=video_path,
            output_path=output_path,
            model_size=model_size,
            language=language,
            subtitle_format="srt",
            position=position,
        )

    # ─── Video Formatting ─────────────────────────────────────────────────────

    def format_for_platform(self,
                            video_path: str,
                            platform: str,
                            output_dir: Optional[str] = None,
                            color_grade: str = "cinematic",
                            quality: str = "high",
                            add_watermark: bool = False,
                            watermark_path: Optional[str] = None) -> str:
        """
        Format video for a specific platform.
        Platform → aspect ratio mapping:
          instagram, tiktok, reels, shorts → 9:16 vertical
          youtube → 16:9 horizontal
          facebook → 16:9 horizontal
        """
        output_dir = output_dir or os.path.join(MEDIA_DIR, "edited", platform)
        os.makedirs(output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{base}_{platform}.mp4")

        editor = VideoEditor(video_path, output_path)

        # Apply aspect ratio
        if platform in ("instagram", "tiktok"):
            editor.to_vertical(1080, 1920)
        elif platform in ("youtube", "facebook"):
            editor.to_horizontal(1920, 1080)
        elif platform == "reels":
            editor.to_vertical(1080, 1920)
        elif platform == "shorts":
            editor.to_vertical(1080, 1920)

        # Apply color grade
        if color_grade != "none":
            editor.colorgrade(color_grade)

        # Add watermark
        if add_watermark and watermark_path:
            editor.add_watermark(watermark_path, position="右下", opacity=0.7)

        # Render
        return editor.render(output_path=output_path, quality=quality)

    def create_lyric_video(self,
                           audio_path: str,
                           lyrics: List[Dict[str, Any]],
                           album_art: Optional[str] = None,
                           output_path: Optional[str] = None,
                           color_grade: str = "cinematic",
                           quality: str = "high") -> str:
        """
        Create a lyric video from audio + timed lyrics.
        lyrics: list of dicts with: start, end, text
        Uses FFmpeg to overlay timed text on a static image or generated background.
        """
        if output_path is None:
            base = os.path.splitext(os.path.basename(audio_path))[0]
            output_path = os.path.join(MEDIA_DIR, "edited", f"{base}_lyric.mp4")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        editor = VideoEditor(audio_path.replace(".mp3", ".mp4") if os.path.exists(audio_path.replace(".mp3", ".mp4")) else audio_path, output_path)

        # Use album art as background (or generate black bg)
        if album_art and os.path.exists(album_art):
            # For a lyric video we'd use ffmpeg's overlay filter with timeline
            pass

        # Add color grade
        editor.colorgrade(color_grade)

        # Build ASS subtitle filter for karaoke-style lyrics
        import tempfile
        ass_path = tempfile.mktemp(suffix=".ass")

        with open(ass_path, "w") as f:
            f.write(_lyrics_to_ass(lyrics))

        editor._filters.append(f"ass='{ass_path}'")

        result = editor.render(output_path=output_path, quality=quality)
        os.unlink(ass_path)
        return result

    # ─── Full pipeline ────────────────────────────────────────────────────────

    def create_promo_video(self, project: ContentProject) -> Dict[str, Any]:
        """
        Run the full content pipeline:
        1. Generate AI video (or use provided source)
        2. Format for each target platform
        3. Add captions
        4. Save outputs
        Returns dict with paths for each platform.
        """
        results: Dict[str, Any] = {"success": False, "outputs": {}}
        steps: List[str] = []

        try:
            # Step 1: Determine source video
            if project.source_video and os.path.exists(project.source_video):
                source_video = project.source_video
                steps.append(f"Using source video: {source_video}")
            elif project.source_image and os.path.exists(project.source_image):
                # Generate AI video from image
                steps.append("Generating AI video from image...")
                ai_result = self.generate_ai_video(
                    prompt=f"Professional music video shot, cinematic quality, {project.color_grade}",
                    image_path=project.source_image,
                    quality=project.quality,
                )
                if not ai_result.get("success"):
                    results["error"] = f"AI generation failed: {ai_result.get('error', 'unknown')}"
                    return results
                source_video = ai_result.get("video_path", project.source_image)
                steps.append(f"AI video generated: {ai_result.get('generation_id')}")
            else:
                results["error"] = "No source video or image provided"
                return results

            # Step 2: Format for each platform
            for platform in project.platforms:
                steps.append(f"Formatting for {platform}...")
                out = self.format_for_platform(
                    video_path=source_video,
                    platform=platform,
                    color_grade=project.color_grade,
                    quality=project.quality,
                    add_watermark=project.watermark_path is not None,
                    watermark_path=project.watermark_path,
                )

                # Step 3: Add captions if audio available
                if project.add_captions and project.audio_path:
                    captioned_out = out.replace(".mp4", "_captioned.mp4")
                    try:
                        captioned_out = self.add_captions_to_video(
                            video_path=out,
                            output_path=captioned_out,
                            language=project.caption_language,
                        )
                        out = captioned_out
                    except Exception as cap_err:
                        steps.append(f"Caption failed for {platform}: {cap_err}")

                results["outputs"][platform] = out
                steps.append(f"✓ {platform}: {out}")

            results["success"] = True
            results["steps"] = steps

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
            results["steps"] = steps

        return results

    # ─── Database helpers ────────────────────────────────────────────────────

    def save_project(self, project: ContentProject) -> int:
        """Save project to database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO content_projects
            (id, name, campaign_id, status, settings, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            project.id, project.name, project.campaign_id,
            project.status, json.dumps(project.to_dict()),
            project.created_at
        ))
        conn.commit()
        project_id = cur.lastrowid
        conn.close()
        return project_id

    def get_project(self, project_id: str) -> Optional[ContentProject]:
        """Load project from database."""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            data = dict(row)
            settings = json.loads(data.get("settings", "{}"))
            data.update(settings)
            return ContentProject.from_dict(data)
        return None

    def list_projects(self, status: Optional[str] = None) -> List[ContentProject]:
        """List all projects."""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if status:
            cur.execute("SELECT * FROM content_projects WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cur.execute("SELECT * FROM content_projects ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        projects = []
        for row in rows:
            data = dict(row)
            settings = json.loads(data.get("settings", "{}"))
            data.update(settings)
            projects.append(ContentProject.from_dict(data))
        return projects

    def update_project_status(self, project_id: str, status: str) -> None:
        """Update project status."""
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE content_projects SET status = ? WHERE id = ?", (status, project_id))
        conn.commit()
        conn.close()


# ─── ASS subtitle builder ─────────────────────────────────────────────────────

def _lyrics_to_ass(lyrics: List[Dict[str, Any]]) -> str:
    """Convert timed lyrics dict to ASS subtitle format."""
    lines = [
        "[Script Info]",
        "Title: Lyric Video",
        "ScriptType: v4.00+",
        "Collisions: Normal",
        "PlayDepth: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,2,3,2,10,10,30,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Text",
    ]
    for lyric in lyrics:
        start = _seconds_to_ass(lyric.get("start", 0))
        end = _seconds_to_ass(lyric.get("end", start + 3))
        text = lyric.get("text", "").replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
    return "\n".join(lines)


def _seconds_to_ass(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
