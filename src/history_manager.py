import json
import os
import datetime

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(_PROJECT_ROOT, "history.json")

class HistoryManager:
    @staticmethod
    def load_history():
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def add_history(url, title):
        history = HistoryManager.load_history()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {"time": now, "url": url, "title": title}
        
        # 避免连续相同记录
        if history and history[-1]["url"] == url:
            return
            
        history.append(record)
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print("History save error:", e)

    @staticmethod
    def clear_history():
        """清除所有历史记录"""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except IOError as e:
            print("History clear error:", e)
            return False
