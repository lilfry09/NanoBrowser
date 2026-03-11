"""History Manager Module - Manages browser history records."""

import datetime
import json
import os

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(_PROJECT_ROOT, "history.json")

# Type aliases
HistoryRecord = dict[str, str]


class HistoryManager:
    """Manages browser history records with persistence."""

    @staticmethod
    def load_history() -> list[HistoryRecord]:
        """Load history records from file."""
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

    @staticmethod
    def add_history(url: str, title: str) -> None:
        """Add a history record."""
        history = HistoryManager.load_history()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record: HistoryRecord = {"time": now, "url": url, "title": title}

        # 避免连续相同记录
        if history and history[-1]["url"] == url:
            return

        history.append(record)
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print("History save error:", e)

    @staticmethod
    def clear_history() -> bool:
        """Clear all history records."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except OSError as e:
            print("History clear error:", e)
            return False
