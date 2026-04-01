"""
Auto Caption Generator using faster-whisper
Transcribes audio from video and burns subtitles into video using FFmpeg
"""
import os, subprocess, json, tempfile
from typing import Optional, List, Dict, Any

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


# ─── Whisper Model Sizes ─────────────────────────────────────────────────────
WHISPER_MODELS = {
    "tiny":    "tiny",
    "base":    "base",
    "small":  "small",
    "medium": "medium",
    "large":  "large-v3",
}


class CaptionGenerator:
    """Generate subtitles from video audio using faster-whisper."""

    def __init__(self, model_size: str = "base",
                 device: str = "auto",
                 compute_type: str = "auto"):
        """
        model_size: tiny|base|small|medium|large-v3
        device: auto|cpu|cuda
        compute_type: auto|int8|float16|float32
        """
        if not WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper not installed. Run: pip install faster-whisper")

        if device == "auto":
            device = "cuda" if _has_cuda() else "cpu"

        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"

        self.model_size = model_size
        self.model = WhisperModel(
            WHISPER_MODELS.get(model_size, model_size),
            device=device,
            compute_type=compute_type,
        )

    def transcribe(self, audio_path: str,
                   language: str = "en",
                   beam_size: int = 5,
                   vad_filter: bool = True) -> List[Dict[str, Any]]:
        """
        Transcribe audio file and return list of word-level timestamps.
        Returns list of dicts with: start, end, word, text
        """
        segments, _ = self.model.transcribe(
            audio_path,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            word_timestamps=True,
        )
        result = []
        for seg in segments:
            for word in seg.words:
                result.append({
                    "start":  word.start,
                    "end":    word.end,
                    "word":   word.word.strip(),
                    "text":   seg.text.strip(),
                })
        return result

    def transcribe_video(self, video_path: str,
                         language: str = "en",
                         beam_size: int = 5) -> List[Dict[str, Any]]:
        """
        Extract audio from video and transcribe.
        Uses FFmpeg to extract PCM WAV, then transcribes.
        """
        wav_path = extract_audio(video_path)
        try:
            return self.transcribe(wav_path, language=language, beam_size=beam_size)
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)

    def generate_srt(self, segments: List[Dict], output_path: str) -> str:
        """Write segments to SRT subtitle file."""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start_ts = _seconds_to_srt_timestamp(seg["start"])
                end_ts   = _seconds_to_srt_timestamp(seg["end"])
                # group words into one line per segment
                text = seg.get("text", "")
                f.write(f"{i}\n{start_ts} --> {end_ts}\n{text}\n\n")
        return output_path

    def generate_vtt(self, segments: List[Dict], output_path: str) -> str:
        """Write segments to WebVTT subtitle file."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for seg in segments:
                start_ts = _seconds_to_vtt_timestamp(seg["start"])
                end_ts   = _seconds_to_vtt_timestamp(seg["end"])
                text = seg.get("text", "")
                f.write(f"{start_ts} --> {end_ts}\n{text}\n\n")
        return output_path

    def get_full_text(self, segments: List[Dict]) -> str:
        """Extract plain text from segments."""
        return " ".join(seg.get("text", "") for seg in segments)


# ─── FFmpeg helpers ──────────────────────────────────────────────────────────

def extract_audio(video_path: str,
                  codec: str = "pcm_s16le",
                  sample_rate: int = 16000) -> str:
    """Extract audio track from video as WAV for Whisper."""
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", codec,
        "-ar", str(sample_rate), "-ac", "1",
        out
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return out


def burn_subtitles_srt(video_path: str,
                       srt_path: str,
                       output_path: str,
                       font: str = "Arial",
                       font_size: int = 28,
                       font_color: str = "white",
                       bold: bool = True,
                       position: str = "bottom") -> str:
    """
    Burn SRT subtitles directly into video using FFmpeg with libass.
    position: bottom | top | center
    """
    # Build subtitle position override
    margin_v = 20 if position == "bottom" else (20 if position == "top" else 0)
    alignment = 2 if position == "bottom" else (8 if position == "top" else 5)

    filter_str = (
        f"subtitles='{srt_path}':force_style='"
        f"FontName={font},FontSize={font_size},PrimaryColour=&H00{_hex_color(font_color)},"
        f"Bold={1 if bold else 0},Alignment={alignment},MarginV={margin_v}'"
    )

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", filter_str,
        "-c:a", "copy",
        "-c:v", "libx264", "-preset", "fast",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def burn_subtitles_vtt(video_path: str,
                       vtt_path: str,
                       output_path: str,
                       font: str = "Arial",
                       font_size: int = 28,
                       bold: bool = True,
                       position: str = "bottom") -> str:
    """Burn WebVTT subtitles into video."""
    margin_v = 20 if position == "bottom" else (20 if position == "top" else 0)
    alignment = 2 if position == "bottom" else (8 if position == "top" else 5)

    filter_str = (
        f"subtitles='{vtt_path}':force_style='"
        f"FontName={font},FontSize={font_size},Bold={1 if bold else 0},"
        f"Alignment={alignment},MarginV={margin_v}'"
    )
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", filter_str,
        "-c:a", "copy", "-c:v", "libx264", "-preset", "fast",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


# ─── Utility ─────────────────────────────────────────────────────────────────

def _has_cuda() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def _seconds_to_srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _seconds_to_vtt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _hex_color(name: str) -> str:
    """Convert CSS color name to BGR hex for libass."""
    colors = {
        "white": "FFFFFF", "yellow": "FFFF00", "red": "FF0000",
        "green": "00FF00", "blue": "0000FF", "cyan": "00FFFF",
        "magenta": "FF00FF",
    }
    return colors.get(name.lower(), "FFFFFF")


# ─── One-shot helpers ─────────────────────────────────────────────────────────

def transcribe_and_burn(video_path: str,
                         output_path: str,
                         model_size: str = "base",
                         language: str = "en",
                         subtitle_format: str = "srt",
                         position: str = "bottom") -> str:
    """
    Full pipeline: transcribe video → generate subtitle file → burn into video.
    Returns path to the final burned video.
    """
    cap = CaptionGenerator(model_size=model_size)
    segments = cap.transcribe_video(video_path, language=language)

    tmp_dir = os.path.dirname(output_path) or "."
    base = os.path.splitext(os.path.basename(video_path))[0]

    if subtitle_format == "vtt":
        sub_path = os.path.join(tmp_dir, f"{base}_subs.vtt")
        cap.generate_vtt(segments, sub_path)
        return burn_subtitles_vtt(video_path, sub_path, output_path, position=position)
    else:
        sub_path = os.path.join(tmp_dir, f"{base}_subs.srt")
        cap.generate_srt(segments, sub_path)
        return burn_subtitles_srt(video_path, sub_path, output_path, position=position)
