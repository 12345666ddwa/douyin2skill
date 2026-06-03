from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="douyin2skill",
    version="0.1.0",
    author="douyin2skill contributors",
    description="Turn Douyin tutorial videos into reusable AI Agent skills — automatically",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/douyin2skill",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.28",
        "openai-whisper>=20231117",
        "pyyaml>=6.0",
    ],
    extras_require={
        "ocr": ["paddleocr>=2.7", "easyocr>=1.7"],
        "vision": [
            "torch>=2.1",
            "transformers>=4.40",
            "accelerate>=0.28",
            "pillow>=10.0",
            "qwen-vl-utils>=0.0.8",
        ],
        "full": [
            "paddleocr>=2.7",
            "easyocr>=1.7",
            "torch>=2.1",
            "transformers>=4.40",
            "accelerate>=0.28",
            "pillow>=10.0",
            "qwen-vl-utils>=0.0.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "douyin2skill=douyin2skill.cli:main",
        ],
    },
)
