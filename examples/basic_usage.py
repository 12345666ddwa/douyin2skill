#!/usr/bin/env python3
"""Basic usage example: process a single Douyin video."""

from douyin2skill import Pipeline


def main():
    # Replace with a real Douyin short link
    url = "https://v.douyin.com/xxxxx/"

    pipe = Pipeline(
        use_vision=False,   # Set True if you have GPU
        use_ocr=True,
        model_size="base",
    )

    print(f"🔍 Learning from: {url}")
    skill = pipe.learn(url)

    print(f"\n📹 Title: {skill['title']}")
    print(f"📝 Summary: {skill['description']}")

    if skill.get("github_repo"):
        print(f"🔗 GitHub: {skill['github_repo']} (⭐{skill.get('stars', '?')})")

    # Save as Hermes Skill
    path = skill.save("learned_skill.md")
    print(f"\n✅ Skill saved: {path}")


if __name__ == "__main__":
    main()
