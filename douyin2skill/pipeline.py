"""
douyin2skill — Turn Douyin tutorial videos into reusable AI Agent skills.

Core pipeline orchestrator. Single entry point for all operations.
"""

import logging
from pathlib import Path
from typing import Optional

from .extractors.link_resolver import resolve_short_link
from .extractors.video_source import extract_video_sources
from .extractors.downloader import download_video
from .extractors.frame_extractor import extract_keyframes
from .analyzers.whisper_stt import transcribe_audio
from .analyzers.ocr_reader import read_subtitles
from .skill_builder import SkillBuilder

logger = logging.getLogger(__name__)


class Pipeline:
    """Main pipeline: link → video → analysis → skill."""

    def __init__(
        self,
        use_vision: bool = False,
        use_ocr: bool = True,
        model_size: str = "base",
        proxy: Optional[str] = None,
    ):
        self.use_vision = use_vision
        self.use_ocr = use_ocr
        self.model_size = model_size
        self.proxy = proxy
        self.builder = SkillBuilder()

    def learn(self, url: str) -> dict:
        """Process a single Douyin link and return a structured skill.

        Args:
            url: Douyin short link (e.g., https://v.douyin.com/xxxx/)

        Returns:
            dict with keys: title, summary, concepts, operations, cases, tips, github_repo
        """
        # Phase 1: Resolve short link
        logger.info(f"Resolving: {url}")
        real_url = resolve_short_link(url)
        logger.info(f"Resolved: {real_url}")

        # Phase 2: Extract video sources
        sources = extract_video_sources(real_url, proxy=self.proxy)
        logger.info(f"Found {len(sources)} video sources")

        # Phase 3: Download video
        video_path = download_video(sources[0], proxy=self.proxy)
        logger.info(f"Downloaded: {video_path}")

        # Phase 4: Extract keyframes
        frames_dir = extract_keyframes(video_path)
        logger.info(f"Frames extracted to {frames_dir}")

        # Phase 5: Multi-channel analysis
        # Channel A: Whisper audio transcription
        transcript = transcribe_audio(video_path, model_size=self.model_size)

        # Channel B: OCR subtitle reading
        ocr_text = ""
        if self.use_ocr:
            ocr_text = read_subtitles(frames_dir)

        # Channel C: Qwen2-VL visual analysis (if GPU available)
        vision_text = ""
        if self.use_vision:
            try:
                from .analyzers.qwen2vl_vision import analyze_frames
                vision_text = analyze_frames(frames_dir)
            except ImportError:
                logger.warning("Qwen2-VL not available, skipping vision analysis")
            except Exception as e:
                logger.warning(f"Vision analysis failed: {e}")

        # Phase 6: Triangulate (cross-validate with GitHub API)
        repo_info = {}
        try:
            from .analyzers.triangulator import triangulate
            repo_info = triangulate(transcript, ocr_text, title_hint="")
        except Exception as e:
            logger.warning(f"Triangulation failed: {e}")

        # Phase 7: Build structured skill
        skill = self.builder.build(
            transcript=transcript,
            ocr_text=ocr_text,
            vision_text=vision_text,
            repo_info=repo_info,
            title_hint="",
        )

        # Cleanup
        self._cleanup(video_path, frames_dir)

        return skill

    def _cleanup(self, video_path: Path, frames_dir: Path):
        """Remove temporary files."""
        import shutil
        try:
            video_path.unlink(missing_ok=True)
            shutil.rmtree(frames_dir, ignore_errors=True)
        except Exception:
            pass


class BatchLearner:
    """Process multiple videos with parallelism."""

    def __init__(self, max_parallel: int = 3, **pipeline_kwargs):
        self.max_parallel = max_parallel
        self.pipeline_kwargs = pipeline_kwargs

    def learn_all(self, urls: list[str]) -> list[dict]:
        """Process all URLs and return list of skills."""
        results = []
        for url in urls:
            pipe = Pipeline(**self.pipeline_kwargs)
            try:
                skill = pipe.learn(url)
                results.append(skill)
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                results.append({"error": str(e), "url": url})
        return results

    def merge_skills(self, skills: list[dict], output: str = "merged.md") -> str:
        """Merge multiple skills into a unified document."""
        builder = SkillBuilder()
        return builder.merge(skills, output)
