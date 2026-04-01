"""
Video Editor using FFmpeg
Hollywood-quality video formatting: 9:16 vertical, 16:9 horizontal,
letterboxing, LUTs, transitions, effects
"""
import os, subprocess, tempfile, shutil
from typing import Optional, List, Dict, Any


# ─── LUT files (basic colour grading .cube files) ─────────────────────────────
LUT_DIR = os.path.join(os.path.dirname(__file__), "luts")
os.makedirs(LUT_DIR, exist_ok=True)

DEFAULT_LUTS = {
    "none":         None,
    "cinematic":    None,   # generated via curves
    "warm_vintage": None,
    "cool_modern":  None,
    "high_contrast": None,
    "teal_orange":  None,   # Hollywood blockbuster look
}


# ─── FFmpeg filter builders ──────────────────────────────────────────────────

def _run_ffmpeg(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run FFmpeg command, return result."""
    result = subprocess.run(
        cmd, capture_output=True, text=True
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr}")
    return result


class VideoEditor:
    """
    High-quality video processing via FFmpeg.
    Supports: resize, crop, pad, letterbox, trim, concat, LUT, transitions.
    """

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        self.input_path = input_path
        self.output_path = output_path or self._default_output()
        self._filters: List[str] = []
        self._audio_codec = "aac"
        self._video_codec = "libx264"
        self._preset = "slow"   # slower = better compression/quality
        self._crf = 18          # lower = better quality (0-51)
        self._pix_fmt = "yuv420p"

    def _default_output(self) -> str:
        base, ext = os.path.splitext(self.input_path)
        return f"{base}_edited{ext}"

    # ─── Aspect Ratio / Framing ──────────────────────────────────────────────

    def to_vertical(self, target_width: int = 1080, target_height: int = 1920,
                    position: str = "center") -> "VideoEditor":
        """
        Scale and pad to 9:16 vertical (TikTok, Reels, Shorts).
        position: center|top|bottom
        """
        # Get input dimensions
        dims = get_video_dimensions(self.input_path)
        if dims is None:
            raise RuntimeError("Cannot read input dimensions")
        w, h = dims

        # Calculate scale to fit width, then pad height (letterbox)
        scale_w = target_width
        scale_h = int(h * (target_width / w))
        if scale_h > target_height:
            scale_h = target_height
            scale_w = int(w * (target_height / h))

        filters = [
            f"scale={scale_w}:{scale_h}",
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
        ]
        self._filters.extend(filters)
        return self

    def to_horizontal(self, target_width: int = 1920, target_height: int = 1080,
                      position: str = "center") -> "VideoEditor":
        """
        Scale and pad to 16:9 horizontal (YouTube).
        """
        dims = get_video_dimensions(self.input_path)
        if dims is None:
            raise RuntimeError("Cannot read input dimensions")
        w, h = dims

        scale_h = target_height
        scale_w = int(w * (target_height / h))
        if scale_w > target_width:
            scale_w = target_width
            scale_h = int(h * (target_width / w))

        filters = [
            f"scale={scale_w}:{scale_h}",
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
        ]
        self._filters.extend(filters)
        return self

    def to_square(self, size: int = 1080) -> "VideoEditor":
        """Pad to 1:1 square (Instagram feed)."""
        dims = get_video_dimensions(self.input_path)
        if dims is None:
            raise RuntimeError("Cannot read input dimensions")
        w, h = dims

        scale = min(size, int(w * (size / h)), int(h * (size / w)))
        self._filters.extend([
            f"scale={scale}:{scale}",
            f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=black"
        ])
        return self

    def crop(self, width: int, height: int, x: int = 0, y: int = 0) -> "VideoEditor":
        """Crop video to specified region."""
        self._filters.append(f"crop={width}:{height}:{x}:{y}")
        return self

    def cinematic_letterbox(self, target_ratio: str = "2.39:1") -> "VideoEditor":
        """
        Add cinematic letterbox (letterbox bars top/bottom).
        Common ratios: '2.39:1' (Cinemascope), '1.85:1', '21:9'
        """
        # Parse ratio
        parts = target_ratio.split(":")
        ratio = float(parts[0]) / float(parts[1])

        dims = get_video_dimensions(self.input_path)
        if dims is None:
            return self
        w, h = dims

        # Calculate target height to achieve ratio
        new_h = int(w / ratio)
        pad_v = max(0, (new_h - h) // 2)
        pad_u = max(0, (h * ratio - w) // 2) if h > new_h else 0

        self._filters.append(
            f"pad={w}:{new_h}:0:{pad_v}:color=black"
        )
        return self

    # ─── Color / LUT ─────────────────────────────────────────────────────────

    def apply_lut(self, lut_path: Optional[str] = None,
                  lut_name: str = "none") -> "VideoEditor":
        """Apply a .cube LUT file for colour grading."""
        if lut_name != "none" and not lut_path:
            lut_path = os.path.join(LUT_DIR, f"{lut_name}.cube")

        if lut_path and os.path.exists(lut_path):
            self._filters.append(f"lut3d='{lut_path}'")
        return self

    def colorgrade(self, preset: str = "cinematic") -> "VideoEditor":
        """
        Apply programmatic colour grade (no LUT file needed).
        Presets: cinematic, warm_vintage, cool_modern, high_contrast, teal_orange
        """
        if preset == "cinematic":
            # Teal shadows, warm highlights, slight desaturation
            self._filters.extend([
                "curves=all='0/0 0.12/0.08 0.5/0.48 0.88/0.92 1/1'",
                "colorbalance=bs=0.1:rs=-0.05:gs=0.0:bl=0.1:rs=0.05:gs=0.0:bl=-0.05:rm=0.05:gm=0:bm=-0.05",
                "saturation=1.15",
            ])
        elif preset == "warm_vintage":
            self._filters.extend([
                "colorbalance=bs=0.15:rs=-0.1:gs=0.05:bl=0.0:rs=0.1:gs=0.05:bl=0.0",
                "curves=all='0/0 0.2/0.18 0.5/0.52 0.8/0.85 1/1'",
                "saturation=1.1",
            ])
        elif preset == "cool_modern":
            self._filters.extend([
                "colorbalance=bs=-0.1:rs=0.05:gs=0.0:bl=0.15:rs=-0.05:gs=0.0:bl=0.1",
                "curves=all='0/0 0.15/0.12 0.5/0.5 0.85/0.88 1/1'",
                "saturation=1.2",
            ])
        elif preset == "high_contrast":
            self._filters.extend([
                "curves=all='0/0.02 0.25/0.15 0.5/0.50 0.75/0.88 1/0.98'",
                "colorlevels=rimin=0.05:gimin=0.05:bimin=0.05",
                "saturation=1.3",
            ])
        elif preset == "teal_orange":
            # Classic Hollywood: lift shadows to teal, push highlights to orange
            self._filters.extend([
                "colorbalance=bs=0.12:rs=-0.05:gs=0:bl=0.08:rs=0.08:gs=0:bl=-0.05",
                "curves=master='0/0.03 0.5/0.48 1/0.97'",
                "saturation=1.25",
            ])
        return self

    def exposure(self, gamma: float = 1.0, brightness: float = 0.0,
                  contrast: float = 1.0) -> "VideoEditor":
        """Adjust exposure, brightness, contrast."""
        if gamma != 1.0:
            self._filters.append(f"geq=pow(X/{255},1/{gamma})*255")
        if brightness != 0.0:
            self._filters.append(f"eq=brightness={brightness}")
        if contrast != 1.0:
            self._filters.append(f"eq=contrast={contrast}")
        return self

    def denoise(self, strength: str = "medium") -> "VideoEditor":
        """Apply video denoising. strength: light|medium|strong"""
        strength_map = {"light": "3:5:3", "medium": "5:5:3", "strong": "7:7:5"}
        param = strength_map.get(strength, "5:5:3")
        self._filters.append(f"hqdn3d={param}")
        return self

    def sharpen(self, amount: float = 1.0) -> "VideoEditor":
        """Sharpen video (amount: 0.5 - 2.0)."""
        self._filters.append(f"unsharp=5:5:{amount}:5:5:{amount}")
        return self

    # ─── Text / Watermark ───────────────────────────────────────────────────

    def add_text(self, text: str,
                 font: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 font_size: int = 36,
                 color: str = "white",
                 x: int = "(w-text_w)/2",
                 y: str = "(h-text_h)-20",
                 box: bool = True,
                 box_color: str = "black@0.5") -> "VideoEditor":
        """Add text overlay."""
        box_str = f":box=1:boxcolor={box_color}" if box else ""
        self._filters.append(
            f"drawtext=text='{text}':fontfile='{font}':"
            f"fontsize={font_size}:fontcolor={color}:"
            f"x={x}:y={y}{box_str}"
        )
        return self

    def add_watermark(self, watermark_path: str,
                      position: str = "右下",
                      opacity: float = 0.7,
                      scale: float = 0.15) -> "VideoEditor":
        """
        Add image watermark. position: 左上|左下|右上|右下|中心
        """
        pos_map = {
            "左上":  "10:10",
            "左下":  "10:h-th-10",
            "右上":  "w-tw-10:10",
            "右下":  "W-tw-10:h-th-10",
            "中心":  "(w-tw)/2:(h-th)/2",
        }
        xy = pos_map.get(position, "W-tw-10:h-th-10")
        overlay = watermark_path.replace("'", "\\'")
        self._filters.append(
            f"overlay={xy}:format=auto:alpha={opacity}"
        )
        return self

    # ─── Audio ──────────────────────────────────────────────────────────────

    def normalize_audio(self, level: float = -20.0) -> "VideoEditor":
        """Normalize audio to target dBFS."""
        self._filters.append(f"loudnorm=I={level}")
        return self

    def adjust_audio(self, volume: float = 1.0,
                     fade_in: float = 0.0,
                     fade_out: float = 0.0) -> "VideoEditor":
        """Adjust audio volume and add fades."""
        if volume != 1.0:
            self._filters.append(f"volume={volume}")
        if fade_in > 0:
            self._filters.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            self._filters.append(f"afade=t=out:st=-{fade_out}:d={fade_out}")
        return self

    # ─── Transitions ─────────────────────────────────────────────────────────

    def trim(self, start: float = 0.0, end: Optional[float] = None) -> "VideoEditor":
        """Trim video to start:end seconds."""
        end_str = f":{end}" if end is not None else ""
        self._filters.append(f"trim=start={start}{end_str},setpts=PTS-STARTPTS")
        return self

    def fade_in(self, duration: float = 1.0) -> "VideoEditor":
        """Add fade-in."""
        self._filters.append(f"fade=t=in:st=0:d={duration}")
        return self

    def fade_out(self, duration: float = 1.0) -> "VideoEditor":
        """Add fade-out (applied at end of video)."""
        # We need to handle this differently since we don't know total duration yet
        self._filters.append(f"fade=t=out:st=-{duration}:d={duration}")
        return self

    # ─── Speed / Reverse ─────────────────────────────────────────────────────

    def speed(self, factor: float = 1.0) -> "VideoEditor":
        """Change playback speed (0.25 - 4.0)."""
        if factor <= 0 or factor > 4:
            raise ValueError("Speed factor must be between 0.25 and 4.0")
        self._filters.append(f"setpts={1/factor}*PTS")
        self._filters.append(f"atempo={min(max(factor, 0.5), 2.0)}")
        return self

    def reverse(self) -> "VideoEditor":
        """Reverse video playback."""
        self._filters.append("reverse")
        return self

    # ─── Stabilization ───────────────────────────────────────────────────────

    def stabilize(self) -> "VideoEditor":
        """Apply video stabilization (deshake)."""
        self._filters.append("deshake")
        return self

    # ─── Render ──────────────────────────────────────────────────────────────

    def render(self, output_path: Optional[str] = None,
               quality: str = "high") -> str:
        """
        Render final video with all accumulated filters.
        quality: draft|standard|high|ultra
        """
        if output_path:
            self.output_path = output_path

        quality_settings = {
            "draft":    {"crf": 28, "preset": "ultrafast"},
            "standard": {"crf": 23, "preset": "medium"},
            "high":     {"crf": 18, "preset": "slow"},
            "ultra":    {"crf": 15, "preset": "veryslow"},
        }
        qs = quality_settings.get(quality, quality_settings["high"])

        filter_chain = ";".join(self._filters) if self._filters else "null"
        cmd = [
            "ffmpeg", "-y", "-i", self.input_path,
            "-vf", filter_chain,
            "-c:v", self._video_codec,
            "-preset", qs["preset"],
            "-crf", str(qs["crf"]),
            "-pix_fmt", self._pix_fmt,
            "-c:a", self._audio_codec,
            "-b:a", "192k",
            self.output_path
        ]
        _run_ffmpeg(cmd)
        return self.output_path

    # ─── Chain builder (for complex pipelines) ────────────────────────────────

    def build_command(self, output_path: Optional[str] = None) -> List[str]:
        """Return the full ffmpeg command without running it."""
        if output_path:
            self.output_path = output_path
        filter_chain = ";".join(self._filters) if self._filters else "null"
        return [
            "ffmpeg", "-y", "-i", self.input_path,
            "-vf", filter_chain,
            "-c:v", self._video_codec,
            "-preset", self._preset,
            "-crf", str(self._crf),
            "-pix_fmt", self._pix_fmt,
            "-c:a", self._audio_codec,
            "-b:a", "192k",
            self.output_path
        ]


# ─── Utility functions ────────────────────────────────────────────────────────

def get_video_dimensions(path: str) -> Optional[tuple]:
    """Return (width, height) of video using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=s=x:p=0", path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        w, h = result.stdout.strip().split("x")
        return int(w), int(h)
    except Exception:
        return None


def get_video_duration(path: str) -> float:
    """Get duration in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def get_video_info(path: str) -> Dict[str, Any]:
    """Return full video info dict."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams", path
    ]
    import json
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception:
        return {}


def concat_videos(video_paths: List[str], output_path: str) -> str:
    """Concatenate multiple videos into one."""
    # Write concat list
    list_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for p in video_paths:
        list_file.write(f"file '{p}'\n")
    list_file.close()

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file.name,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    _run_ffmpeg(cmd)
    os.unlink(list_file.name)
    return output_path


def extract_thumbnail(video_path: str,
                       time_seconds: float = 1.0,
                       output_path: Optional[str] = None) -> str:
    """Extract a single thumbnail from video."""
    if output_path is None:
        base = os.path.splitext(video_path)[0]
        output_path = f"{base}_thumb.jpg"
    cmd = [
        "ffmpeg", "-y", "-ss", str(time_seconds),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_path
    ]
    _run_ffmpeg(cmd)
    return output_path


def extract_frames(video_path: str,
                   output_dir: str,
                   every_seconds: float = 1.0) -> List[str]:
    """Extract frames as images at regular intervals."""
    os.makedirs(output_dir, exist_ok=True)
    out_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps=1/{every_seconds}",
        "-q:v", "2",
        out_pattern
    ]
    _run_ffmpeg(cmd)
    import glob
    return sorted(glob.glob(os.path.join(output_dir, "frame_*.jpg")))


def add_subtitle_track(video_path: str,
                       srt_path: str,
                       output_path: str,
                       lang: str = "en") -> str:
    """Add a subtitle track (not burn-in) to the video."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-i", srt_path,
        "-c:v", "copy", "-c:a", "copy",
        "-c:s", "mov_text",
        "-map", "0:v", "-map", "0:a",
        "-map", "1",
        f"-metadata:s:s:{0}", f"language={lang}",
        output_path
    ]
    _run_ffmpeg(cmd)
    return output_path


def convert_audio(video_path: str,
                  output_path: str,
                  codec: str = "libmp3lame",
                  bitrate: str = "192k") -> str:
    """Extract audio from video and convert format."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-c:a", codec, "-b:a", bitrate,
        output_path
    ]
    _run_ffmpeg(cmd)
    return output_path
