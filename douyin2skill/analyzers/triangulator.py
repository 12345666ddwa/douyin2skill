"""Multi-source triangulator — cross-validate video analysis with GitHub API.

Integrates noisy signals from three sources:
  1. Whisper ASR (phonetic clues, even when words are wrong)
  2. OCR output (visual text clues, even with garbled characters)
  3. Page metadata (title, tags, description)

...and validates against GitHub's search API to precisely identify projects.
"""

import json
import logging
import re
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_SEARCH = f"{GITHUB_API}/search/repositories"


def triangulate(
    whisper_text: str,
    ocr_text: str,
    title_hint: str = "",
    proxy: Optional[str] = None,
) -> dict:
    """Cross-validate video analysis signals against GitHub.

    Args:
        whisper_text: Full Whisper transcription (may contain errors)
        ocr_text: OCR-extracted text from frames (may be garbled)
        title_hint: Page title or description (usually most reliable)
        proxy: Optional HTTP proxy

    Returns:
        {
            "repo": "owner/name",
            "stars": 12345,
            "description": "...",
            "confidence": "high/medium/low",
            "sources_matched": ["whisper", "ocr", "metadata"]
        }
    """
    # Step 1: Extract candidate keywords from each source
    whisper_keywords = _extract_keywords_from_whisper(whisper_text)
    ocr_keywords = _extract_keywords_from_ocr(ocr_text)
    meta_keywords = _extract_keywords_from_metadata(title_hint)

    logger.info(f"Whisper keywords: {whisper_keywords}")
    logger.info(f"OCR keywords: {ocr_keywords}")
    logger.info(f"Metadata keywords: {meta_keywords}")

    # Step 2: Generate search queries (combine sources)
    queries = _generate_queries(whisper_keywords, ocr_keywords, meta_keywords)

    # Step 3: Search GitHub API
    candidates = _search_github(queries, proxy=proxy)

    if not candidates:
        return {
            "repo": None,
            "stars": 0,
            "description": "",
            "confidence": "none",
            "sources_matched": [],
        }

    # Step 4: Score and pick best match
    best = candidates[0]
    sources = _which_sources_matched(best, whisper_keywords, ocr_keywords, meta_keywords)

    confidence = "high" if len(sources) >= 2 else "medium" if len(sources) >= 1 else "low"

    return {
        "repo": best["full_name"],
        "stars": best["stargazers_count"],
        "description": best.get("description", ""),
        "url": best["html_url"],
        "confidence": confidence,
        "sources_matched": sources,
    }


def _extract_keywords_from_whisper(text: str) -> list[str]:
    """Extract keywords from Whisper transcription.

    Handles common Chinese Whisper errors:
      - "get-up" → "GitHub"
      - "灯顶" → "登顶"
      - "热绑" → "热榜"
      - "保障项目" → "宝藏项目"
    """
    if not text:
        return []

    # Fix common phonetic errors
    fixed = text
    error_map = {
        "get-up": "GitHub",
        "get up": "GitHub",
        "灯顶": "登顶",
        "热绑": "热榜",
        "保障项目": "宝藏项目",
        "面临": "命令",
        "H2": "HR",
    }
    for wrong, correct in error_map.items():
        fixed = fixed.replace(wrong, correct)

    # Extract English words (often correct even when Chinese is garbled)
    english_words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", fixed)
    english_words = list(set(english_words))

    # Extract meaningful Chinese phrases (2-6 chars)
    chinese_phrases = re.findall(r"[\u4e00-\u9fff]{2,6}", fixed)
    # Remove common noise words
    noise = {"一个", "可以", "这个", "我们", "他们", "就是", "而且", "所以", "但是"}
    chinese_phrases = [p for p in chinese_phrases if p not in noise]
    chinese_phrases = list(set(chinese_phrases))

    return english_words + chinese_phrases[:10]  # Cap to avoid noise


def _extract_keywords_from_ocr(text: str) -> list[str]:
    """Extract keywords from OCR output.

    Useful even when garbled — partial matches are enough for triangulation.
    """
    if not text:
        return []

    # Extract GitHub-style patterns
    patterns = [
        r"([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)",  # owner/repo
        r"⭐\s*([\d,]+)",  # star count
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)",  # CamelCase phrases
    ]

    keywords = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)

    return list(set(keywords))[:10]


def _extract_keywords_from_metadata(title: str) -> list[str]:
    """Extract keywords from page title/tags/description.

    Most reliable source — doublespeak titles are designed to be search-friendly.
    Tags like #GitHub #AI工具 #token are gold.
    """
    if not title:
        return []

    # Extract hashtags
    hashtags = re.findall(r"#(\w+)", title)
    # Extract meaningful words
    words = re.findall(r"[\u4e00-\u9fff]{2,6}", title)

    return hashtags + words


def _generate_queries(
    whisper_kw: list[str],
    ocr_kw: list[str],
    meta_kw: list[str],
) -> list[str]:
    """Generate prioritized search queries combining sources.

    Query priority:
      1. meta + whisper (highest precision)
      2. meta + ocr
      3. meta only (fallback)
      4. whisper only (lowest, but sometimes works)
    """
    queries = []

    if meta_kw:
        meta_str = " ".join(meta_kw[:5])

        if whisper_kw:
            queries.append(f"{meta_str} {' '.join(whisper_kw[:3])}")
        if ocr_kw:
            queries.append(f"{meta_str} {' '.join(ocr_kw[:3])}")

        queries.append(meta_str)

    if whisper_kw and not queries:
        queries.append(" ".join(whisper_kw[:5]))

    return queries[:5]


def _search_github(
    queries: list[str],
    proxy: Optional[str] = None,
    per_page: int = 5,
) -> list[dict]:
    """Search GitHub API with multiple queries, return ranked candidates."""
    import urllib.parse

    all_candidates = []

    for query in queries:
        encoded = urllib.parse.quote(query)
        url = f"{GITHUB_SEARCH}?q={encoded}&sort=stars&per_page={per_page}"

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "douyin2skill",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            opener = urllib.request.build_opener()
            if proxy:
                opener.add_handler(
                    urllib.request.ProxyHandler({"http": proxy, "https": proxy})
                )

            resp = opener.open(req, timeout=15)
            data = json.loads(resp.read())

            for item in data.get("items", []):
                all_candidates.append({
                    "full_name": item["full_name"],
                    "stargazers_count": item["stargazers_count"],
                    "description": item.get("description", ""),
                    "html_url": item["html_url"],
                    "query": query,
                })

        except Exception as e:
            logger.debug(f"GitHub search failed for '{query}': {e}")
            continue

    # Deduplicate by full_name, keep highest stars
    seen = {}
    for c in all_candidates:
        name = c["full_name"]
        if name not in seen or c["stargazers_count"] > seen[name]["stargazers_count"]:
            seen[name] = c

    # Sort by stars descending
    return sorted(seen.values(), key=lambda x: x["stargazers_count"], reverse=True)


def _which_sources_matched(
    candidate: dict,
    whisper_kw: list[str],
    ocr_kw: list[str],
    meta_kw: list[str],
) -> list[str]:
    """Determine which analysis sources contributed to this match."""
    matched = []
    text = f"{candidate['full_name']} {candidate.get('description', '')}".lower()

    if meta_kw and any(kw.lower() in text for kw in meta_kw):
        matched.append("metadata")
    if ocr_kw and any(kw.lower() in text for kw in ocr_kw):
        matched.append("ocr")
    if whisper_kw and any(kw.lower() in text for kw in whisper_kw):
        matched.append("whisper")

    return matched
