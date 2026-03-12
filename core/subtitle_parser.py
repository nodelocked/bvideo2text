"""
字幕文件解析模块
支持 SRT、ASS、JSON（B站格式）字幕文件解析为纯文本
"""

import re
import json
import os
from typing import Optional


def parse_srt(filepath: str) -> str:
    """
    解析 SRT 字幕文件为纯文本
    
    SRT 格式:
    1
    00:00:01,000 --> 00:00:03,000
    字幕内容
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # 去除序号行和时间戳行
    lines = content.strip().split('\n')
    text_lines = []
    skip_next = False
    
    for line in lines:
        line = line.strip()
        # 跳过空行
        if not line:
            skip_next = False
            continue
        # 跳过纯数字行（序号）
        if line.isdigit():
            continue
        # 跳过时间戳行
        if re.match(r'\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}', line):
            continue
        # 去除 HTML 标签
        line = re.sub(r'<[^>]+>', '', line)
        if line:
            text_lines.append(line)

    # 去除连续重复行
    deduplicated = []
    for line in text_lines:
        if not deduplicated or line != deduplicated[-1]:
            deduplicated.append(line)

    return '\n'.join(deduplicated)


def parse_ass(filepath: str) -> str:
    """
    解析 ASS/SSA 字幕文件为纯文本
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    lines = content.split('\n')
    text_lines = []
    in_events = False

    for line in lines:
        line = line.strip()
        if line.startswith('[Events]'):
            in_events = True
            continue
        if line.startswith('[') and in_events:
            break
        if in_events and line.startswith('Dialogue:'):
            # Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,字幕内容
            parts = line.split(',', 9)
            if len(parts) >= 10:
                text = parts[9]
                # 去除 ASS 样式标签
                text = re.sub(r'\{[^}]*\}', '', text)
                # 替换 \N 为换行
                text = text.replace('\\N', '\n').replace('\\n', '\n')
                text = text.strip()
                if text:
                    text_lines.append(text)

    # 去除连续重复行
    deduplicated = []
    for line in text_lines:
        if not deduplicated or line != deduplicated[-1]:
            deduplicated.append(line)

    return '\n'.join(deduplicated)


def parse_bilibili_json(filepath: str) -> str:
    """
    解析 B站 JSON 字幕文件为纯文本
    
    B站字幕 JSON 格式:
    {
        "body": [
            {"from": 0.0, "to": 2.0, "content": "字幕内容"},
            ...
        ]
    }
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        data = json.load(f)

    text_lines = []
    
    # B站字幕格式
    if isinstance(data, dict) and 'body' in data:
        for item in data['body']:
            content = item.get('content', '').strip()
            if content:
                text_lines.append(content)
    # 也可能是列表格式
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                content = item.get('content', item.get('text', '')).strip()
                if content:
                    text_lines.append(content)

    # 去除连续重复行
    deduplicated = []
    for line in text_lines:
        if not deduplicated or line != deduplicated[-1]:
            deduplicated.append(line)

    return '\n'.join(deduplicated)


def parse_subtitle_file(filepath: str) -> Optional[str]:
    """
    自动检测并解析字幕文件
    
    Returns:
        解析后的纯文本，或 None（如果格式不支持）
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.srt':
            return parse_srt(filepath)
        elif ext in ('.ass', '.ssa'):
            return parse_ass(filepath)
        elif ext == '.json':
            return parse_bilibili_json(filepath)
        elif ext == '.lrc':
            return parse_lrc(filepath)
        else:
            # 尝试直接读取文本
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
    except Exception as e:
        print(f"解析字幕文件失败 ({filepath}): {e}")
        return None


def parse_lrc(filepath: str) -> str:
    """
    解析 LRC 歌词格式文件
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    lines = content.strip().split('\n')
    text_lines = []
    
    for line in lines:
        # 去除时间标签 [mm:ss.xx]
        text = re.sub(r'\[\d{2}:\d{2}[\.:]\d{2,3}\]', '', line).strip()
        # 跳过元数据标签
        if text.startswith('[') and text.endswith(']'):
            continue
        if text:
            text_lines.append(text)

    deduplicated = []
    for line in text_lines:
        if not deduplicated or line != deduplicated[-1]:
            deduplicated.append(line)

    return '\n'.join(deduplicated)
