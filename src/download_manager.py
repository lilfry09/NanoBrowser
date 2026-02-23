import json
import os
import datetime

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_FILE = os.path.join(_PROJECT_ROOT, "downloads.json")

# 默认下载目录
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


class DownloadManager:
    """管理下载历史记录的持久化存储"""

    @staticmethod
    def load_downloads():
        """加载下载历史记录"""
        if not os.path.exists(DOWNLOADS_FILE):
            return []
        try:
            with open(DOWNLOADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def add_download(url, file_path, file_size=0, status="completed"):
        """添加一条下载记录"""
        downloads = DownloadManager.load_downloads()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
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
        except IOError as e:
            print("Download record save error:", e)
            return False

    @staticmethod
    def clear_downloads():
        """清除所有下载记录"""
        try:
            with open(DOWNLOADS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except IOError as e:
            print("Download history clear error:", e)
            return False

    @staticmethod
    def format_file_size(size_bytes):
        """将字节数转换为可读的文件大小字符串"""
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
    def format_speed(bytes_per_second):
        """将每秒字节数转换为可读的速度字符串"""
        if bytes_per_second <= 0:
            return "0 B/s"
        return DownloadManager.format_file_size(bytes_per_second) + "/s"

    @staticmethod
    def format_remaining_time(seconds):
        """将剩余秒数转换为可读的时间字符串"""
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
