# 🎬 douyin2skill — 别再收藏夹吃灰了，抖音教程，AI替你一键学会

<p align="center">
  <i>Turn Douyin tutorial videos into reusable AI Agent skills — automatically.<br>
  Zero API cost. Fully local. Built for the Chinese internet.</i>
</p>

<p align="center">
  <img src="docs/assets/demo.gif" width="650" alt="Demo: link in, skill out">
</p>

---

## 🤔 你遇到过吗？

刷到个好教程 → ❤️点赞 → ⭐收藏 → 再也没打开过。

**douyin2skill 把这个循环打断。** 你发一条抖音链接 → 自动下载视频 → 语音转写 + 画面理解 + 代码识别 → 输出一个可复用的AI技能文件。就像给AI装了一个"自动消化教程的大脑"。

---

## ✨ 三句话看懂

| 你做什么 | 它做什么 | 耗时 |
|:---------|:---------|:----:|
| 🔗 发一条抖音链接 | 解析短链 → 浏览器提取视频源 → 下载 | 5s |
| ⏳ 等待分析 | Whisper语音 + PaddleOCR字幕 + Qwen2-VL视觉 三通道并跑 | 30-90s |
| 📦 获得Skill | 结构化笔记 + 可复用Hermes Skill文件 | ✅ |

---

## 🧠 凭什么比别人强？

### 其他方案的问题

| 方法 | 痛点 |
|:-----|:-----|
| yt-dlp | 抖音需要浏览器 cookies，WSL/CICD下直接**不可用** |
| 单一ASR | 技术术语误识别严重：`"命令"→"面临"` `"GitHub"→"get-up"` |
| 纯OCR | 小字/特殊字体乱码：`"Prompt Garden"→"Prompl Garden"` |
| API方案 | 视频分钟数 × API单价 = 💸 |

### douyin2skill 的解法

```
抖音链接
    ↓
┌───────────────────────────────────────────┐
│  三通道并行理解（全部本地，零费用）           │
│                                            │
│  🅰 Whisper 音频转写   → 语音内容（口音自适应）│
│  🅱 PaddleOCR 字幕提取 → 字幕文字（双遍策略）  │
│  🅲 Qwen2-VL 视觉理解  → 代码/GUI/界面（本地GPU）│
│                                            │
│  ↓ 三源合并 ↓                               │
│                                            │
│  🔺 多源三角定位 → GitHub API交叉验证项目身份  │
└───────────────────────────────────────────┘
    ↓
结构化学习笔记 → Hermes Skill 文件
```

---

## 🚀 5分钟跑起来

### 前提条件

- Python 3.10+
- ffmpeg
- （可选）NVIDIA GPU + 8GB+ 显存 → 启用 Qwen2-VL 视觉理解

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/douyin2skill.git
cd douyin2skill
pip install -e .
```

### 基础用法

```python
from douyin2skill import Pipeline

# 单视频学习
pipe = Pipeline(use_vision=True)   # 启用GPU视觉理解
skill = pipe.learn("https://v.douyin.com/xxxxx/")

print(skill.title)
print(skill.summary)
skill.save("my_new_skill.md")
```

```bash
# 命令行直接使用
douyin2skill "https://v.douyin.com/xxxxx/" --output my_skill.md --vision
```

### 批量学习

```python
from douyin2skill import BatchLearner

urls = [
    "https://v.douyin.com/video1/",
    "https://v.douyin.com/video2/",
    "https://v.douyin.com/video3/",
]

learner = BatchLearner(max_parallel=3)
skills = learner.learn_all(urls)
learner.merge_skills(skills, output="merged_toolkit.md")
```

---

## 🏗️ 架构设计

### L1→L4 自适应降级链

在中国网络环境下，任一环节被反爬，自动切换备选方案：

```
L1 程序化请求  → browser API / requests（最快）
    ↓ 被封
L2 DOM提取    → browser_console JS注入 提取视频源
    ↓ 被封
L3 Windows桥接 → cmd.exe → Windows Python → PyAutoGUI 控制真实浏览器
    ↓ 被封
L4 AI桌面操控  → Agent S 操控整个桌面
```

**你可能用不到L3/L4，但它们一直在那里。**

### 核心模块

```
douyin2skill/
├── pipeline.py           # 主入口：Pipeline / BatchLearner
├── extractors/
│   ├── link_resolver.py  # 短链接 → 完整URL
│   ├── video_source.py   # 浏览器JS提取视频源（绕过yt-dlp限制）
│   ├── downloader.py     # 视频下载 + 音视频分离处理
│   └── frame_extractor.py # 关键帧提取 + 双遍策略
├── analyzers/
│   ├── whisper_stt.py    # Whisper语音转写
│   ├── ocr_reader.py     # PaddleOCR/EasyOCR字幕
│   ├── qwen2vl_vision.py # Qwen2-VL本地视觉理解
│   └── triangulator.py   # 多源三角定位（Whisper+OCR+元数据→GitHub验证）
├── skill_builder.py      # 学习笔记 → Hermes Skill
└── utils.py              # 清理/日志/代理管理
```

---

## 📊 实测效果

| 视频 | 时长 | 方法 | 准确率 | 备注 |
|:-----|:----:|:----|:------:|:-----|
| "让你拥有真人AI Agent" | 22s | Qwen2-VL + Whisper | ✅ 95% | 精准定位 `gui-agents` → Agent S (⭐11.2k) |
| "港大开源神级项目" | 1min | 三角定位 | ✅ | 从模糊关键词定位 `CLI-Anything` (HKUDS) |
| "编程名词扫盲之GitHub" | 7min | Whisper only | ✅ 85% | 口音中等，关键概念完整 |

**Whisper 中文纠错**：
- `"get-up"` → `"GitHub"` ✅ 
- `"灯顶开元"` → `"登顶开源"` ✅
- `"面临"` → `"命令"` ✅

---

## 🌐 针对中国网络优化

| 问题 | 解法 |
|:-----|:-----|
| GitHub 被墙 | 自动走 `ghproxy` / 直连重试 |
| HuggingFace 不可达 | `HF_ENDPOINT=https://hf-mirror.com` |
| 抖音反爬（3次/会话限制） | 浏览器预算管理 + 元数据优先策略 |
| 视频URL过期（temp=1） | 提取后立即下载，不缓存URL |
| 音视频分离（blob URL） | performance.getEntries 提取真URL → ffmpeg合并 |

---

## 🤝 贡献 & 路线图

- [ ] Web UI 界面
- [ ] B站 / YouTube 支持
- [ ] 更多视觉模型（Qwen2-VL-7B）
- [ ] WeChat Bot 集成（手机上发链接→自动学习）

欢迎提 Issue / PR！尤其欢迎：
- 新的抖音反爬方案的报告
- 更多视频平台的支持
- 更好的中文ASR模型建议

---

## 📄 License

MIT © 2025

---

<p align="center">
  <sub>Built with ❤️ for the Chinese developer community.<br>
  If this saved you from bookmark-hell, give it a ⭐</sub>
</p>
