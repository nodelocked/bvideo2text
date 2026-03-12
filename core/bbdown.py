"""
BBDown 调用封装模块
负责调用 BBDown.exe 下载字幕和音频
"""

import subprocess
import os
import sys
import re
import glob
import json
from pathlib import Path
from typing import Optional, Callable


def get_bbdown_path() -> str:
    """获取 BBDown.exe 的路径"""
    # 打包后的路径
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    bbdown_path = os.path.join(base_dir, "BBDown.exe")
    if not os.path.exists(bbdown_path):
        # 也尝试在当前工作目录找
        bbdown_path = os.path.join(os.getcwd(), "BBDown.exe")
    return bbdown_path


def run_bbdown(args: list, work_dir: str, log_callback: Optional[Callable] = None) -> subprocess.CompletedProcess:
    """
    运行 BBDown 命令
    
    Args:
        args: BBDown 参数列表
        work_dir: 工作目录
        log_callback: 日志回调函数
    """
    bbdown_path = get_bbdown_path()
    if not os.path.exists(bbdown_path):
        raise FileNotFoundError(f"BBDown.exe 未找到: {bbdown_path}")

    cmd = [bbdown_path] + args + ["--work-dir", work_dir]
    
    if log_callback:
        log_callback(f"[BBDown] 执行命令: {' '.join(cmd)}")

    # 使用 Popen 实时读取输出
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=work_dir
    )

    output_lines = []
    for line in process.stdout:
        line = line.rstrip('\n\r')
        if line:
            output_lines.append(line)
            if log_callback:
                log_callback(f"[BBDown] {line}")

    process.wait()
    
    result = subprocess.CompletedProcess(
        args=cmd,
        returncode=process.returncode,
        stdout='\n'.join(output_lines),
        stderr=''
    )
    return result


def extract_video_title(url: str, work_dir: str, log_callback: Optional[Callable] = None) -> str:
    """
    通过 BBDown --only-show-info 获取视频标题
    """
    try:
        result = run_bbdown([url, "--only-show-info"], work_dir, log_callback)
        # 尝试从输出中提取标题
        for line in result.stdout.split('\n'):
            if '标题' in line or 'Title' in line:
                # 尝试提取冒号后面的内容
                parts = line.split(':', 1) if ':' in line else line.split('：', 1)
                if len(parts) > 1:
                    return parts[1].strip()
    except Exception as e:
        if log_callback:
            log_callback(f"[警告] 获取视频标题失败: {e}")
    
    # 从 URL 中提取 BV 号作为备用标题
    bv_match = re.search(r'(BV\w+)', url, re.IGNORECASE)
    if bv_match:
        return bv_match.group(1)
    return "bilibili_video"


def download_subtitles(url: str, work_dir: str, log_callback: Optional[Callable] = None) -> list:
    """
    下载字幕文件
    
    Returns:
        字幕文件路径列表（空列表表示未找到字幕）
    """
    if log_callback:
        log_callback("[信息] 正在尝试下载字幕...")

    try:
        # 尝试仅下载字幕，不跳过AI字幕
        run_bbdown([url, "--sub-only"], work_dir, log_callback)
    except Exception as e:
        if log_callback:
            log_callback(f"[警告] 下载字幕时出错: {e}")
        return []

    # 查找下载到的字幕文件
    subtitle_files = []
    for ext in ['*.srt', '*.ass', '*.json', '*.lrc']:
        subtitle_files.extend(glob.glob(os.path.join(work_dir, '**', ext), recursive=True))
    
    if subtitle_files and log_callback:
        log_callback(f"[信息] 找到 {len(subtitle_files)} 个字幕文件")
    elif log_callback:
        log_callback("[信息] 未找到字幕文件")

    return subtitle_files


def download_audio(url: str, work_dir: str, log_callback: Optional[Callable] = None) -> Optional[str]:
    """
    下载音频文件
    
    Returns:
        音频文件路径，失败返回 None
    """
    if log_callback:
        log_callback("[信息] 正在下载音频...")

    try:
        run_bbdown([url, "--audio-only"], work_dir, log_callback)
    except Exception as e:
        if log_callback:
            log_callback(f"[错误] 下载音频失败: {e}")
        return None

    # 查找下载到的音频文件
    audio_files = []
    for ext in ['*.m4a', '*.mp3', '*.aac', '*.flac', '*.wav', '*.ogg', '*.wma']:
        audio_files.extend(glob.glob(os.path.join(work_dir, '**', ext), recursive=True))

    if audio_files:
        # 返回最新的音频文件
        audio_files.sort(key=os.path.getmtime, reverse=True)
        if log_callback:
            log_callback(f"[信息] 音频下载完成: {os.path.basename(audio_files[0])}")
        return audio_files[0]
    
    if log_callback:
        log_callback("[错误] 未找到下载的音频文件")
    return None
