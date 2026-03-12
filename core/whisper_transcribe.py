"""
Whisper 语音转写模块
使用 OpenAI Whisper 将音频转为文本
自动检测 CUDA GPU，有则用GPU加速，无则用CPU
"""

import os
from typing import Optional, Callable


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
    
    # 也收集带时间戳的段落（可选用）
    segments = result.get("segments", [])
    
    if log_callback:
        log_callback(f"[Whisper] 转写完成，共 {len(segments)} 个片段，{len(text)} 个字符")

    return text


def transcribe_with_segments(
    audio_path: str,
    model_name: str = "base",
    language: str = "zh",
    log_callback: Optional[Callable] = None
) -> tuple:
    """
    转写并返回分段结果
    
    Returns:
        (full_text, segments_list)
        segments_list: [{"start": float, "end": float, "text": str}, ...]
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音频文件不存在: {audio_path}")

    import whisper
    
    device_info = get_device_info()
    if log_callback:
        device_desc = device_info['device_name'] if device_info['cuda_available'] else 'CPU'
        log_callback(f"[Whisper] 使用设备: {device_desc}，模型: {model_name}")

    model = whisper.load_model(model_name, device=device_info["device"])
    
    if log_callback:
        log_callback(f"[Whisper] 开始转写...")

    result = model.transcribe(
        audio_path,
        language=language,
        verbose=False
    )

    text = result.get("text", "")
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })

    if log_callback:
        log_callback(f"[Whisper] 转写完成")

    return text, segments
