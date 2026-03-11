"""Download Manager Module - Manages download history and file operations."""

import datetime
import json
import os

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_FILE = os.path.join(_PROJECT_ROOT, "downloads.json")

# 默认下载目录
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Type aliases
DownloadRecord = dict[str, str]
FileSize = int
Speed = float
TimeSeconds = float


class DownloadManager:
    """Manages download history records with persistence."""

    @staticmethod
    def load_downloads() -> list[DownloadRecord]:
        """Load download history records."""
        if not os.path.exists(DOWNLOADS_FILE):
            return []
        try:
            with open(DOWNLOADS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    @staticmethod
    def add_download(url: str, file_path: str, file_size: FileSize = 0, status: str = "completed") -> bool:
        """Add a download record."""
        downloads = DownloadManager.load_downloads()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record: DownloadRecord = {
            "time": now,
            "url": url,
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": file_size,
            "status": status,
        }
        downloads.append(record)
        try:
            with open(DOWNLOADS_FILE, "w", encoding="utf-8") as f:
                json.dump(downloads, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print("Download record save error:", e)
            return False

    @staticmethod
    def clear_downloads() -> bool:
        """Clear all download records."""
        try:
            with open(DOWNLOADS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except OSError as e:
            print("Download history clear error:", e)
            return False

    @staticmethod
    def format_file_size(size_bytes: FileSize) -> str:
        """Convert bytes to human-readable file size."""
        if size_bytes <= 0:
            return "Unknown"
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.1f} {units[unit_index]}"

    @staticmethod
    def format_speed(bytes_per_second: Speed) -> str:
        """Convert bytes per second to human-readable speed string."""
        if bytes_per_second <= 0:
            return "0 B/s"
        return DownloadManager.format_file_size(int(bytes_per_second)) + "/s"

    @staticmethod
    def format_remaining_time(seconds: TimeSeconds) -> str:
        """Convert remaining seconds to human-readable time string."""
        if seconds <= 0 or seconds == float("inf"):
            return "Unknown"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
