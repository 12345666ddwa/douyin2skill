"""Skill builder — convert analysis results into structured Hermes Skill files.

Outputs Markdown + YAML frontmatter format compatible with Hermes Agent.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SKILL_TEMPLATE = """---
name: {name}
description: {description}
category: {category}
tags: {tags}
source_video: {source_video}
learned_at: {learned_at}
---

# {title}

## 核心概念

{concepts}

## 操作步骤

{operations}

## 使用示例

{examples}

## 注意事项

{tips}

## 参考

- 来源视频: {source_video}
- 学习日期: {learned_at}
{dependencies}
"""


class SkillResult(dict):
    """A skill dict with a .save() convenience method."""

    def save(self, output_path: str) -> str:
        """Save this skill as a SKILL.md file."""
        builder = SkillBuilder()
        return builder.save_to_markdown(self, output_path)


class SkillBuilder:
    """Build structured Hermes Skill files from analysis results."""

    def __init__(self):
        self.skills = []

    def build(
        self,
        transcript: str = "",
        ocr_text: str = "",
        vision_text: str = "",
        repo_info: dict = None,
        title_hint: str = "",
    ) -> dict:
        """Build a structured skill from multi-channel analysis.

        Returns a dict with all skill components (can be serialized as SKILL.md).
        """
        from datetime import datetime

        # Merge all text sources
        merged_text = "\n".join(
            t for t in [transcript, ocr_text, vision_text] if t
        )

        # Extract structured content
        title = self._extract_title(merged_text, title_hint)
        concepts = self._extract_concepts(merged_text)
        operations = self._extract_operations(merged_text)
        examples = self._extract_examples(merged_text, repo_info)
        tips = self._extract_tips(merged_text)
        tags = self._extract_tags(merged_text)

        skill = {
            "name": self._slugify(title),
            "title": title,
            "description": self._generate_description(title, concepts),
            "category": self._guess_category(tags),
            "tags": tags,
            "concepts": concepts,
            "operations": operations,
            "examples": examples,
            "tips": tips,
            "github_repo": repo_info.get("repo") if repo_info else None,
            "source_video": title_hint or "Douyin video",
            "learned_at": datetime.now().strftime("%Y-%m-%d"),
            "dependencies": self._extract_dependencies(merged_text, repo_info),
        }

        self.skills.append(skill)
        return SkillResult(skill)

    def save_to_markdown(self, skill: dict, output_path: str) -> str:
        """Save a skill dict as a SKILL.md file."""
        content = SKILL_TEMPLATE.format(
            name=skill["name"],
            description=skill["description"],
            category=skill["category"],
            tags=str(skill["tags"]),
            source_video=skill["source_video"],
            learned_at=skill["learned_at"],
            title=skill["title"],
            concepts=skill["concepts"] or "（待提取）",
            operations=skill["operations"] or "（待提取）",
            examples=skill["examples"] or "（待提取）",
            tips=skill["tips"] or "（待提取）",
            dependencies=self._format_repo(skill.get("github_repo")),
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Skill saved → {path}")
        return str(path)

    def merge(self, skills: list[dict], output: str) -> str:
        """Merge multiple skills into a unified document."""
        # For now, simple concatenation
        # TODO: Cross-video deduplication and thematic grouping
        merged = "# 批量学习汇总\n\n"
        for skill in skills:
            merged += f"## {skill['title']}\n\n"
            merged += f"{skill['description']}\n\n"
            if skill.get("github_repo"):
                merged += f"- GitHub: {skill['github_repo']}\n"
            merged += "\n---\n\n"

        Path(output).write_text(merged, encoding="utf-8")
        return merged

    def _extract_title(self, text: str, hint: str) -> str:
        if hint:
            return hint
        # Take first meaningful line
        lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
        return lines[0][:60] if lines else "未命名技能"

    def _extract_concepts(self, text: str) -> str:
        """Extract conceptual knowledge (definitions, principles)."""
        # Simple heuristic: lines with explanatory patterns
        patterns = ["是什么", "定义", "概念", "指的是", "就是"]
        lines = []
        for line in text.split("\n"):
            if any(p in line for p in patterns) and len(line) > 10:
                lines.append(f"- {line.strip()}")
        return "\n".join(lines[:10]) if lines else ""

    def _extract_operations(self, text: str) -> str:
        """Extract actionable steps (commands, installations)."""
        lines = []
        steps = []
        for line in text.split("\n"):
            stripped = line.strip()
            if any(kw in stripped for kw in ["pip install", "git clone", "运行", "安装", "配置"]):
                if stripped.startswith("```"):
                    continue
                steps.append(f"1. {stripped}")
            elif stripped.startswith("```"):
                lines.append(stripped)
        return "\n".join(steps[:10])

    def _extract_examples(self, text: str, repo_info: dict = None) -> str:
        examples = ""
        if repo_info and repo_info.get("repo"):
            examples += f"- GitHub 项目: [{repo_info['repo']}]({repo_info.get('url', '')})\n"
            if repo_info.get("stars"):
                examples += f"- ⭐ Stars: {repo_info['stars']}\n"
        return examples or ""

    def _extract_tips(self, text: str) -> str:
        """Extract tips, warnings, and pitfalls."""
        tips = []
        for line in text.split("\n"):
            if any(kw in line for kw in ["注意", "⚠", "小心", "不要", "避免"]):
                tips.append(f"- ⚠️ {line.strip()}")
        return "\n".join(tips[:10]) if tips else ""

    def _extract_tags(self, text: str) -> list[str]:
        """Extract relevant tags."""
        import re
        tags = re.findall(r"#(\w+)", text)
        return list(set(tags))[:10]

    def _guess_category(self, tags: list[str]) -> str:
        """Guess skill category from tags."""
        tag_lower = [t.lower() for t in tags]
        mappings = {
            "automation": ["自动化", "automation", "bot"],
            "devops": ["docker", "deploy", "ci", "server"],
            "data-science": ["数据", "data", "ml", "ai", "python"],
            "workflow": ["workflow", "pipeline", "pipeline"],
        }
        for category, keywords in mappings.items():
            if any(kw in tag_lower for kw in keywords):
                return category
        return "learning-productivity"

    def _extract_dependencies(self, text: str, repo_info: dict = None) -> str:
        deps = []
        if "pip install" in text:
            deps.append(text)
        if repo_info and repo_info.get("repo"):
            deps.append(f"- 来源项目: [{repo_info['repo']}]({repo_info.get('url', '')})")
        return "\n".join(deps)

    def _generate_description(self, title: str, concepts: str) -> str:
        first_line = concepts.split("\n")[0] if concepts else title
        return f"从抖音视频中自动学习: {first_line[:100]}"

    def _slugify(self, title: str) -> str:
        import re
        slug = re.sub(r"[^\w\s-]", "", title)
        slug = re.sub(r"\s+", "-", slug.strip())
        return slug.lower()[:64]

    def _format_repo(self, repo: str = None) -> str:
        if not repo:
            return ""
        return f"- GitHub: [{repo}](https://github.com/{repo})\n"
