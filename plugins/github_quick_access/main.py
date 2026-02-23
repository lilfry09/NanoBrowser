"""
GitHub Quick Access Extension for NanoBrowser

提供 GitHub 相关的快捷功能：
- 工具栏按钮快速打开 GitHub
- 右键菜单中添加 GitHub 搜索选项
- 页面加载时检测 GitHub 仓库页面
"""

import sys
import os

# 添加 src 目录到路径以便导入 BaseExtension
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from extension_manager import BaseExtension


class GitHubQuickAccess(BaseExtension):
    """GitHub 快捷访问扩展"""

    GITHUB_LINKS = {
        "GitHub Home": "https://github.com",
        "Trending": "https://github.com/trending",
        "Explore": "https://github.com/explore",
        "Your Repos": "https://github.com/dashboard",
        "Gists": "https://gist.github.com",
        "GitHub Status": "https://www.githubstatus.com",
    }

    def on_load(self):
        """扩展加载时初始化"""
        print(f"[{self.name}] Extension loaded!")

    def on_unload(self):
        """扩展卸载时清理"""
        print(f"[{self.name}] Extension unloaded.")

    def on_page_loaded(self, url: str, title: str):
        """页面加载完成回调"""
        if "github.com" in url.lower():
            self.show_status_message(f"GitHub page detected: {title}", 2000)

    def get_toolbar_actions(self) -> list:
        """在工具栏添加 GitHub 按钮"""
        return [
            {
                "label": "GitHub",
                "tooltip": "Open GitHub",
                "callback": lambda: self.open_url("https://github.com"),
            },
        ]

    def get_context_menu_items(self, url: str) -> list:
        """在右键菜单添加 GitHub 相关选项"""
        items = []
        # GitHub 快捷链接子菜单
        for label, link in self.GITHUB_LINKS.items():
            items.append(
                {
                    "label": f"GitHub: {label}",
                    "callback": lambda u=link: self.open_url(u),
                }
            )

        # 如果在 GitHub 页面，添加额外选项
        if "github.com" in url.lower():
            items.append(
                {
                    "label": "GitHub: View Raw",
                    "callback": lambda: self._view_raw(),
                }
            )

        return items

    def _view_raw(self):
        """尝试将 GitHub 文件 URL 转换为 raw 链接"""
        url = self.get_current_url()
        if "/blob/" in url:
            raw_url = url.replace("github.com", "raw.githubusercontent.com").replace(
                "/blob/", "/"
            )
            self.open_url(raw_url)
        else:
            self.show_status_message("Not a GitHub file page.", 2000)
