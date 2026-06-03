"""Video downloader — download Douyin videos with proper headers.

Handles the time-sensitive nature of Douyin video URLs (temp=1 parameter).
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Standard browser-emulating headers for Douyin CDN
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.douyin.com/",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
}


def download_video(
    url: str,
    output_dir: Optional[Path] = None,
    proxy: Optional[str] = None,
    timeout: int = 60,
) -> Path:
    """Download a Douyin video to a temporary file.

    IMPORTANT: Douyin URLs contain `temp=1` and expire quickly.
    Call this function immediately after extracting the URL.

    Args:
        url: Raw video source URL (from extract_video_sources)
        output_dir: Directory to save the file (default: system temp)
        proxy: HTTP proxy URL (e.g. http://127.0.0.1:7897)
        timeout: Download timeout in seconds

    Returns:
        Path to the downloaded video file

    Raises:
        requests.RequestException: If download fails
    """
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir())

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"douyin2skill_{_random_suffix()}.mp4"

    headers = DEFAULT_HEADERS.copy()
    proxies = {"http": proxy, "https": proxy} if proxy else None

    logger.info(f"Downloading video → {output_path}")

    try:
        resp = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            timeout=timeout,
            stream=True,
        )
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)

        size_mb = downloaded / (1024 * 1024)
        logger.info(f"Downloaded {size_mb:.1f} MB → {output_path}")
        return output_path

    except requests.RequestException as e:
        # Clean up partial download
        output_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download video from {url[:80]}...: {e}")


def _random_suffix(length: int = 8) -> str:
    import random
    import string
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
