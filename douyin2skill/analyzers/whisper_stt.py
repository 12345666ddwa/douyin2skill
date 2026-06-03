"""Whisper speech-to-text — transcribe Chinese audio from Douyin videos.

Uses OpenAI Whisper locally. Base model (139M) is sufficient for most cases.
Small model (244M) recommended when technical terms are important.
"""

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Model size → approximate load time + accuracy
MODEL_SIZES = {
    "tiny": (39, "⭐ Fast but less accurate for Chinese"),
    "base": (139, "⭐⭐ Good balance for daily use"),
    "small": (244, "⭐⭐⭐ Better for technical terms"),
    "medium": (769, "⭐⭐⭐⭐ Heavy accents / background noise"),
}


def transcribe_audio(
    video_path: Path,
    model_size: str = "base",
    language: str = "zh",
) -> str:
    """Extract audio and transcribe using Whisper.

    Args:
        video_path: Path to the video file
        model_size: Whisper model size (tiny/base/small/medium)
        language: Language code (default: zh for Chinese)

    Returns:
        Transcribed Chinese text

    Raises:
        FileNotFoundError: If ffmpeg or whisper is not installed
    """
    # Step 1: Extract audio as 16kHz mono WAV
    audio_path = _extract_audio(video_path)

    # Step 2: Transcribe with Whisper
    logger.info(f"Transcribing with Whisper ({model_size})...")

    result = subprocess.run(
        [
            "python3", "-c",
            f"""
import whisper
model = whisper.load_model('{model_size}')
result = model.transcribe('{audio_path}', language='{language}')

# Output full text
print(result['text'])

# Output segments with timestamps for structured extraction
print('===SEGMENTS===')
for seg in result['segments']:
    m, s = divmod(int(seg['start']), 60)
    print(f'[{m:02d}:{s:02d}] {{seg[\"text\"].strip()}}')
""",
        ],
        capture_output=True,
        text=True,
        timeout=300,  # Whisper can take a while on CPU
    )

    if result.returncode != 0:
        raise RuntimeError(f"Whisper transcription failed: {result.stderr}")

    # Clean up audio
    audio_path.unlink(missing_ok=True)

    output = result.stdout.strip()
    logger.info(f"Transcription complete: {len(output)} chars")

    return output


def _extract_audio(video_path: Path) -> Path:
    """Extract audio track as 16kHz mono WAV for Whisper."""
    audio_path = video_path.with_suffix(".wav")

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le",
        "-ar", "16000",  # 16kHz (Whisper optimal)
        "-ac", "1",  # Mono
        "-y",
        str(audio_path),
    ]

    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    return audio_path


def extract_segments(transcript: str) -> list[dict]:
    """Parse Whisper output into timestamped segments.

    Returns:
        List of {start: str, text: str} dicts
    """
    segments = []
    for line in transcript.split("\n"):
        if line.startswith("[") and "]" in line:
            try:
                time_str = line[1:6]  # [MM:SS]
                text = line[7:].strip()
                if text:
                    segments.append({"start": time_str, "text": text})
            except (IndexError, ValueError):
                continue
    return segments
