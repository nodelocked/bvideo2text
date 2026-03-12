"""
B站视频转文本 GUI 工具
输入B站视频链接，下载字幕或转写音频，导出纯文本
"""

import io
import sys

# PyInstaller --windowed 模式下 sys.stdout/stderr 可能为 None，
# 导致 tqdm 等库崩溃。必须在最早期修复。
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import json
import os
import tempfile
import shutil
import re
from pathlib import Path

from core.bbdown import download_subtitles, download_audio, extract_video_title
from core.subtitle_parser import parse_subtitle_file
from core.exporter import export_text, sanitize_filename


# ============================================================
# 配置文件管理
# ============================================================

def get_config_path() -> str:
    """获取配置文件路径"""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "bvideo2text_config.json")


def load_config() -> dict:
    """加载配置"""
    default_config = {
        "output_dir": os.path.join(os.path.expanduser("~"), "Desktop", "B站文本"),
        "whisper_model": "base",
        "language": "zh",
    }
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                default_config.update(saved)
        except Exception:
            pass
    return default_config


def save_config(config: dict):
    """保存配置"""
    config_path = get_config_path()
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")


# ============================================================
# 主窗口
# ============================================================

class BVideo2TextApp:
    """B站视频转文本 主窗口"""

    WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]
    LANGUAGES = {"中文": "zh", "英文": "en", "日文": "ja", "韩文": "ko", "自动检测": None}

    def __init__(self):
        self.config = load_config()
        self.is_processing = False
        self.root = tk.Tk()
        self._setup_window()
        self._create_widgets()

    def _setup_window(self):
        """设置窗口属性"""
        self.root.title("B站视频转文本")
        self.root.geometry("780x620")
        self.root.minsize(650, 500)

        # 设置窗口图标（使用默认）
        try:
            self.root.iconbitmap(default='')
        except Exception:
            pass

        # 高 DPI 支持
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # 主题样式
        style = ttk.Style()
        style.theme_use('clam')

        # 自定义颜色
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        ACCENT = "#89b4fa"
        SURFACE = "#313244"
        BUTTON_BG = "#45475a"
        BUTTON_ACTIVE = "#585b70"
        SUCCESS = "#a6e3a1"
        WARNING = "#fab387"
        ERROR = "#f38ba8"

        self.colors = {
            "bg": BG, "fg": FG, "accent": ACCENT, "surface": SURFACE,
            "button_bg": BUTTON_BG, "button_active": BUTTON_ACTIVE,
            "success": SUCCESS, "warning": WARNING, "error": ERROR,
        }

        self.root.configure(bg=BG)

        # Style configurations
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=ACCENT, font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Status.TLabel", background=SURFACE, foreground=FG, font=("Microsoft YaHei UI", 9), padding=5)
        style.configure("TButton", font=("Microsoft YaHei UI", 10))
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TLabelframe", background=BG, foreground=FG, font=("Microsoft YaHei UI", 10))
        style.configure("TLabelframe.Label", background=BG, foreground=ACCENT, font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("TCombobox", font=("Microsoft YaHei UI", 10))

    def _create_widgets(self):
        """创建所有控件"""
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---- 标题 ----
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="📺 B站视频转文本", style="Title.TLabel").pack(side=tk.LEFT)

        # ---- 链接输入区 ----
        url_frame = ttk.LabelFrame(main_frame, text="视频链接", padding=10)
        url_frame.pack(fill=tk.X, pady=(0, 8))

        url_inner = ttk.Frame(url_frame)
        url_inner.pack(fill=tk.X)

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            url_inner, textvariable=self.url_var,
            font=("Consolas", 11), bg=self.colors["surface"],
            fg=self.colors["fg"], insertbackground=self.colors["accent"],
            relief="flat", bd=5
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.url_entry.bind('<Return>', lambda e: self._start_processing())

        # ---- 设置区 ----
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 8))

        # 输出目录
        dir_frame = ttk.Frame(settings_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(dir_frame, text="输出文件夹:").pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar(value=self.config.get("output_dir", ""))
        self.dir_entry = tk.Entry(
            dir_frame, textvariable=self.output_dir_var,
            font=("Microsoft YaHei UI", 9), bg=self.colors["surface"],
            fg=self.colors["fg"], insertbackground=self.colors["accent"],
            relief="flat", bd=3
        )
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 5), ipady=2)

        browse_btn = tk.Button(
            dir_frame, text="浏览...", command=self._browse_output_dir,
            bg=self.colors["button_bg"], fg=self.colors["fg"],
            activebackground=self.colors["button_active"], activeforeground=self.colors["fg"],
            relief="flat", padx=12, pady=2, font=("Microsoft YaHei UI", 9)
        )
        browse_btn.pack(side=tk.RIGHT)

        # Whisper 设置行
        whisper_frame = ttk.Frame(settings_frame)
        whisper_frame.pack(fill=tk.X)

        ttk.Label(whisper_frame, text="Whisper 模型:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=self.config.get("whisper_model", "base"))
        model_combo = ttk.Combobox(
            whisper_frame, textvariable=self.model_var,
            values=self.WHISPER_MODELS, state="readonly", width=10
        )
        model_combo.pack(side=tk.LEFT, padx=(8, 20))

        ttk.Label(whisper_frame, text="语言:").pack(side=tk.LEFT)
        self.lang_var = tk.StringVar(value="中文")
        # 找到当前配置对应的语言名
        saved_lang = self.config.get("language", "zh")
        for name, code in self.LANGUAGES.items():
            if code == saved_lang:
                self.lang_var.set(name)
                break
        lang_combo = ttk.Combobox(
            whisper_frame, textvariable=self.lang_var,
            values=list(self.LANGUAGES.keys()), state="readonly", width=10
        )
        lang_combo.pack(side=tk.LEFT, padx=(8, 0))

        # GPU 状态提示
        gpu_label = ttk.Label(whisper_frame, text="", font=("Microsoft YaHei UI", 9))
        gpu_label.pack(side=tk.RIGHT)
        self._update_gpu_label(gpu_label)

        # ---- 操作按钮 ----
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        self.start_btn = tk.Button(
            btn_frame, text="▶  开始处理", command=self._start_processing,
            bg=self.colors["accent"], fg="#1e1e2e",
            activebackground="#b4d0fb", activeforeground="#1e1e2e",
            relief="flat", padx=30, pady=8,
            font=("Microsoft YaHei UI", 12, "bold"),
            cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT)

        self.open_folder_btn = tk.Button(
            btn_frame, text="📂  打开输出文件夹", command=self._open_output_folder,
            bg=self.colors["button_bg"], fg=self.colors["fg"],
            activebackground=self.colors["button_active"], activeforeground=self.colors["fg"],
            relief="flat", padx=16, pady=8,
            font=("Microsoft YaHei UI", 10),
            cursor="hand2"
        )
        self.open_folder_btn.pack(side=tk.LEFT, padx=(10, 0))

        # ---- 日志区 ----
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg="#181825", fg="#cdd6f4",
            insertbackground=self.colors["accent"],
            relief="flat", bd=0, wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志文本颜色标签
        self.log_text.tag_config("info", foreground="#89b4fa")
        self.log_text.tag_config("success", foreground="#a6e3a1")
        self.log_text.tag_config("warning", foreground="#fab387")
        self.log_text.tag_config("error", foreground="#f38ba8")
        self.log_text.tag_config("bbdown", foreground="#cba6f7")

        # ---- 状态栏 ----
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel")
        status_bar.pack(fill=tk.X)

    def _update_gpu_label(self, label):
        """异步更新 GPU 状态标签"""
        def check():
            try:
                import torch
                if torch.cuda.is_available():
                    name = torch.cuda.get_device_name(0)
                    label.configure(text=f"🟢 GPU: {name}", foreground=self.colors["success"])
                else:
                    label.configure(text="🟡 CPU 模式", foreground=self.colors["warning"])
            except ImportError:
                label.configure(text="⚪ Whisper 未安装", foreground=self.colors["fg"])
        threading.Thread(target=check, daemon=True).start()

    def _browse_output_dir(self):
        """选择输出目录"""
        current = self.output_dir_var.get()
        dir_path = filedialog.askdirectory(initialdir=current if os.path.isdir(current) else None)
        if dir_path:
            self.output_dir_var.set(dir_path)
            self.config["output_dir"] = dir_path
            save_config(self.config)

    def _open_output_folder(self):
        """打开输出文件夹"""
        output_dir = self.output_dir_var.get()
        if os.path.isdir(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showinfo("提示", f"文件夹不存在: {output_dir}")

    def log(self, message: str, tag: str = ""):
        """向日志窗口添加消息"""
        def _append():
            self.log_text.configure(state=tk.NORMAL)
            # 自动检测标签类型
            auto_tag = tag
            if not auto_tag:
                if "[错误]" in message or "[ERROR]" in message:
                    auto_tag = "error"
                elif "[警告]" in message or "[WARNING]" in message:
                    auto_tag = "warning"
                elif "[信息]" in message or "[INFO]" in message:
                    auto_tag = "info"
                elif "[BBDown]" in message:
                    auto_tag = "bbdown"
                elif "[Whisper]" in message:
                    auto_tag = "info"
                elif "[导出]" in message or "✅" in message:
                    auto_tag = "success"

            self.log_text.insert(tk.END, message + "\n", auto_tag if auto_tag else ())
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.root.after(0, _append)

    def _set_status(self, text: str):
        """更新状态栏"""
        self.root.after(0, lambda: self.status_var.set(text))

    def _set_processing(self, is_processing: bool):
        """切换处理状态"""
        self.is_processing = is_processing
        def _update():
            if is_processing:
                self.start_btn.configure(
                    text="⏳  处理中...", state=tk.DISABLED,
                    bg=self.colors["button_bg"]
                )
                self.url_entry.configure(state=tk.DISABLED)
            else:
                self.start_btn.configure(
                    text="▶  开始处理", state=tk.NORMAL,
                    bg=self.colors["accent"]
                )
                self.url_entry.configure(state=tk.NORMAL)
        self.root.after(0, _update)

    def _validate_url(self, url: str) -> bool:
        """验证是否为有效的B站链接"""
        patterns = [
            r'bilibili\.com/video/',
            r'b23\.tv/',
            r'^BV\w+$',
            r'^bv\w+$',
            r'^av\d+$',
            r'^ep\d+$',
            r'^ss\d+$',
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in patterns)

    def _start_processing(self):
        """开始处理"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入B站视频链接")
            return
        if not self._validate_url(url):
            messagebox.showwarning("提示", "请输入有效的B站视频链接\n支持格式: bilibili.com/video/BVxxx, b23.tv/xxx, BVxxx, avxxx 等")
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("提示", "请设置输出文件夹")
            return

        # 保存配置
        self.config["output_dir"] = output_dir
        self.config["whisper_model"] = self.model_var.get()
        self.config["language"] = self.LANGUAGES.get(self.lang_var.get(), "zh")
        save_config(self.config)

        # 清空日志
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # 在后台线程执行
        self._set_processing(True)
        thread = threading.Thread(target=self._process_video, args=(url, output_dir), daemon=True)
        thread.start()

    def _process_video(self, url: str, output_dir: str):
        """后台线程：处理视频"""
        temp_dir = None
        try:
            self.log("=" * 60)
            self.log(f"🎬 开始处理: {url}", "info")
            self.log("=" * 60)
            self._set_status("正在获取视频信息...")

            # 创建临时工作目录
            temp_dir = tempfile.mkdtemp(prefix="bvideo2text_")
            self.log(f"[信息] 临时工作目录: {temp_dir}")

            # 1. 获取视频标题
            self._set_status("正在获取视频标题...")
            video_title = extract_video_title(url, temp_dir, self.log)
            self.log(f"[信息] 视频标题: {video_title}", "info")

            # 2. 尝试下载字幕
            self._set_status("正在尝试下载字幕...")
            subtitle_files = download_subtitles(url, temp_dir, self.log)

            text_content = ""
            source_type = ""

            if subtitle_files:
                # 有字幕文件，解析它
                self.log(f"[信息] 找到字幕文件，正在解析...", "success")
                self._set_status("正在解析字幕文件...")

                all_texts = []
                for sf in subtitle_files:
                    self.log(f"[信息] 解析: {os.path.basename(sf)}")
                    parsed = parse_subtitle_file(sf)
                    if parsed:
                        all_texts.append(parsed)

                if all_texts:
                    text_content = '\n\n'.join(all_texts)
                    source_type = "B站字幕"
                    self.log(f"✅ 字幕解析完成，共 {len(text_content)} 个字符", "success")

            if not text_content:
                # 没有字幕，走 Whisper 转写流程
                self.log("[信息] 未找到可用字幕，将下载音频并使用 Whisper 转写", "warning")
                self._set_status("正在下载音频...")

                audio_path = download_audio(url, temp_dir, self.log)
                if not audio_path:
                    self.log("[错误] 音频下载失败，无法继续", "error")
                    self._set_status("处理失败")
                    return

                # 检查 Whisper 是否可用
                from core.whisper_transcribe import check_whisper_available, transcribe
                if not check_whisper_available():
                    self.log("[错误] Whisper 未安装！请运行: pip install openai-whisper", "error")
                    self._set_status("处理失败 - Whisper 未安装")
                    return

                self._set_status("正在使用 Whisper 转写音频（可能需要几分钟）...")
                model_name = self.model_var.get()
                language = self.LANGUAGES.get(self.lang_var.get(), "zh")

                text_content = transcribe(
                    audio_path,
                    model_name=model_name,
                    language=language,
                    log_callback=self.log
                )
                source_type = f"Whisper 转写 (模型: {model_name})"

                if not text_content:
                    self.log("[错误] 转写结果为空", "error")
                    self._set_status("处理失败")
                    return

                self.log(f"✅ 转写完成，共 {len(text_content)} 个字符", "success")

            # 3. 导出文本
            self._set_status("正在导出文本...")
            filepath = export_text(
                text=text_content,
                video_title=video_title,
                video_url=url,
                output_dir=output_dir,
                source_type=source_type,
                log_callback=self.log
            )

            self.log("")
            self.log("=" * 60)
            self.log(f"✅ 处理完成！", "success")
            self.log(f"📄 文件: {filepath}", "success")
            self.log("=" * 60)
            self._set_status(f"完成 - {os.path.basename(filepath)}")

        except Exception as e:
            self.log(f"[错误] 处理过程中出错: {e}", "error")
            import traceback
            self.log(traceback.format_exc(), "error")
            self._set_status("处理失败")

        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.log("[信息] 临时文件已清理")
                except Exception:
                    pass
            self._set_processing(False)

    def run(self):
        """启动应用"""
        self.root.mainloop()


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    app = BVideo2TextApp()
    app.run()
