"""
Whisper 语音转写模块
使用 faster-whisper 将音频转为文本
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
    """检查 faster_whisper 是否可用"""
    try:
        import faster_whisper
        return True
    except ImportError:
        return False


def get_device_info() -> dict:
    """获取设备信息"""
    info = {
        "device": "cpu",
        "device_name": "CPU",
        "cuda_available": False,
        "compute_type": "int8"
    }
    try:
        import torch
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["device"] = "cuda"
            info["device_name"] = torch.cuda.get_device_name(0)
            info["compute_type"] = "float16" # CUDA 通常支持 float16
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
    使用 faster-whisper 转写音频文件
    
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

    from faster_whisper import WhisperModel
    
    # 构建缓存路径
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        download_root = os.path.join(base_dir, "whisper_models")
    else:
        download_root = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
        
    os.makedirs(download_root, exist_ok=True)
    
    # 检测设备
    device_info = get_device_info()
    if log_callback:
        if device_info["cuda_available"]:
            log_callback(f"[Whisper] 检测到 GPU: {device_info['device_name']}，将使用 CUDA 加速")
        else:
            log_callback(f"[Whisper] 未检测到 CUDA GPU，将使用 CPU 模式（速度较慢）")
        log_callback(f"[Whisper] 正在加载 faster-whisper 模型: {model_name}...")

    # 加载模型
    try:
        model = WhisperModel(
            model_size_or_path=model_name,
            device=device_info["device"],
            compute_type=device_info["compute_type"],
            download_root=download_root
        )
    except Exception as e:
        if device_info["device"] == "cuda" and "cublas" in str(e).lower():
            if log_callback:
                log_callback(f"[警告] CUDA 初始化失败，可能缺少 cuBLAS/cuDNN 库。退回使用 CPU 模式！")
            device_info["device"] = "cpu"
            device_info["compute_type"] = "int8"
            model = WhisperModel(
                model_size_or_path=model_name,
                device=device_info["device"],
                compute_type=device_info["compute_type"],
                download_root=download_root
            )
        else:
            raise e
    
    if log_callback:
        log_callback(f"[Whisper] 模型加载完成，开始转写...")
        log_callback(f"[Whisper] 音频文件: {os.path.basename(audio_path)}")

    # 执行转写
    segments, info = model.transcribe(
        audio=audio_path,
        language=language,
        beam_size=5,
        vad_filter=True
    )

    full_text = []
    segment_count = 0
    
    if log_callback:
        log_callback(f"[Whisper] 检测到语言: {info.language} (概率: {info.language_probability:.2f})")
    
    for segment in segments:
        full_text.append(segment.text.strip())
        segment_count += 1
        
    text = " ".join(full_text)
    
    if log_callback:
        log_callback(f"[Whisper] 转写完成，共 {segment_count} 个片段，{len(text)} 个字符")

    return text
