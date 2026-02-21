import json
import os
import datetime

HISTORY_FILE = "history.json"

class HistoryManager:
    @staticmethod
    def load_history():
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
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
        except Exception as e:
            print("History save error:", e)
