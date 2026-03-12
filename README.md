<p align="center">
  <h1 align="center">📺 B站视频转文本</h1>
  <p align="center">
    一键提取 B 站视频中的文字内容，导出为纯文本文件<br/>
    方便复制粘贴给 ChatGPT / Claude / Gemini 等 AI 工具阅读
  </p>
  <p align="center">
    <a href="https://github.com/YOUR_USERNAME/bvideo2text/releases/latest"><img src="https://img.shields.io/github/v/release/YOUR_USERNAME/bvideo2text?style=flat-square&color=blue" alt="Release"></a>
    <img src="https://img.shields.io/badge/platform-Windows-brightgreen?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square" alt="Python">
    <img src="https://img.shields.io/github/license/YOUR_USERNAME/bvideo2text?style=flat-square" alt="License">
  </p>
</p>

---

## ✨ 功能亮点

| 功能 | 说明 |
|------|------|
| � **粘贴链接即用** | 输入 B 站视频链接，点击按钮，自动完成全部流程 |
| 📝 **智能字幕提取** | 优先下载视频自带字幕（CC 字幕 / AI 字幕） |
| 🎤 **AI 语音转写** | 没有字幕？自动调用 [Whisper](https://github.com/openai/whisper) 语音识别 |
| ⚡ **GPU 加速** | 自动检测 NVIDIA 显卡，有 GPU 用 CUDA 加速，没有也能用（CPU 模式） |
| 📄 **纯文本导出** | 输出干净的 `.txt` 文件，复制粘贴即用 |
| 🎨 **暗色主题 GUI** | 简洁美观的桌面客户端，操作直观 |

## 🔄 工作流程

```
输入B站链接 → 尝试下载字幕 → 有字幕？→ 是 → 解析字幕为纯文本 → 导出 .txt
                                    → 否 → 下载音频 → Whisper AI 转写 → 导出 .txt
```

## 📦 安装使用

### 方式一：直接下载（推荐普通用户）

1. 前往 [Releases](https://github.com/YOUR_USERNAME/bvideo2text/releases/latest) 页面
2. 下载 `bvideo2text-windows.zip`
3. 解压后运行 `B站视频转文本.exe`

> ⚠️ **注意**：直接下载的版本**不包含** Whisper 语音转写功能（因为 PyTorch 体积太大）。
> 如果视频有字幕（大部分 B 站视频都有），可以正常使用。
> 如果需要 Whisper 转写功能，请使用方式二。

### 方式二：从源码运行（完整功能）

**前置要求**：
- [Python 3.8+](https://www.python.org/downloads/)
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/)（Whisper 需要）

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/bvideo2text.git
cd bvideo2text

# 安装依赖（或双击 install.bat）
pip install openai-whisper

# 运行
python main.py
```

## 🖥️ 使用方法

1. **启动程序**：运行 `B站视频转文本.exe` 或 `python main.py`
2. **粘贴链接**：将 B 站视频链接粘贴到输入框（支持 `bilibili.com/video/BVxxx`、`b23.tv/xxx`、`BVxxx` 等格式）
3. **设置输出文件夹**：点击「浏览」选择文本文件保存位置（默认桌面 `B站文本` 文件夹）
4. **点击处理**：点击「开始处理」，等待完成
5. **查看结果**：点击「打开输出文件夹」查看导出的 `.txt` 文件

## 🎛️ Whisper 模型选择

> 仅在视频没有字幕、需要语音转写时生效

| 模型 | 显存需求 | 速度 | 中文效果 | 推荐场景 |
|------|---------|------|---------|---------|
| `tiny` | ~1 GB | ⚡⚡⚡⚡ | ★★☆☆ | 快速预览 |
| `base` | ~1 GB | ⚡⚡⚡ | ★★★☆ | **日常使用（默认）** |
| `small` | ~2 GB | ⚡⚡ | ★★★★ | 较高质量 |
| `medium` | ~5 GB | ⚡ | ★★★★ | 高质量 |
| `large` | ~10 GB | 🐢 | ★★★★★ | 最佳质量 |
| `turbo` | ~6 GB | ⚡⚡ | ★★★★★ | 速度与质量平衡 |

### GPU 说明

- **有 NVIDIA 显卡**：自动检测并使用 CUDA 加速，转写速度大幅提升
- **无 NVIDIA 显卡**：自动回退到 CPU 模式，速度较慢但完全可用
- 程序启动后右下角会显示 GPU 检测状态

## 🗂️ 项目结构

```
bvideo2text/
├── main.py                   # GUI 主程序入口
├── core/
│   ├── bbdown.py             # BBDown 下载器封装
│   ├── subtitle_parser.py    # 字幕解析（SRT/ASS/JSON/LRC）
│   ├── whisper_transcribe.py # Whisper 语音转写（自动 GPU/CPU）
│   └── exporter.py           # 文本导出
├── BBDown.exe                # B站视频下载工具（by nilaoda）
├── requirements.txt          # Python 依赖
├── install.bat               # Windows 一键安装脚本
├── build.bat                 # 本地打包脚本
└── .github/workflows/
    └── release.yml           # GitHub Actions 自动打包
```

## 🙏 致谢

- [BBDown](https://github.com/nilaoda/BBDown) - 命令行式哔哩哔哩下载器
- [Whisper](https://github.com/openai/whisper) - OpenAI 通用语音识别模型

## 📄 License

MIT License
