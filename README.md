<p align="center">
  <h1 align="center">📺 B站视频转文本</h1>
  <p align="center">
    一键提取 B 站视频中的文字内容，导出为纯文本文件<br/>
    方便复制粘贴给 ChatGPT / Claude / Gemini 等 AI 工具阅读
  </p>
</p>

---

## ✨ 功能亮点

| 功能 | 说明 |
|------|------|
| 🔗 **粘贴链接即用** | 输入 B 站视频链接，点击按钮，自动完成全部流程 |
| 📝 **智能字幕提取** | 优先下载视频自带字幕（CC 字幕 / AI 字幕） |
| 🎤 **AI 语音转写** | 没有字幕？自动调用 [Whisper](https://github.com/openai/whisper) 语音识别 |
| ⚡ **GPU 加速** | 自动检测 NVIDIA 显卡，有 GPU 用 CUDA 加速，没有也能用 |
| 🔄 **繁简转换** | 自动将繁体中文转为简体中文 |
| 📄 **纯文本导出** | 输出干净的 `.txt` 文件，保留完整标点符号 |

## � 下载使用

前往 [Releases](../../releases/latest) 页面下载，根据需求选择版本：

| 文件 | 说明 | 适合场景 |
|------|------|---------|
| `bvideo2text-base.zip` | **推荐** - 内置 base 模型 | 日常使用，速度快效果好 |
| `bvideo2text-tiny.zip` | 内置 tiny 模型 | 电脑配置低 / 追求速度 |
| `bvideo2text-small.zip` | 内置 small 模型 | 需要更好的转写效果 |
| `bvideo2text-medium.zip` | 内置 medium 模型 | 高质量转写 |
| `bvideo2text-large.zip` | 内置 large 模型 | 最佳转写效果 |
| `bvideo2text-turbo.zip` | 内置 turbo 模型 | 速度与质量平衡 |
| `bvideo2text-all-models.zip` | 不带模型，首次转写时在线下载 | 想灵活切换模型 |
| `bvideo2text-lite.zip` | 精简版，需 Python 环境 | 开发者 / 极小安装包 |

**下载后**：解压 → 双击 `B站视频转文本-xxx.exe` → 开始使用

## 🖥️ 使用方法

1. **粘贴链接**：将 B 站视频链接粘贴到输入框（支持 `bilibili.com/video/BVxxx`、`b23.tv/xxx`、`BVxxx` 等）
2. **设置输出文件夹**：选择文本文件保存位置（默认桌面 `B站文本` 文件夹）
3. **点击「开始处理」**：等待完成即可
4. **查看结果**：点击「打开输出文件夹」查看 `.txt` 文件

## 🔧 从源码运行（完整功能）

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/bvideo2text.git
cd bvideo2text

# 下载 BBDown.exe 放到项目根目录
# https://github.com/nilaoda/BBDown/releases

# 安装依赖（或双击 install.bat）
pip install -r requirements.txt

# 运行
python main.py
```

**前置要求**：Python 3.8+、[ffmpeg](https://www.gyan.dev/ffmpeg/builds/)

## 🎛️ Whisper 模型对比

| 模型 | 显存 | 速度 | 中文效果 | 推荐 |
|------|------|------|---------|-----|
| `tiny` | ~1 GB | ⚡⚡⚡⚡ | ★★☆ | 电脑配置低 |
| `base` | ~1 GB | ⚡⚡⚡ | ★★★ | **日常使用** |
| `small` | ~2 GB | ⚡⚡ | ★★★★ | 较高质量 |
| `medium` | ~5 GB | ⚡ | ★★★★ | 高质量 |
| `large` | ~10 GB | 🐢 | ★★★★★ | 最佳 |
| `turbo` | ~6 GB | ⚡⚡ | ★★★★★ | 速度与质量平衡 |

- **有 NVIDIA 显卡** → 自动 GPU 加速
- **无 NVIDIA 显卡** → 自动 CPU 模式，建议选 `tiny` 或 `base`

## 🗂️ 项目结构

```
bvideo2text/
├── main.py                 # GUI 主程序
├── core/
│   ├── bbdown.py           # BBDown 封装
│   ├── subtitle_parser.py  # 字幕解析（SRT/ASS/JSON/LRC）
│   ├── whisper_transcribe.py # Whisper 转写（自动 GPU/CPU）
│   └── exporter.py         # 文本导出 + 繁简转换
├── requirements.txt
├── install.bat             # 一键安装
├── build.bat               # 本地打包
└── .github/workflows/
    └── release.yml         # CI：tag 触发，按模型打包
```

## 📋 发布流程

推送 tag 触发自动打包：

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions 会自动为每个 Whisper 模型构建独立安装包并发布到 Releases。

## 🙏 致谢

- [BBDown](https://github.com/nilaoda/BBDown) - 哔哩哔哩下载器
- [Whisper](https://github.com/openai/whisper) - OpenAI 语音识别
- [OpenCC](https://github.com/BYVoid/OpenCC) - 繁简转换

## 📄 License

MIT License
