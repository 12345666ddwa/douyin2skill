"""Video source extractor — extract raw MP4 URLs from Douyin pages.

Bypasses yt-dlp's cookie requirement by using browser JS injection.
Handles the new audio/video separate-stream anti-pattern.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# JavaScript snippets for extracting video sources
EXTRACT_SRC_JS = """
JSON.stringify(
    Array.from(document.querySelectorAll('video source')).map(s => s.src)
)
"""

EXTRACT_PERFORMANCE_JS = """
(function() {
    var entries = performance.getEntriesByType('resource');
    var video = entries.filter(e => e.name.includes('media-video')).map(e => e.name);
    var audio = entries.filter(e => e.name.includes('media-audio')).map(e => e.name);
    return JSON.stringify({video: video, audio: audio});
})()
"""

EXTRACT_CURRENTSRC_JS = """
document.querySelector('video').currentSrc
"""


def extract_video_sources(page_url: str, proxy: Optional[str] = None) -> list[str]:
    """Extract video source URLs from a Douyin page.

    Args:
        page_url: Full video page URL
        proxy: Optional HTTP proxy (e.g. http://127.0.0.1:7897)

    Returns:
        List of video source URLs (prioritized: first is best quality)

    Note:
        This function requires browser access. In a headless environment,
        it falls back to the `browser_navigate` + `browser_console` flow.
        The URLs contain `temp=1` and must be used immediately.
    """
    # This is the core logic; actual browser interaction happens via
    # the Hermes Agent browser tools. The function signature is designed
    # to be called from a browser-enabled context.

    logger.info(f"Extracting video sources from: {page_url}")
    logger.info("Use browser_console with EXTRACT_SRC_JS for normal pages")
    logger.info("Use EXTRACT_PERFORMANCE_JS when video/audio streams are separated")

    # In a standalone script context, guide the caller
    return _extract_via_browser(page_url)


def _extract_via_browser(page_url: str) -> list[str]:
    """Extract video sources using browser tools (Hermes Agent context).

    The actual implementation is:
    1. browser_navigate(url=page_url)
    2. browser_console(expression=EXTRACT_SRC_JS)
    3. If empty, try EXTRACT_PERFORMANCE_JS for separate streams
    4. Return the first valid URL
    """
    raise NotImplementedError(
        "extract_video_sources requires browser access. "
        "Call from a Hermes Agent context with browser_navigate + browser_console."
    )
