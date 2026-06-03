"""Link resolver — convert Douyin short links to full video URLs."""

import re
import logging
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

DOUYIN_SHORT_RE = re.compile(r"https?://v\.douyin\.com/\w+/?")


def resolve_short_link(url: str, timeout: int = 15) -> str:
    """Resolve a Douyin short link to the full video page URL.

    Uses HTTP redirect tracking (no browser needed, zero cost).

    Args:
        url: Short link like https://v.douyin.com/xxxxx/
        timeout: HTTP timeout in seconds

    Returns:
        Full URL like https://www.douyin.com/video/123456789

    Raises:
        ValueError: If the URL doesn't look like a Douyin short link
        ConnectionError: If the redirect fails
    """
    if not DOUYIN_SHORT_RE.match(url):
        raise ValueError(f"Not a Douyin short link: {url}")

    # Use urllib to follow redirects without downloading the body
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", "Mozilla/5.0")

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        final_url = resp.geturl()
        logger.debug(f"Resolved: {url} → {final_url}")

        # Extract just the video ID part
        video_id_match = re.search(r"/video/(\d+)", final_url)
        if video_id_match:
            video_id = video_id_match.group(1)
            return f"https://www.douyin.com/video/{video_id}"

        return final_url

    except Exception as e:
        raise ConnectionError(f"Failed to resolve short link {url}: {e}")
