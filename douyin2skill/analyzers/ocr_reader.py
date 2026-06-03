"""OCR subtitle reader — extract Chinese subtitles from video frames.

Supports PaddleOCR (recommended for Chinese) and EasyOCR (fallback).
Handles subtitle deduplication across adjacent frames.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_subtitles(
    frames_dir: Path,
    engine: str = "paddleocr",
) -> str:
    """Read Chinese subtitles from cropped frame images.

    Args:
        frames_dir: Directory containing subtitle-cropped frame images
        engine: OCR engine ('paddleocr' or 'easyocr')

    Returns:
        Merged and deduplicated subtitle text
    """
    frames = sorted(frames_dir.glob("*.jpg"))
    if not frames:
        logger.warning(f"No frames found in {frames_dir}")
        return ""

    logger.info(f"Reading subtitles from {len(frames)} frames")

    all_texts = _read_frames(frames, engine)
    merged = _deduplicate(all_texts)

    logger.info(f"Subtitle reading complete: {len(merged)} chars")
    return merged


def _read_frames(frames: list[Path], engine: str) -> list[str]:
    """Read text from each frame using the specified OCR engine."""
    import subprocess

    texts = []
    for i, frame in enumerate(frames):
        try:
            if engine == "paddleocr":
                text = _paddleocr_read(frame)
            elif engine == "easyocr":
                text = _easyocr_read(frame)
            else:
                raise ValueError(f"Unknown OCR engine: {engine}")

            if text and len(text.strip()) > 3:
                texts.append(text.strip())

        except Exception as e:
            logger.debug(f"Frame {i} OCR failed: {e}")
            continue

    return texts


def _paddleocr_read(image_path: Path, timeout: int = 60) -> str:
    """Read text from a single image using PaddleOCR."""
    import subprocess

    result = subprocess.run(
        [
            "python3", "-c",
            f"""
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch', show_log=False)
result = ocr.ocr('{image_path}')
if result and result[0]:
    texts = [line[1][0] for line in result[0]]
    print(' '.join(texts))
""",
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        logger.debug(f"PaddleOCR failed: {result.stderr[:100]}")
        return ""

    return result.stdout.strip()


def _easyocr_read(image_path: Path, timeout: int = 30) -> str:
    """Read text from a single image using EasyOCR (fallback)."""
    import subprocess

    result = subprocess.run(
        [
            "python3", "-c",
            f"""
import easyocr
reader = easyocr.Reader(['ch_sim', 'en'])
result = reader.readtext('{image_path}')
texts = [item[1] for item in result]
print(' '.join(texts))
""",
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip()


def _deduplicate(texts: list[str], similarity_threshold: float = 0.8) -> str:
    """Merge adjacent frames, removing near-duplicate subtitles.

    Subtitles typically stay on screen for multiple frames.
    Adjacent frames with >80% text similarity are merged.
    """
    if not texts:
        return ""

    merged = [texts[0]]

    for text in texts[1:]:
        prev = merged[-1]
        similarity = _text_similarity(prev, text)
        if similarity < similarity_threshold:
            merged.append(text)

    return "\n".join(merged)


def _text_similarity(a: str, b: str) -> float:
    """Simple Jaccard-like similarity between two texts."""
    if not a or not b:
        return 0.0
    set_a = set(a)
    set_b = set(b)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0
