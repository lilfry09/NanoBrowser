import json
import os

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = os.path.join(_PROJECT_ROOT, "session.json")


class SessionManager:
    """
    会话管理器 - 保存和恢复浏览器标签页状态。

    session.json 格式:
    {
        "tabs": [
            {"url": "https://...", "title": "Page Title"},
            ...
        ],
        "active_tab": 0
    }
    """

    @staticmethod
    def save_session(tabs_data, active_index=0):
        """
        保存当前会话。
        tabs_data: [{"url": str, "title": str}, ...]
        active_index: 当前激活的标签页索引
        """
        session = {
            "tabs": tabs_data,
            "active_tab": active_index,
        }
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print("Session save error:", e)
            return False

    @staticmethod
    def load_session():
        """
        加载上次保存的会话。
        返回 (tabs_data, active_index) 或 ([], 0)。
        """
        if not os.path.exists(SESSION_FILE):
            return [], 0
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session = json.load(f)
            tabs = session.get("tabs", [])
            active = session.get("active_tab", 0)
            return tabs, active
        except (json.JSONDecodeError, IOError):
            return [], 0

    @staticmethod
    def has_session():
        """检查是否存在已保存的会话"""
        if not os.path.exists(SESSION_FILE):
            return False
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session = json.load(f)
            return bool(session.get("tabs"))
        except (json.JSONDecodeError, IOError):
            return False

    @staticmethod
    def clear_session():
        """清除保存的会话"""
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            return True
        except IOError:
            return False
