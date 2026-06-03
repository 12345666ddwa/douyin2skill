# 🎬 douyin2skill — 别再收藏夹吃灰了，抖音教程，AI替你一键学会

> 把抖音教程视频自动转化为可复用的AI Agent技能。全本地运行，零API费用。专为中国网络环境优化。

---

## 目录

- [为什么做这个](#为什么做这个)
- [核心能力](#核心能力)
- [快速开始](#快速开始)
- [工作原理详解](#工作原理详解)
- [架构设计](#架构设计)
- [降级策略](#降级策略)
- [实战案例](#实战案例)
- [FAQ](#faq)
- [贡献指南](#贡献指南)

---

## 为什么做这个

**问题：** 每天刷抖音，看到好的编程/技术教程 → 点赞收藏 → 再也没打开过。收藏夹成了"赛博坟场"。

**根因：** "收藏"这个动作太轻了，它只解决了"我怕以后找不到"的焦虑，但没有解决"我真的要学会"的需求。

**解法：** douyin2skill 接过"学会"这个重任。你发链接，它自动：

1. 解析短链接 → 绕过反爬获取视频源
2. 下载视频 → 三通道并行分析（语音+字幕+画面）
3. 多源交叉验证 → GitHub API精确定位项目身份
4. 输出结构化AI技能文件 → 下次你问"这怎么做"，AI直接就能回答

---

## 核心能力

### 🎯 三通道视频理解

| 通道 | 技术 | 擅长 | 局限 |
|:----|:-----|:-----|:-----|
| **语音** | OpenAI Whisper (base/small) | 中文讲解内容 | 技术术语口音误识 |
| **字幕** | PaddleOCR / EasyOCR | 内嵌字幕精确文字 | 小字/特殊字体乱码 |
| **视觉** | Qwen2-VL-2B (本地GPU) | 代码/GUI/界面/图表 | 需8GB+显存 |

**三通道互补。** 单个通道可能有30%错误率，三通道交叉验证后正确率可达95%+。

### 🔺 多源三角定位

```
Whisper输出: "get-up上的保障项目，灯顶开元热绑了"
                              ↓ 音韵还原
                           "GitHub" "登顶开源热榜"
                                    +
OCR输出:    "Prompl Garden" "Chrome Etension"
                              ↓ 形态还原
                        "Prompt Garden" "Chrome Extension"
                                    +
页面元数据:  "#GitHub #AI工具 #token #提示词优化"
                                    ↓
                    GitHub API 交叉搜索验证
                                    ↓
              linshenkx/prompt-optimizer ⭐29,229 ✅
```

### 🔄 自适应降级链

在中国网络环境下，任何环节都可能被反爬。douyin2skill 内置4层降级：

```
L1: HTTP请求/API（最快）
L2: 浏览器JS注入DOM（绕过简单反爬）
L3: Windows桥接 PyAutoGUI 控制真实Chrome（绕过高级反爬）
L4: AI桌面操控 Agent S（终极方案）
```

---

## 快速开始

### 环境要求

- Python 3.10+
- ffmpeg（用于音频提取和关键帧）
- （可选）NVIDIA GPU + 8GB+ VRAM（用于Qwen2-VL视觉理解）
- （可选）Windows + PyAutoGUI（用于L3降级）

### 安装

```bash
git clone https://github.com/YOUR_USERNAME/douyin2skill.git
cd douyin2skill

# 基础安装（只用Whisper+OCR）
pip install -e ".[basic]"

# 完整安装（含Qwen2-VL视觉理解）
pip install -e ".[full]"
```

### 第一次使用

```python
from douyin2skill import Pipeline

# 创建管线（use_vision=True需要GPU）
pipe = Pipeline(use_vision=True)

# 发链接，等结果
skill = pipe.learn("https://v.douyin.com/xxxxx/")

# 查看学到了什么
print(f"📹 {skill.title}")
print(f"📝 {skill.summary}")
print(f"🔗 相关项目: {skill.github_repo}")

# 保存为Hermes Skill文件
skill.save("my_skill.md")
```

### 命令行

```bash
# 基础模式（只用Whisper）
douyin2skill "https://v.douyin.com/xxxxx/"

# 完整模式
douyin2skill "https://v.douyin.com/xxxxx/" --vision --output learned_skill.md

# 批量模式
douyin2skill batch urls.txt --parallel 3 --output merged.md
```

---

## 工作原理详解

### 完整管线

```
用户发来抖音短链接
    ↓
① 短链接解析（curl重定向追踪，零成本）
    https://v.douyin.com/xxxx/ → https://www.douyin.com/video/123456
    ↓
② 浏览器打开页面（budget管理：3次/会话）
    ↓
③ JS提取视频源地址（绕过yt-dlp的cookie限制）
    performance.getEntriesByType('resource') 处理音视频分离
    ↓
④ 立即下载（URL有时效性，temp=1参数）
    Python requests + 仿浏览器headers
    ↓
⑤ ffmpeg双遍提取
    第一遍: fps=0.1 + crop字幕区域 → OCR读字幕
    第二遍: fps=0.2 + 全帧 → Qwen2-VL理解画面
    ↓
⑥ 三通道并行分析
    ├─ Whisper: 16kHz WAV → base/small模型 → 中文分段
    ├─ PaddleOCR: 字幕帧 → 去重合并
    └─ Qwen2-VL: 关键帧 → prompt差异策略（字幕/代码/GUI不同prompt）
    ↓
⑦ 三角定位验证
    Whisper关键词 + OCR关键片段 + 页面元数据 → GitHub API → 精确项目
    ↓
⑧ 结构化输出
    概念层 + 操作层 + 案例层 + 技巧层 → Skill文件
    ↓
⑨ 清理临时文件
```

### 浏览器预算管理

抖音对单次会话约限制3次页面加载。douyin2skill 自动管理预算：

- 先用 curl 解析所有短链接（无限次）
- 从标题预判优先级
- 只对最重要的2-3个视频开浏览器
- 其余用元数据推测（标题+描述已含80%+信息）

### 帧率选择策略

| 视频时长 | fps | 帧数 | 适用场景 |
|:--------|:---:|:----:|:--------|
| < 1分钟 | 0.5 | ~30 | 短教程，逐帧 |
| 1-3分钟 | 0.2 | ~36 | 中等，关键帧覆盖 |
| 3-5分钟 | 0.1 | ~21-30 | 长视频，平衡效率 |
| > 5分钟 | 0.05 | ~15-20 | 超长，只取关键点 |

**关键帧选择（不全部分析）：** 均匀分布取5-6帧，而非全帧逐帧分析。11分钟视频从133帧→采22帧→选6帧，节省85%计算量，效果不减。

---

## 架构设计

```
douyin2skill/
├── douyin2skill/
│   ├── __init__.py
│   ├── pipeline.py           # Pipeline(单视频) / BatchLearner(批量)
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── link_resolver.py   # 短链接解析
│   │   ├── video_source.py    # 浏览器提取视频源
│   │   ├── downloader.py      # 视频下载
│   │   └── frame_extractor.py # 关键帧提取
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── whisper_stt.py     # Whisper语音转写
│   │   ├── ocr_reader.py      # OCR字幕读取
│   │   ├── qwen2vl_vision.py  # Qwen2-VL视觉理解
│   │   └── triangulator.py    # 多源三角定位
│   ├── skill_builder.py       # Skill构建器
│   └── utils.py               # 工具函数
├── skills/                     # 预置Skill模板
├── examples/                   # 使用示例
├── docs/                       # 文档
├── setup.py
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 降级策略

### 视频源获取降级

| 尝试 | 方法 | 适用 |
|:---:|:-----|:-----|
| 1 | `document.querySelectorAll('video source')` | 正常页面 |
| 2 | `performance.getEntriesByType('resource')` | 音视频分离 |
| 3 | browser_vision 截图 + OCR | JS执行受阻 |
| 4 | 放弃下载，仅用页面元数据 | 全面封锁 |

### 内容分析降级

| 优先级 | 方案 | 条件 |
|:-----:|:-----|:-----|
| ★ | Qwen2-VL 视觉理解 | GPU可用 |
| 1 | PaddleOCR 字幕 | 有可见字幕 |
| 2 | Whisper 音频 | 有语音讲解 |
| 3 | 页面元数据推测 | 上述均不可用 |

### Qwen2-VL提示词策略（踩坑总结）

| 画面类型 | ✅ 推荐prompt | ❌ 错误prompt | 
|:--------|:-------------|:------------|
| 字幕/底部文字 | "逐字输出所有中文文字" | "详细描述" → 返回坐标 |
| 复杂UI（小字密集） | "逐行提取所有可见文字，每行一个" | "描述" → `(133,103),(889,889)` |
| 代码/终端截图 | "提取所有代码行，保留原样" | "文字内容" → 省略格式 |
| GitHub页面/列表 | "列出项目名、star数、描述，每行一个" | "画面内容" → 循环重复 |

---

## 实战案例

### 案例1：精确识别GitHub项目

**输入：** 抖音教程"自动优化提示词的神器"

| 来源 | 输出 | 质量 |
|:----|:-----|:---:|
| Whisper | "get-up上的保障项目，灯顶开元热绑了" | ⭐⭐ |
| OCR | "Prompl Garden" "Chrome Etension" "提示花旮" | ⭐⭐ |
| 页面元数据 | "#GitHub #AI工具 #token #自动优化提示词" | ⭐⭐⭐⭐ |

**三角定位结果：** `linshenkx/prompt-optimizer` ⭐29,229  
**验证：** GitHub API desc匹配 + stars匹配 + Chrome Extension匹配 ✅

### 案例2：批量8个视频学习

**输入：** 8个抖音链接（AI工具合集系列）  
**策略：** 元数据优先 — 只下载3个最重要的，其余5个从标题+描述提取  
**结果：** 完整技能分类图谱（11个类别的Hermes技能），仅用2次浏览器导航

### 案例3：音视频分离处理

**现象：** `document.querySelectorAll('video source')` 返回空数组，`video.currentSrc` 返回 `blob:`  
**根因：** 抖音视频流+音频流分离为两个独立URL  
**解法：** `performance.getEntriesByType('resource')` 分别提取视频和音频URL → ffmpeg合并

---

## FAQ

**Q: 需要抖音登录吗？**  
A: 不需要。通过curl解析短链接 + 浏览器JS提取视频源，全程无需登录。

**Q: Qwen2-VL 一定要GPU吗？**  
A: 不必须。没有GPU时自动降级到OCR+Whisper方案，效果也够用。有GPU时视觉理解更全面（能看懂代码和界面）。

**Q: 能处理YouTube/B站吗？**  
A: 当前专注抖音。架构上已预留扩展接口，欢迎贡献其他平台的extractor。

**Q: 和yt-dlp的区别？**  
A: yt-dlp 的抖音extractor需要Chrome cookies（WSL/CICD下不可用）。douyin2skill通过浏览器JS注入直接提取视频源，无需cookies。

**Q: 学习结果存在哪？**  
A: 输出为Hermes Skill格式（Markdown + YAML frontmatter），可直接被Hermes Agent加载。也可以纯文本/JSON输出。

**Q: 有中文口音问题吗？**  
A: Whisper base模型对标准中文效果良好。遇到口音重的情况，三通道交叉验证会自动纠正。实测"命令→面临" "GitHub→get-up"等常见误识可以被三角定位修正。

---

## 贡献指南

欢迎一切形式的贡献！

**特别需要：**
- 🐛 新的抖音反爬方案的发现报告
- 🔌 其他视频平台（B站/YouTube/小红书）的支持
- 🎯 更准的中文ASR模型推荐
- 🧪 更多视频类型的测试case

**提交PR前：**
1. 确保代码通过 `python -m pytest`
2. 新增功能需要配example
3. 中文注释允许，docstring用英文

---

## 致谢

本项目深度依赖以下开源项目：
- [OpenAI Whisper](https://github.com/openai/whisper) — 语音转写
- [Qwen2-VL](https://github.com/QwenLM/Qwen2-VL) — 视觉理解
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — 中文OCR
- [ffmpeg](https://ffmpeg.org/) — 音视频处理

---

## 📄 License

MIT © 2025

---

<p align="center">
  <sub>如果你也有一个吃灰的抖音收藏夹，给这个项目一个⭐吧。<br>
  每一个star都是对"学了比收藏更有用"的投票。</sub>
</p>
