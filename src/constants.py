"""常量定义模块 - 集中管理浏览器应用中使用的常量"""

# 项目根目录
import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 文件路径常量
SETTINGS_FILE = os.path.join(_PROJECT_ROOT, "settings.json")
HISTORY_FILE = os.path.join(_PROJECT_ROOT, "history.json")
BOOKMARKS_FILE = os.path.join(_PROJECT_ROOT, "bookmarks.json")
SESSION_FILE = os.path.join(_PROJECT_ROOT, "session.json")
DOWNLOADS_FILE = os.path.join(_PROJECT_ROOT, "downloads.json")
PASSWORDS_FILE = os.path.join(_PROJECT_ROOT, "passwords.json")
FEEDS_FILE = os.path.join(_PROJECT_ROOT, "feeds.json")
CUSTOM_THEMES_FILE = os.path.join(_PROJECT_ROOT, "custom_themes.json")

# 搜索引擎 URL 模板
SEARCH_ENGINES = {
    "Bing": "https://www.bing.com/search?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Baidu": "https://www.baidu.com/s?wd={}",
}

# 默认设置
DEFAULT_SETTINGS = {
    "search_engine": "Bing",
    "home_page": "https://www.bing.com",
    "restore_session": True,
    "theme": "Dark (Default)",
    "user_agent": "Chrome (Windows)",
}

# 用户代理选项
USER_AGENTS = {
    "Chrome (Windows)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Chrome (Mac)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Firefox (Windows)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Firefox (Mac)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Safari (Mac)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Edge (Windows)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "iPhone": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Android": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
}

# 缩放比例限制
MIN_ZOOM = 0.25
MAX_ZOOM = 5.0
DEFAULT_ZOOM = 1.0

# 主题列表
BUILTIN_THEMES = [
    "Dark (Default)",
    "Light",
    "High Contrast",
]

# 快捷键常量
SHORTCUTS = {
    "new_tab": "Ctrl+T",
    "close_tab": "Ctrl+W",
    "next_tab": "Ctrl+Tab",
    "prev_tab": "Ctrl+Shift+Tab",
    "focus_address_bar": "Ctrl+L",
    "reload": "Ctrl+R",
    "stop_loading": "Esc",
    "bookmark": "Ctrl+D",
    "history": "Ctrl+H",
    "find": "Ctrl+F",
    "zoom_in": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "zoom_reset": "Ctrl+0",
    "view_source": "Ctrl+U",
    "print": "Ctrl+P",
    "new_incognito": "Ctrl+Shift+N",
    "dev_tools": "F12",
    "fullscreen": "F11",
}
