"""工具函数模块 - 集中管理通用工具函数"""

import json
import os
import re
from datetime import datetime
from typing import Any, Optional


def load_json_file(file_path: str, default: Any = None) -> Any:
    """
    读取 JSON 文件。

    Args:
        file_path: 文件路径
        default: 默认返回值（如果文件不存在或解析失败）

    Returns:
        解析后的 JSON 数据，或 default
    """
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def save_json_file(file_path: str, data: Any) -> bool:
    """
    保存数据到 JSON 文件。

    Args:
        file_path: 文件路径
        data: 要保存的数据

    Returns:
        是否保存成功
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def is_valid_url(url: str) -> bool:
    """
    检查字符串是否是有效的 URL。

    Args:
        url: 要检查的字符串

    Returns:
        是否是有效的 URL
    """
    if not url:
        return False
    # 检查是否以 http:// 或 https:// 开头
    if re.match(r"^[a-zA-Z]+://", url):
        return True
    # 检查是否像域名（有句点且没有空格）
    return "." in url and " " not in url


def add_url_scheme(url: str, default_scheme: str = "https://") -> str:
    """
    为 URL 添加协议前缀。

    Args:
        url: 原始 URL
        default_scheme: 默认协议（默认 https://）

    Returns:
        带有协议前缀的 URL
    """
    if re.match(r"^[a-zA-Z]+://", url):
        return url
    return default_scheme + url


def format_timestamp(timestamp: Optional[float] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳。

    Args:
        timestamp: Unix 时间戳（默认当前时间）
        fmt: 格式字符串

    Returns:
        格式化后的时间字符串
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromtimestamp(timestamp)
    return dt.strftime(fmt)


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小。

    Args:
        size_bytes: 字节数

    Returns:
        格式化的文件大小字符串（如 "1.5 MB"）
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串。

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符。

    Args:
        filename: 原始文件名

    Returns:
        清理后的文件名
    """
    # 移除 Windows 文件名中的非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    return re.sub(illegal_chars, "_", filename)
