"""
Batch learning example: process multiple Douyin videos.

Usage:
    python examples/batch_learning.py
"""

from douyin2skill import BatchLearner


def main():
    urls = [
        "https://v.douyin.com/video1/",
        "https://v.douyin.com/video2/",
        "https://v.douyin.com/video3/",
    ]

    print(f"🎬 Processing {len(urls)} videos...")

    learner = BatchLearner(max_parallel=3, use_vision=False)
    skills = learner.learn_all(urls)

    print(f"\n✅ Learned {len(skills)} skills:")
    for i, skill in enumerate(skills, 1):
        if "error" in skill:
            print(f"  {i}. ❌ {skill['url']}: {skill['error']}")
        else:
            print(f"  {i}. ✅ {skill['title']}")

    # Merge into unified document
    merged_path = learner.merge_skills(skills, output="batch_learned.md")
    print(f"\n📦 Merged output: {merged_path}")


if __name__ == "__main__":
    main()
