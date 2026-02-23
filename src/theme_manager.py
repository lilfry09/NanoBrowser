import json
import os

# 使用项目根目录（src 的上级目录）作为数据文件存储路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES_FILE = os.path.join(_PROJECT_ROOT, "custom_themes.json")

# 主题颜色配置键
# bg_primary: 主背景色
# bg_secondary: 工具栏/表头等次要背景
# bg_tertiary: 深层背景/输入框聚焦
# text_primary: 主要文字颜色
# text_secondary: 次要/高亮文字
# border: 边框颜色
# accent: 强调色（进度条、选中、按下等）
# accent_hover: 强调色悬停
# menu_selected: 菜单选中背景
# tab_hover: 标签悬停背景
# button_bg: 按钮背景
# button_hover: 按钮悬停
# selection_bg: 选择背景


BUILTIN_THEMES = {
    "Dark (Default)": {
        "bg_primary": "#2b2b2b",
        "bg_secondary": "#3c3f41",
        "bg_tertiary": "#1e1e1e",
        "text_primary": "#a9b7c6",
        "text_secondary": "#ffffff",
        "border": "#555555",
        "accent": "#3d6a99",
        "accent_hover": "#4b6eaf",
        "menu_selected": "#4b6eaf",
        "tab_hover": "#4c5052",
        "button_bg": "#4c5052",
        "button_hover": "#5c6062",
        "selection_bg": "#214283",
    },
    "Light": {
        "bg_primary": "#f5f5f5",
        "bg_secondary": "#e0e0e0",
        "bg_tertiary": "#ffffff",
        "text_primary": "#333333",
        "text_secondary": "#000000",
        "border": "#cccccc",
        "accent": "#1a73e8",
        "accent_hover": "#1565c0",
        "menu_selected": "#1a73e8",
        "tab_hover": "#d5d5d5",
        "button_bg": "#e8e8e8",
        "button_hover": "#d0d0d0",
        "selection_bg": "#b3d4fc",
    },
    "High Contrast": {
        "bg_primary": "#000000",
        "bg_secondary": "#1a1a1a",
        "bg_tertiary": "#000000",
        "text_primary": "#ffffff",
        "text_secondary": "#ffff00",
        "border": "#ffffff",
        "accent": "#00ff00",
        "accent_hover": "#00cc00",
        "menu_selected": "#0000ff",
        "tab_hover": "#333333",
        "button_bg": "#333333",
        "button_hover": "#555555",
        "selection_bg": "#0000ff",
    },
}

# 默认主题颜色模板（用于自定义主题的起始值）
DEFAULT_THEME_COLORS = BUILTIN_THEMES["Dark (Default)"].copy()


def generate_stylesheet(colors: dict) -> str:
    """根据颜色配置生成完整的 QSS 样式表"""
    c = colors
    return f"""
QMainWindow {{
    background-color: {c["bg_primary"]};
}}
QToolBar {{
    background: {c["bg_secondary"]};
    border-bottom: 1px solid {c["bg_tertiary"]};
    spacing: 5px;
    padding: 3px;
}}
QToolBar::separator {{
    background-color: {c["border"]};
    width: 1px;
    margin: 4px 5px;
}}
QLineEdit {{
    background-color: {c["bg_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 12px;
    padding: 3px 12px;
    color: {c["text_primary"]};
    font-size: 13px;
    selection-background-color: {c["selection_bg"]};
}}
QLineEdit:focus {{
    border: 1px solid {c["accent"]};
    background-color: {c["bg_tertiary"]};
}}
QTabWidget::pane {{
    border: none;
    background: {c["bg_primary"]};
}}
QTabBar::tab {{
    background: {c["bg_secondary"]};
    color: {c["text_primary"]};
    border: 1px solid {c["bg_tertiary"]};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 6px 12px;
    margin-right: -1px;
    max-width: 220px;
    min-width: 100px;
}}
QTabBar::tab:selected {{
    background: {c["bg_primary"]};
    color: {c["text_secondary"]};
}}
QTabBar::tab:hover:!selected {{
    background: {c["tab_hover"]};
}}
QTabBar::close-button {{
    image: url('');
}}
QMenu {{
    background-color: {c["bg_secondary"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
}}
QMenu::item:selected {{
    background-color: {c["menu_selected"]};
    color: {c["text_secondary"]};
}}
QProgressBar {{
    max-height: 2px;
    background: transparent;
    border: none;
}}
QProgressBar::chunk {{
    background-color: {c["accent"]};
}}
QDialog {{
    background-color: {c["bg_primary"]};
    color: {c["text_primary"]};
}}
QTableWidget {{
    background-color: {c["bg_primary"]};
    color: {c["text_primary"]};
    gridline-color: {c["bg_secondary"]};
    border: 1px solid {c["border"]};
}}
QHeaderView::section {{
    background-color: {c["bg_secondary"]};
    color: {c["text_primary"]};
    padding: 4px;
    border: 1px solid {c["bg_tertiary"]};
}}
QPushButton {{
    background-color: {c["button_bg"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 5px 15px;
}}
QPushButton:hover {{
    background-color: {c["button_hover"]};
}}
QPushButton:pressed {{
    background-color: {c["accent"]};
}}
QComboBox {{
    background-color: {c["bg_primary"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    padding: 2px 8px;
}}
QComboBox:hover {{
    border: 1px solid {c["accent"]};
}}
QComboBox::drop-down {{
    border: none;
}}
QLabel {{
    color: {c["text_primary"]};
}}
QListWidget {{
    background-color: {c["bg_primary"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
}}
QListWidget::item:selected {{
    background-color: {c["menu_selected"]};
    color: {c["text_secondary"]};
}}
QTreeWidget {{
    background-color: {c["bg_primary"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
}}
QTreeWidget::item:selected {{
    background-color: {c["menu_selected"]};
    color: {c["text_secondary"]};
}}
QTextEdit {{
    background-color: {c["bg_primary"]};
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
}}
QCheckBox {{
    color: {c["text_primary"]};
}}
QGroupBox {{
    color: {c["text_primary"]};
    border: 1px solid {c["border"]};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 4px;
}}
QScrollBar:vertical {{
    background: {c["bg_primary"]};
    width: 10px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {c["border"]};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c["accent"]};
}}
QScrollBar:horizontal {{
    background: {c["bg_primary"]};
    height: 10px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {c["border"]};
    border-radius: 5px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c["accent"]};
}}
QStatusBar {{
    background-color: {c["bg_secondary"]};
    color: {c["text_primary"]};
}}
"""


class ThemeManager:
    """主题管理器：管理内置和自定义主题"""

    @staticmethod
    def get_builtin_theme_names() -> list:
        """获取内置主题名称列表"""
        return list(BUILTIN_THEMES.keys())

    @staticmethod
    def get_theme_colors(theme_name: str) -> dict | None:
        """获取主题颜色配置（内置或自定义）"""
        if theme_name in BUILTIN_THEMES:
            return BUILTIN_THEMES[theme_name].copy()
        custom = ThemeManager.load_custom_themes()
        if theme_name in custom:
            return custom[theme_name].copy()
        return None

    @staticmethod
    def get_stylesheet(theme_name: str) -> str:
        """获取主题对应的 QSS 样式表"""
        colors = ThemeManager.get_theme_colors(theme_name)
        if colors is None:
            colors = BUILTIN_THEMES["Dark (Default)"]
        return generate_stylesheet(colors)

    @staticmethod
    def get_all_theme_names() -> list:
        """获取所有主题名称（内置 + 自定义）"""
        names = list(BUILTIN_THEMES.keys())
        custom = ThemeManager.load_custom_themes()
        names.extend(custom.keys())
        return names

    @staticmethod
    def load_custom_themes() -> dict:
        """加载自定义主题配置"""
        if not os.path.exists(THEMES_FILE):
            return {}
        try:
            with open(THEMES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @staticmethod
    def save_custom_themes(themes: dict):
        """保存自定义主题配置"""
        try:
            with open(THEMES_FILE, "w", encoding="utf-8") as f:
                json.dump(themes, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print("Theme save error:", e)

    @staticmethod
    def save_custom_theme(name: str, colors: dict):
        """保存/更新一个自定义主题"""
        themes = ThemeManager.load_custom_themes()
        themes[name] = colors
        ThemeManager.save_custom_themes(themes)

    @staticmethod
    def delete_custom_theme(name: str):
        """删除一个自定义主题"""
        themes = ThemeManager.load_custom_themes()
        if name in themes:
            del themes[name]
            ThemeManager.save_custom_themes(themes)

    @staticmethod
    def export_theme(name: str) -> str:
        """导出主题为 JSON 字符串"""
        colors = ThemeManager.get_theme_colors(name)
        if colors is None:
            return ""
        data = {"name": name, "colors": colors}
        return json.dumps(data, ensure_ascii=False, indent=2)

    @staticmethod
    def import_theme(json_str: str) -> tuple:
        """
        从 JSON 字符串导入主题。
        返回 (theme_name, colors) 或 (None, None) 如果格式错误。
        """
        try:
            data = json.loads(json_str)
            name = data.get("name", "")
            colors = data.get("colors", {})
            if not name or not isinstance(colors, dict):
                return None, None
            # 验证必要的键
            required_keys = set(DEFAULT_THEME_COLORS.keys())
            if not required_keys.issubset(set(colors.keys())):
                return None, None
            return name, colors
        except (json.JSONDecodeError, KeyError, TypeError):
            return None, None

    @staticmethod
    def get_color_labels() -> dict:
        """获取颜色键的可读名称"""
        return {
            "bg_primary": "Primary Background",
            "bg_secondary": "Secondary Background",
            "bg_tertiary": "Tertiary Background",
            "text_primary": "Primary Text",
            "text_secondary": "Secondary Text",
            "border": "Border",
            "accent": "Accent",
            "accent_hover": "Accent Hover",
            "menu_selected": "Menu Selected",
            "tab_hover": "Tab Hover",
            "button_bg": "Button Background",
            "button_hover": "Button Hover",
            "selection_bg": "Selection Background",
        }
