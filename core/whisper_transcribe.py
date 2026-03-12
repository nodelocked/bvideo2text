"""
Whisper 语音转写模块
使用 OpenAI Whisper 将音频转为文本
自动检测 CUDA GPU，有则用GPU加速，无则用CPU
"""

import io
import os
import sys
from typing import Optional, Callable


def _fix_stdio():
    """
    修复 PyInstaller --windowed 模式下 sys.stdout/stderr 为 None 的问题。
    tqdm 等库依赖 sys.stderr.write()，为 None 时会崩溃。
    """
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()


def check_whisper_available() -> bool:
    """检查 whisper 是否可用"""
    try:
        import whisper
        return True
    except ImportError:
        return False


def get_device_info() -> dict:
    """获取设备信息"""
    info = {
        "device": "cpu",
        "device_name": "CPU",
        "cuda_available": False,
    }
    try:
        import torch
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["device"] = "cuda"
            info["device_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return info


def transcribe(
    audio_path: str,
    model_name: str = "base",
    language: str = "zh",
    log_callback: Optional[Callable] = None
) -> str:
    """
    使用 Whisper 转写音频文件
    
    Args:
        audio_path: 音频文件路径
        model_name: Whisper 模型名称 (tiny, base, small, medium, large, turbo)
        language: 语言代码，默认中文
        log_callback: 日志回调函数
    
    Returns:
        转写后的文本
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    # 修复打包后 stdio 为 None 的问题
    _fix_stdio()

    # 如果是打包后的程序，检查是否有内置模型文件
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        bundled_models = os.path.join(base_dir, "whisper_models")
        if os.path.isdir(bundled_models):
            # 将内置模型目录设置为 whisper 缓存目录
            os.environ["XDG_CACHE_HOME"] = base_dir
            # whisper 会在 {XDG_CACHE_HOME}/whisper/ 下查找模型
            # 但我们的模型在 whisper_models/，需要重命名或软链接
            whisper_cache = os.path.join(base_dir, "whisper")
            if not os.path.exists(whisper_cache):
                try:
                    os.rename(bundled_models, whisper_cache)
                except Exception:
                    # 如果重命名失败，直接设置环境变量指向原目录
                    import shutil
                    shutil.copytree(bundled_models, whisper_cache, dirs_exist_ok=True)
            if log_callback:
                log_callback(f"[Whisper] 使用内置模型文件")

    import whisper
    
    # 检测设备
    device_info = get_device_info()
    if log_callback:
        if device_info["cuda_available"]:
            log_callback(f"[Whisper] 检测到 GPU: {device_info['device_name']}，将使用 CUDA 加速")
        else:
            log_callback(f"[Whisper] 未检测到 CUDA GPU，将使用 CPU 模式（速度较慢）")
        log_callback(f"[Whisper] 正在加载模型: {model_name} ...")

    # 加载模型
    model = whisper.load_model(model_name, device=device_info["device"])
    
    if log_callback:
        log_callback(f"[Whisper] 模型加载完成，开始转写...")
        log_callback(f"[Whisper] 音频文件: {os.path.basename(audio_path)}")

    # 执行转写
    result = model.transcribe(
        audio_path,
        language=language,
        verbose=False
    )

    text = result.get("text", "")
    
    segments = result.get("segments", [])
    
    if log_callback:
        log_callback(f"[Whisper] 转写完成，共 {len(segments)} 个片段，{len(text)} 个字符")

    return text
