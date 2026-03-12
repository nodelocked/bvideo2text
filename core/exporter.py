"""
文本导出模块
将提取的文本内容导出为 .txt 文件
自动将繁体中文转换为简体中文
"""

import os
import re
from datetime import datetime
from typing import Optional


def _convert_to_simplified(text: str) -> str:
    """将繁体中文转换为简体中文"""
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')  # Traditional to Simplified
        return cc.convert(text)
    except ImportError:
        # opencc 未安装时不转换
        return text
    except Exception:
        return text


def sanitize_filename(name: str) -> str:
    """清理文件名，去除不合法字符"""
    # 替换 Windows 不允许的文件名字符
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 去除首尾空格和点
    name = name.strip(' .')
    # 限制长度
    if len(name) > 200:
        name = name[:200]
    return name or "untitled"


def export_text(
    text: str,
    video_title: str,
    video_url: str,
    output_dir: str,
    source_type: str = "字幕",
    log_callback: Optional[callable] = None
) -> str:
    """
    导出文本到文件
    
    Args:
        text: 要导出的文本内容
        video_title: 视频标题
        video_url: 视频链接
        output_dir: 输出目录
        source_type: 来源类型（"字幕" 或 "语音转写"）
        log_callback: 日志回调
    
    Returns:
        导出的文件路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 繁体转简体
    text = _convert_to_simplified(text)
    video_title = _convert_to_simplified(video_title)
    
    if log_callback:
        log_callback("[信息] 已将繁体中文转换为简体中文")

    # 提取视频 ID (BV号、av号等)
    video_id = ""
    id_match = re.search(r'(BV\w+|bv\w+|av\d+|ep\d+|ss\d+)', video_url, re.IGNORECASE)
    if id_match:
        video_id = f"_{id_match.group(1)}"

    # 生成文件名，包含标题和视频ID
    safe_title = sanitize_filename(video_title)
    filename = f"{safe_title}{video_id}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # 如果文件已存在，加上时间戳
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_title}{video_id}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
    
    # 组织内容
    content_parts = [
        f"标题: {video_title}",
        f"链接: {video_url}",
        f"来源: {source_type}",
        f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "=" * 60,
        "",
        text
    ]
    
    content = '\n'.join(content_parts)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    if log_callback:
        log_callback(f"[导出] 文本已保存到: {filepath}")
        log_callback(f"[导出] 文件大小: {os.path.getsize(filepath)} 字节")
    
    return filepath
