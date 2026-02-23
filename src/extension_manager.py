"""
NanoBrowser Extension System

扩展系统 API 和加载器。

## 扩展目录结构:
plugins/
  my_extension/
    manifest.json     # 扩展清单
    main.py           # 扩展入口

## manifest.json 格式:
{
    "name": "My Extension",
    "version": "1.0.0",
    "description": "A sample extension",
    "author": "Author Name",
    "entry": "main.py",
    "permissions": ["context_menu", "toolbar", "page_load"],
    "enabled": true
}

## 扩展入口 (main.py) 需要定义一个继承 BaseExtension 的类:
class MyExtension(BaseExtension):
    def on_load(self):
        ...
    def on_page_loaded(self, url, title):
        ...
    def get_context_menu_items(self, url):
        return [{"label": "...", "callback": self.my_action}]
    def get_toolbar_actions(self):
        return [{"label": "...", "tooltip": "...", "callback": self.my_action}]
"""

import json
import os
import importlib.util
import traceback

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(_PROJECT_ROOT, "plugins")
EXTENSIONS_STATE_FILE = os.path.join(_PROJECT_ROOT, "extensions_state.json")


class BaseExtension:
    """扩展基类，所有扩展必须继承此类"""

    def __init__(self, manifest: dict, plugin_dir: str):
        self.manifest = manifest
        self.plugin_dir = plugin_dir
        self.name = manifest.get("name", "Unknown")
        self.version = manifest.get("version", "0.0.0")
        self.description = manifest.get("description", "")
        self.author = manifest.get("author", "")
        self._main_window = None

    def set_main_window(self, main_window):
        """由扩展管理器调用，注入主窗口引用"""
        self._main_window = main_window

    def on_load(self):
        """扩展加载时调用（初始化）"""
        pass

    def on_unload(self):
        """扩展卸载时调用（清理）"""
        pass

    def on_page_loaded(self, url: str, title: str):
        """
        页面加载完成时调用。
        url: 当前页面 URL
        title: 当前页面标题
        """
        pass

    def get_context_menu_items(self, url: str) -> list:
        """
        获取右键菜单项。
        返回 [{"label": "Menu Text", "callback": callable}, ...]
        """
        return []

    def get_toolbar_actions(self) -> list:
        """
        获取工具栏按钮。
        返回 [{"label": "Button Text", "tooltip": "...", "callback": callable}, ...]
        """
        return []

    # ---- 便捷 API ----

    def open_url(self, url: str):
        """在浏览器中打开指定 URL（新标签页）"""
        if self._main_window:
            from PyQt6.QtCore import QUrl

            self._main_window.add_new_tab(QUrl(url), "Loading...")

    def get_current_url(self) -> str:
        """获取当前标签页的 URL"""
        if self._main_window:
            browser = self._main_window.current_browser()
            if browser:
                return browser.url().toString()
        return ""

    def get_current_title(self) -> str:
        """获取当前标签页的标题"""
        if self._main_window:
            browser = self._main_window.current_browser()
            if browser:
                return browser.title()
        return ""

    def show_status_message(self, message: str, timeout_ms: int = 3000):
        """在状态栏显示消息"""
        if self._main_window:
            self._main_window.statusBar().showMessage(message, timeout_ms)

    def run_javascript(self, js_code: str):
        """在当前页面执行 JavaScript"""
        if self._main_window:
            browser = self._main_window.current_browser()
            if browser:
                browser.page().runJavaScript(js_code)


class ExtensionManager:
    """扩展管理器：加载、卸载、管理扩展"""

    def __init__(self):
        self._extensions = {}  # {extension_name: BaseExtension instance}
        self._manifests = {}  # {extension_name: manifest dict}
        self._main_window = None

    def set_main_window(self, main_window):
        """注入主窗口引用"""
        self._main_window = main_window
        for ext in self._extensions.values():
            ext.set_main_window(main_window)

    def discover_extensions(self) -> list:
        """扫描 plugins/ 目录，发现所有扩展"""
        if not os.path.isdir(PLUGINS_DIR):
            os.makedirs(PLUGINS_DIR, exist_ok=True)
            return []

        manifests = []
        for entry in os.listdir(PLUGINS_DIR):
            ext_dir = os.path.join(PLUGINS_DIR, entry)
            if not os.path.isdir(ext_dir):
                continue
            manifest_path = os.path.join(ext_dir, "manifest.json")
            if not os.path.isfile(manifest_path):
                continue
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                manifest["_dir"] = ext_dir
                manifest["_dirname"] = entry
                manifests.append(manifest)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading manifest for {entry}: {e}")

        return manifests

    def load_extension(self, manifest: dict) -> bool:
        """加载单个扩展"""
        name = manifest.get("name", "Unknown")
        ext_dir = manifest.get("_dir", "")
        entry_file = manifest.get("entry", "main.py")
        entry_path = os.path.join(ext_dir, entry_file)

        if not os.path.isfile(entry_path):
            print(f"Extension entry not found: {entry_path}")
            return False

        try:
            # 动态加载 Python 模块
            spec = importlib.util.spec_from_file_location(
                f"nanobrowser_ext_{manifest.get('_dirname', name)}", entry_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找继承 BaseExtension 的类
            ext_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseExtension)
                    and attr is not BaseExtension
                ):
                    ext_class = attr
                    break

            if ext_class is None:
                print(f"No BaseExtension subclass found in {entry_path}")
                return False

            # 实例化扩展
            instance = ext_class(manifest, ext_dir)
            if self._main_window:
                instance.set_main_window(self._main_window)
            instance.on_load()

            self._extensions[name] = instance
            self._manifests[name] = manifest
            print(f"Extension loaded: {name} v{manifest.get('version', '?')}")
            return True

        except Exception as e:
            print(f"Error loading extension {name}: {e}")
            traceback.print_exc()
            return False

    def unload_extension(self, name: str):
        """卸载单个扩展"""
        if name in self._extensions:
            try:
                self._extensions[name].on_unload()
            except Exception as e:
                print(f"Error unloading extension {name}: {e}")
            del self._extensions[name]
            if name in self._manifests:
                del self._manifests[name]

    def load_all_enabled(self):
        """加载所有启用的扩展"""
        state = self._load_state()
        manifests = self.discover_extensions()
        for manifest in manifests:
            name = manifest.get("name", "Unknown")
            # 检查是否在状态文件中被禁用
            if name in state and not state[name].get("enabled", True):
                continue
            # 检查 manifest 中的 enabled 字段
            if not manifest.get("enabled", True):
                continue
            self.load_extension(manifest)

    def get_loaded_extensions(self) -> dict:
        """获取已加载的扩展"""
        return self._extensions.copy()

    def get_all_manifests(self) -> list:
        """获取所有发现的扩展清单"""
        return self.discover_extensions()

    # ---- 扩展点回调 ----

    def on_page_loaded(self, url: str, title: str):
        """通知所有扩展页面已加载"""
        for ext in self._extensions.values():
            try:
                ext.on_page_loaded(url, title)
            except Exception as e:
                print(f"Extension error ({ext.name}) on_page_loaded: {e}")

    def get_all_context_menu_items(self, url: str) -> list:
        """收集所有扩展的右键菜单项"""
        items = []
        for ext in self._extensions.values():
            try:
                ext_items = ext.get_context_menu_items(url)
                for item in ext_items:
                    item["_extension"] = ext.name
                items.extend(ext_items)
            except Exception as e:
                print(f"Extension error ({ext.name}) get_context_menu_items: {e}")
        return items

    def get_all_toolbar_actions(self) -> list:
        """收集所有扩展的工具栏按钮"""
        actions = []
        for ext in self._extensions.values():
            try:
                ext_actions = ext.get_toolbar_actions()
                for action in ext_actions:
                    action["_extension"] = ext.name
                actions.extend(ext_actions)
            except Exception as e:
                print(f"Extension error ({ext.name}) get_toolbar_actions: {e}")
        return actions

    # ---- 扩展状态持久化 ----

    def _load_state(self) -> dict:
        """加载扩展启用/禁用状态"""
        if not os.path.exists(EXTENSIONS_STATE_FILE):
            return {}
        try:
            with open(EXTENSIONS_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_state(self, state: dict):
        """保存扩展状态"""
        try:
            with open(EXTENSIONS_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Extension state save error: {e}")

    def set_extension_enabled(self, name: str, enabled: bool):
        """设置扩展启用/禁用状态"""
        state = self._load_state()
        state[name] = {"enabled": enabled}
        self._save_state(state)
        if enabled and name not in self._extensions:
            # 尝试加载
            for m in self.discover_extensions():
                if m.get("name") == name:
                    self.load_extension(m)
                    break
        elif not enabled and name in self._extensions:
            self.unload_extension(name)

    def is_extension_enabled(self, name: str) -> bool:
        """检查扩展是否启用"""
        state = self._load_state()
        if name in state:
            return state[name].get("enabled", True)
        return True  # 默认启用
