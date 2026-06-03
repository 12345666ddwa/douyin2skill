"""Frame extractor — extract keyframes from video for OCR and vision analysis.

Implements the dual-pass strategy:
  Pass 1: Crop subtitle area, low fps → OCR reading
  Pass 2: Full frames at chapter points → Qwen2-VL vision analysis
"""

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_keyframes(
    video_path: Path,
    output_dir: Path = None,
    duration_s: float = None,
) -> Path:
    """Extract keyframes from a video file.

    Frame rate is auto-selected based on video duration:
      < 1 min:  fps=0.5 (~30 frames)
      1-3 min:  fps=0.2 (~36 frames)
      3-5 min:  fps=0.1 (~21-30 frames)
      > 5 min:  fps=0.05 (~15-20 frames)

    Args:
        video_path: Path to the video file
        output_dir: Output directory (default: temp dir)
        duration_s: Video duration in seconds (auto-detected if None)

    Returns:
        Path to the directory containing extracted frames
    """
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="douyin2skill_frames_"))

    output_dir.mkdir(parents=True, exist_ok=True)

    # Auto-detect duration
    if duration_s is None:
        duration_s = _get_duration(video_path)

    # Select fps based on duration
    fps = _select_fps(duration_s)
    logger.info(f"Video duration: {duration_s:.0f}s → fps={fps}")

    # Extract frames
    output_pattern = output_dir / "frame_%03d.jpg"
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-q:v", "1",  # Highest JPEG quality
        "-y",  # Overwrite
        str(output_pattern),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        logger.warning("Frame extraction timed out, using partial results")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg frame extraction failed: {e.stderr.decode()}")

    frame_count = len(list(output_dir.glob("frame_*.jpg")))
    logger.info(f"Extracted {frame_count} frames → {output_dir}")

    return output_dir


def extract_subtitle_frames(
    video_path: Path,
    output_dir: Path = None,
    fps: float = 0.1,
) -> Path:
    """Extract frames with bottom-half crop for subtitle reading (Pass 1).

    This is optimized for Douyin's subtitle placement (bottom 50% of frame).

    Args:
        video_path: Path to the video file
        output_dir: Output directory
        fps: Frame rate (lower is faster, 0.1-0.5 for subtitles)

    Returns:
        Path to the directory containing cropped frames
    """
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="douyin2skill_sub_"))

    output_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = output_dir / "sub_%03d.jpg"
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps},crop=iw:ih/2:0:ih/2",
        "-q:v", "1",
        "-y",
        str(output_pattern),
    ]

    subprocess.run(cmd, check=True, capture_output=True, timeout=60)

    frame_count = len(list(output_dir.glob("sub_*.jpg")))
    logger.info(f"Extracted {frame_count} subtitle frames → {output_dir}")

    return output_dir


def select_keyframes(
    frames_dir: Path,
    max_frames: int = 6,
) -> list[Path]:
    """Select a subset of frames evenly distributed across the video.

    For long videos (many frames), analyzing all frames is wasteful.
    This function picks max_frames frames spread evenly.

    Args:
        frames_dir: Directory containing frame_*.jpg files
        max_frames: Maximum number of frames to select

    Returns:
        Sorted list of selected frame paths
    """
    all_frames = sorted(frames_dir.glob("frame_*.jpg"))
    if len(all_frames) <= max_frames:
        return all_frames

    step = max(1, len(all_frames) // max_frames)
    selected = [all_frames[0]]  # Always include first frame
    for i in range(step, len(all_frames), step):
        selected.append(all_frames[i])

    logger.info(f"Selected {len(selected)}/{len(all_frames)} keyframes")
    return selected


def _get_duration(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return float(result.stdout.strip())


def _select_fps(duration_s: float) -> float:
    """Select optimal fps based on video duration."""
    if duration_s < 60:
        return 0.5
    elif duration_s < 180:
        return 0.3
    elif duration_s < 300:
        return 0.1
    else:
        return 0.05
