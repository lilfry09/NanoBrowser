"""Session Manager Module - Manages browser session persistence."""

import json
import os

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION_FILE = os.path.join(_PROJECT_ROOT, "session.json")

# Type aliases
TabData = dict[str, str]
SessionData = dict[str, list[TabData] | int]


class SessionManager:
    """
    Session Manager - Saves and restores browser tab state.

    session.json format:
    {
        "tabs": [
            {"url": "https://...", "title": "Page Title"},
            ...
        ],
        "active_tab": 0
    }
    """

    @staticmethod
    def save_session(tabs_data: list[TabData], active_index: int = 0) -> bool:
        """
        Save current session.

        Args:
            tabs_data: List of tab data dictionaries with 'url' and 'title' keys
            active_index: Index of the currently active tab
        """
        session: SessionData = {
            "tabs": tabs_data,
            "active_tab": active_index,
        }
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print("Session save error:", e)
            return False

    @staticmethod
    def load_session() -> tuple[list[TabData], int]:
        """
        Load saved session.

        Returns:
            Tuple of (tabs_data, active_index) or ([], 0) if no session exists.
        """
        if not os.path.exists(SESSION_FILE):
            return [], 0
        try:
            with open(SESSION_FILE, encoding="utf-8") as f:
                session = json.load(f)
            tabs: list[TabData] = session.get("tabs", [])
            active: int = session.get("active_tab", 0)
            return tabs, active
        except (OSError, json.JSONDecodeError):
            return [], 0

    @staticmethod
    def has_session() -> bool:
        """Check if a saved session exists."""
        if not os.path.exists(SESSION_FILE):
            return False
        try:
            with open(SESSION_FILE, encoding="utf-8") as f:
                session = json.load(f)
            return bool(session.get("tabs"))
        except (OSError, json.JSONDecodeError):
            return False

    @staticmethod
    def clear_session() -> bool:
        """Clear saved session."""
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            return True
        except OSError:
            return False
