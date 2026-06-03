"""Qwen2-VL visual analysis — understand video frames with a local vision model.

Uses Qwen2-VL-2B (fp16, ~4GB VRAM) to read subtitles, understand code/GUI,
identify GitHub pages, and extract structured info from video frames.

Requirements: NVIDIA GPU with 8GB+ VRAM, transformers + accelerate.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Prompt templates optimized for different frame types
# ⚠️ Using wrong prompts causes:
#   - "详细描述" on dense UI → model returns (x1,y1),(x2,y2) coordinates
#   - "描述画面" on lists → model loops repeating first few items
#   - high max_tokens on lists → model hallucinates extra items

PROMPTS = {
    "subtitle": (
        "请详细读取这张图片中所有的中文字幕/文字内容，逐字输出。"
    ),
    "ui_dense": (
        "逐行提取这张图片中的所有可见文字。"
        "只输出文字内容，不要加描述。格式：每行一个文本片段。"
    ),
    "code": (
        "提取这张图片中的所有代码行或终端输出文字。保留代码原样。"
    ),
    "github": (
        "列出这张图片中的所有项目名称、分类标题、star数、描述。"
        "只输出项目名和数值。"
    ),
    "general": (
        "请描述这张图片中的内容。"
        "包括：1) 所有可见文字  2) 界面元素  3) 代码或技术术语。"
    ),
}


def analyze_frames(
    frames_dir: Path,
    model_name: str = "Qwen/Qwen2-VL-2B-Instruct",
    max_tokens: int = 500,
) -> str:
    """Analyze video frames with Qwen2-VL.

    Uses adaptive prompts based on content type detection.

    Args:
        frames_dir: Directory with frame images
        model_name: HuggingFace model name
        max_tokens: Max new tokens per frame

    Returns:
        Concatenated analysis text from all frames
    """
    import os
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    try:
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        import torch
    except ImportError:
        raise ImportError(
            "Qwen2-VL requires: pip install transformers accelerate torch pillow qwen-vl-utils"
        )

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if not frames:
        logger.warning("No frames to analyze")
        return ""

    # Load model (cached after first run)
    logger.info(f"Loading {model_name}...")
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(model_name)
    logger.info(f"Model loaded on {model.device}")

    results = []
    for i, frame in enumerate(frames):
        try:
            text = _analyze_single_frame(
                frame, model, processor, max_tokens
            )
            if text:
                results.append(f"[帧{i+1:02d}] {text}")
        except Exception as e:
            logger.debug(f"Frame {i} analysis failed: {e}")
            continue

    # Free GPU memory
    del model, processor
    import torch
    torch.cuda.empty_cache()

    return "\n\n".join(results)


def _analyze_single_frame(
    frame_path: Path,
    model,
    processor,
    max_tokens: int = 500,
) -> str:
    """Analyze a single frame with Qwen2-VL."""
    from PIL import Image
    import torch

    image = Image.open(frame_path)

    # Auto-detect content type and select prompt
    prompt = _select_prompt(frame_path)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(
        text=[text], images=[image], padding=True, return_tensors="pt"
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=max_tokens)

    output = processor.batch_decode(
        generated_ids, skip_special_tokens=True
    )[0]

    # Extract assistant response
    if "assistant" in output:
        output = output.split("assistant")[-1].strip()

    # Clean up
    del inputs, generated_ids, image
    torch.cuda.empty_cache()

    return output


def _select_prompt(frame_path: Path) -> str:
    """Select the best prompt based on heuristics about the frame.

    In a full implementation, this would use image analysis
    to detect content type. For now, use the general prompt.
    """
    # TODO: Implement content type detection
    # - Large text ratio → subtitle prompt
    # - Many small rectangles → UI dense prompt
    # - Monospace text → code prompt
    return PROMPTS["general"]
