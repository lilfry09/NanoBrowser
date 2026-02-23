import sys
import os
import re
import json

# 修复在不同目录下执行导致找不到同级模块的问题
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time as _time

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QTabWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QMenu,
    QProgressBar,
    QStyle,
    QComboBox,
    QHeaderView,
    QPushButton,
    QLabel,
    QFileDialog,
    QStatusBar,
)
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile

from history_manager import HistoryManager
from bookmark_manager import BookmarkManager
from download_manager import DownloadManager

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(_PROJECT_ROOT, "settings.json")

# 现代化深色主题风格
STYLE_SHEET = """
QMainWindow {
    background-color: #2b2b2b;
}
QToolBar {
    background: #3c3f41;
    border-bottom: 1px solid #1e1e1e;
    spacing: 5px;
    padding: 3px;
}
QToolBar::separator {
    background-color: #555555;
    width: 1px;
    margin: 4px 5px;
}
QLineEdit {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    border-radius: 12px;
    padding: 3px 12px;
    color: #a9b7c6;
    font-size: 13px;
    selection-background-color: #214283;
}
QLineEdit:focus {
    border: 1px solid #3d6a99;
    background-color: #1e1e1e;
}
QTabWidget::pane {
    border: none;
    background: #2b2b2b;
}
QTabBar::tab {
    background: #3c3f41;
    color: #a9b7c6;
    border: 1px solid #1e1e1e;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 6px 12px;
    margin-right: -1px;
    max-width: 220px;
    min-width: 100px;
}
QTabBar::tab:selected {
    background: #2b2b2b;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background: #4c5052;
}
QTabBar::close-button {
    image: url(''); /* Optionally override close icon here */
}
QMenu {
    background-color: #3c3f41;
    color: #a9b7c6;
    border: 1px solid #555555;
}
QMenu::item:selected {
    background-color: #4b6eaf;
    color: #ffffff;
}
QProgressBar {
    max-height: 2px;
    background: transparent;
    border: none;
}
QProgressBar::chunk {
    background-color: #3d6a99;
}
QDialog {
    background-color: #2b2b2b;
    color: #a9b7c6;
}
QTableWidget {
    background-color: #2b2b2b;
    color: #a9b7c6;
    gridline-color: #3c3f41;
    border: 1px solid #555555;
}
QHeaderView::section {
    background-color: #3c3f41;
    color: #a9b7c6;
    padding: 4px;
    border: 1px solid #1e1e1e;
}
QPushButton {
    background-color: #4c5052;
    color: #a9b7c6;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 15px;
}
QPushButton:hover {
    background-color: #5c6062;
}
QPushButton:pressed {
    background-color: #3d6a99;
}
QComboBox {
    background-color: #2b2b2b;
    color: #a9b7c6;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 2px 8px;
}
QComboBox:hover {
    border: 1px solid #3d6a99;
}
QComboBox::drop-down {
    border: none;
}
QLabel {
    color: #a9b7c6;
}
"""

SEARCH_ENGINES = {
    "Bing": "https://www.bing.com/search?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Baidu": "https://www.baidu.com/s?wd={}",
}


class WebEngineView(QWebEngineView):
    """
    自定义 WebEngineView，重写 createWindow 方法。
    """

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window

    def createWindow(self, window_type):
        new_view = self._main_window.add_new_tab(QUrl("about:blank"), "Loading...")
        return new_view


class SettingsManager:
    @staticmethod
    def load_settings():
        if not os.path.exists(SETTINGS_FILE):
            return {"search_engine": "Bing"}
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"search_engine": "Bing"}

    @staticmethod
    def save_settings(settings):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False


class DownloadProgressDialog(QDialog):
    """下载进度对话框，显示当前所有正在下载的文件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.resize(550, 400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.layout_main = QVBoxLayout(self)

        self.header_label = QLabel("Active Downloads")
        self.header_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin-bottom: 5px;"
        )
        self.layout_main.addWidget(self.header_label)

        # 下载项容器
        self.downloads_layout = QVBoxLayout()
        self.layout_main.addLayout(self.downloads_layout)
        self.layout_main.addStretch()

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        history_btn = QPushButton("View Download History")
        history_btn.clicked.connect(self.show_download_history)
        btn_layout.addWidget(history_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        self.layout_main.addLayout(btn_layout)

        # 下载条目字典 {download_item: widget_dict}
        self._download_widgets = {}

    def show_download_history(self):
        dlg = DownloadHistoryDialog(self.parent())
        dlg.exec()

    def add_download_item(self, download_item):
        """为一个下载请求添加一行进度条 UI"""
        container = QVBoxLayout()

        # 文件名 + 状态
        name_layout = QHBoxLayout()
        file_name = os.path.basename(download_item.downloadFileName())
        name_label = QLabel(file_name)
        name_label.setStyleSheet("font-weight: bold;")
        status_label = QLabel("Downloading...")
        status_label.setStyleSheet("color: #5cb85c;")
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        name_layout.addWidget(status_label)
        container.addLayout(name_layout)

        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setStyleSheet("""
            QProgressBar { max-height: 16px; border: 1px solid #555555; border-radius: 3px; background: #2b2b2b; }
            QProgressBar::chunk { background-color: #3d6a99; }
        """)
        container.addWidget(progress_bar)

        # 详情行：速度、已下载/总大小、剩余时间
        detail_layout = QHBoxLayout()
        speed_label = QLabel("Speed: --")
        size_label = QLabel("Size: --")
        eta_label = QLabel("ETA: --")
        detail_layout.addWidget(speed_label)
        detail_layout.addStretch()
        detail_layout.addWidget(size_label)
        detail_layout.addStretch()
        detail_layout.addWidget(eta_label)
        container.addLayout(detail_layout)

        # 取消按钮
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(lambda: self._cancel_download(download_item))
        container.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self.downloads_layout.addLayout(container)

        widget_dict = {
            "container": container,
            "progress_bar": progress_bar,
            "status_label": status_label,
            "speed_label": speed_label,
            "size_label": size_label,
            "eta_label": eta_label,
            "cancel_btn": cancel_btn,
            "last_received": 0,
            "last_time": _time.time(),
        }
        self._download_widgets[id(download_item)] = widget_dict

        # 绑定下载信号
        download_item.receivedBytesChanged.connect(
            lambda: self._update_progress(download_item)
        )
        download_item.isFinishedChanged.connect(
            lambda: self._on_finished(download_item)
        )

    def _update_progress(self, download_item):
        key = id(download_item)
        if key not in self._download_widgets:
            return
        w = self._download_widgets[key]

        received = download_item.receivedBytes()
        total = download_item.totalBytes()

        now = _time.time()
        elapsed = now - w["last_time"]

        # 计算速度（至少间隔 0.3 秒更新一次，避免抖动）
        if elapsed > 0.3:
            bytes_delta = received - w["last_received"]
            speed = bytes_delta / elapsed if elapsed > 0 else 0
            w["speed_label"].setText(f"Speed: {DownloadManager.format_speed(speed)}")

            # 估算剩余时间
            if speed > 0 and total > 0:
                remaining = (total - received) / speed
                w["eta_label"].setText(
                    f"ETA: {DownloadManager.format_remaining_time(remaining)}"
                )
            else:
                w["eta_label"].setText("ETA: --")

            w["last_received"] = received
            w["last_time"] = now

        # 更新进度条
        if total > 0:
            percent = int(received * 100 / total)
            w["progress_bar"].setValue(percent)
            w["size_label"].setText(
                f"{DownloadManager.format_file_size(received)} / {DownloadManager.format_file_size(total)}"
            )
        else:
            w["progress_bar"].setMaximum(0)  # 不确定大小时显示为忙碌动画
            w["size_label"].setText(f"{DownloadManager.format_file_size(received)}")

    def _on_finished(self, download_item):
        key = id(download_item)
        if key not in self._download_widgets:
            return
        w = self._download_widgets[key]

        from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest

        state = download_item.state()
        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            w["status_label"].setText("Completed")
            w["status_label"].setStyleSheet("color: #5cb85c; font-weight: bold;")
            w["progress_bar"].setValue(100)
            w["speed_label"].setText("")
            w["eta_label"].setText("")
            w["cancel_btn"].setEnabled(False)
            w["cancel_btn"].setText("Done")

            # 保存到下载历史
            DownloadManager.add_download(
                download_item.url().toString(),
                download_item.downloadDirectory()
                + "/"
                + download_item.downloadFileName(),
                download_item.totalBytes(),
                "completed",
            )
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            w["status_label"].setText("Cancelled")
            w["status_label"].setStyleSheet("color: #d9534f;")
            w["cancel_btn"].setEnabled(False)
            w["cancel_btn"].setText("Cancelled")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            w["status_label"].setText("Failed")
            w["status_label"].setStyleSheet("color: #d9534f;")
            w["cancel_btn"].setEnabled(False)

    def _cancel_download(self, download_item):
        download_item.cancel()


class DownloadHistoryDialog(QDialog):
    """下载历史记录对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download History")
        self.resize(700, 450)
        self.main_window = parent

        layout = QVBoxLayout(self)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "File Name", "Size", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_folder_btn = QPushButton("Open Download Folder")
        open_folder_btn.clicked.connect(self.open_download_folder)
        btn_layout.addWidget(open_folder_btn)

        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_downloads)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        self.load_downloads()

    def load_downloads(self):
        self.table.setRowCount(0)
        downloads = DownloadManager.load_downloads()
        downloads = list(reversed(downloads))

        for item in downloads:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item.get("time", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("file_name", "")))
            self.table.setItem(
                row,
                2,
                QTableWidgetItem(
                    DownloadManager.format_file_size(item.get("file_size", 0))
                ),
            )

            status = item.get("status", "unknown")
            status_item = QTableWidgetItem(status.capitalize())
            self.table.setItem(row, 3, status_item)

    def on_double_click(self, row, col):
        """双击打开下载的文件所在目录"""
        downloads = list(reversed(DownloadManager.load_downloads()))
        if row < len(downloads):
            file_path = downloads[row].get("file_path", "")
            if os.path.exists(file_path):
                import subprocess

                # 用系统文件管理器打开文件所在目录并选中文件
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["explorer", "/select,", os.path.normpath(file_path)]
                    )
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", file_path])
                else:
                    subprocess.Popen(["xdg-open", os.path.dirname(file_path)])
            else:
                QMessageBox.warning(
                    self, "File Not Found", f"The file no longer exists:\n{file_path}"
                )

    def open_download_folder(self):
        """打开默认下载文件夹"""
        import subprocess

        download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(download_dir):
            if sys.platform == "win32":
                os.startfile(download_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", download_dir])
            else:
                subprocess.Popen(["xdg-open", download_dir])

    def clear_downloads(self):
        reply = QMessageBox.question(
            self,
            "Clear Download History",
            "Are you sure you want to clear all download history?\n(Downloaded files will not be deleted.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            DownloadManager.clear_downloads()
            self.load_downloads()


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("History")
        self.resize(700, 450)
        self.main_window = parent

        layout = QVBoxLayout(self)

        # 顶部控制栏
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.textChanged.connect(self.filter_history)

        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(clear_btn)
        layout.addLayout(top_layout)

        # 历史记录表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Time", "Title", "URL"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_double_click)

        layout.addWidget(self.table)

        self.load_history()

    def load_history(self, filter_text=""):
        self.table.setRowCount(0)
        history = HistoryManager.load_history()
        # 反转以显示最新
        history = list(reversed(history))

        for item in history:
            time_str = item.get("time", "")
            title_str = item.get("title", "")
            url_str = item.get("url", "")

            if (
                filter_text.lower() in title_str.lower()
                or filter_text.lower() in url_str.lower()
                or not filter_text
            ):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(time_str))
                self.table.setItem(row, 1, QTableWidgetItem(title_str))
                self.table.setItem(row, 2, QTableWidgetItem(url_str))

    def filter_history(self, text):
        self.load_history(text)

    def on_double_click(self, row, col):
        url = self.table.item(row, 2).text()
        if self.main_window:
            self.main_window.add_new_tab(QUrl(url), "Loading...")
        self.accept()

    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            HistoryManager.clear_history()
            self.load_history()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NanoBrowser")
        self.setGeometry(100, 100, 1024, 768)
        self.setStyleSheet(STYLE_SHEET)

        # 加载设置
        self.settings = SettingsManager.load_settings()

        # 1. 进度条 (统一显示在上方)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()

        # 2. 多标签页组件
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)

        # 标签页右键菜单
        self.tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(
            self.show_tab_context_menu
        )

        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.progress_bar)
        central_layout.addWidget(self.tabs)

        central_widget = QDialog()  # Using a dummy widget to hold layout
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # 3. 导航栏
        nav_bar = QToolBar("Navigation")
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)

        # 图标按钮
        self.back_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self
        )
        self.back_btn.triggered.connect(self.navigate_back)
        nav_bar.addAction(self.back_btn)

        self.forward_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward),
            "Forward",
            self,
        )
        self.forward_btn.triggered.connect(self.navigate_forward)
        nav_bar.addAction(self.forward_btn)

        self.reload_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "Reload",
            self,
        )
        self.reload_btn.triggered.connect(self.navigate_reload)
        nav_bar.addAction(self.reload_btn)

        self.home_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon),
            "Home",
            self,
        )
        self.home_btn.triggered.connect(self.navigate_home)
        nav_bar.addAction(self.home_btn)

        nav_bar.addSeparator()

        # 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # 收藏按钮
        bookmark_btn = QAction("★", self)
        bookmark_btn.setToolTip("Bookmark this page")
        bookmark_btn.triggered.connect(self.save_bookmark)
        nav_bar.addAction(bookmark_btn)

        # 搜索引擎设置下拉框
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Bing", "Google", "Baidu"])
        current_engine = self.settings.get("search_engine", "Bing")
        if current_engine in ["Bing", "Google", "Baidu"]:
            self.engine_combo.setCurrentText(current_engine)
        self.engine_combo.currentTextChanged.connect(self.change_search_engine)
        nav_bar.addWidget(self.engine_combo)

        # 历史记录按钮
        history_btn = QAction("History", self)
        history_btn.triggered.connect(self.show_history)
        nav_bar.addAction(history_btn)

        # 添加新标签页按钮置于工具栏
        new_tab_btn = QAction("+", self)
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.triggered.connect(
            lambda: self.add_new_tab(QUrl("https://www.bing.com"), "New Tab")
        )
        nav_bar.addAction(new_tab_btn)

        # 4. 书签菜单
        self.bookmark_menu = self.menuBar().addMenu("Bookmarks")
        self.update_bookmark_menu()

        # 5. 下载菜单
        download_menu = self.menuBar().addMenu("Downloads")

        show_downloads_action = QAction("Show Downloads", self)
        show_downloads_action.triggered.connect(self.show_download_progress)
        download_menu.addAction(show_downloads_action)

        download_history_action = QAction("Download History", self)
        download_history_action.triggered.connect(self.show_download_history)
        download_menu.addAction(download_history_action)

        # 6. 下载进度对话框 (单例)
        self.download_progress_dialog = None

        # 监听下载请求
        QWebEngineProfile.defaultProfile().downloadRequested.connect(
            self.on_download_requested
        )

        # 初始化时，先清空可能存在的缓存以解决某些情况下的网页打不开
        QWebEngineProfile.defaultProfile().clearHttpCache()

        # 初始标签页
        self.add_new_tab(QUrl("https://www.bing.com"), "Homepage")

    def change_search_engine(self, engine_name):
        self.settings["search_engine"] = engine_name
        SettingsManager.save_settings(self.settings)

    def get_search_url(self, keyword):
        engine_name = self.settings.get("search_engine", "Bing")
        template = SEARCH_ENGINES.get(engine_name, SEARCH_ENGINES["Bing"])
        return template.format(keyword)

    def update_bookmark_menu(self):
        self.bookmark_menu.clear()
        bookmarks = BookmarkManager.load_bookmarks()

        for bm in bookmarks:
            action = QAction(bm["title"], self)
            action.triggered.connect(
                lambda checked, url=bm["url"]: self.load_in_current_tab(url)
            )
            self.bookmark_menu.addAction(action)

        if bookmarks:
            self.bookmark_menu.addSeparator()

        manage_action = QAction("Manage Bookmarks...", self)
        manage_action.triggered.connect(self.show_bookmark_manager)
        self.bookmark_menu.addAction(manage_action)

    def load_in_current_tab(self, url):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            self.add_new_tab(QUrl(url), "Bookmark")

    def show_bookmark_manager(self):
        # 简易的书签管理功能，供以后展
        QMessageBox.information(
            self,
            "Bookmarks",
            "Bookmark manager will be full-featured in a future update.\nCurrently managed via menus.",
        )

    def save_bookmark(self):
        if self.tabs.currentWidget():
            url = self.tabs.currentWidget().url().toString()
            title = self.tabs.tabText(self.tabs.currentIndex())
            if BookmarkManager.add_bookmark(url, title):
                self.update_bookmark_menu()
                # 显示简短提示状态栏内容
                self.statusBar().showMessage(f"Saved bookmark: {title}", 3000)
            else:
                self.statusBar().showMessage(
                    "Bookmark already exists or failed to save", 3000
                )

    def show_history(self):
        dlg = HistoryDialog(self)
        dlg.exec()

    def add_new_tab(self, qurl, label):
        browser = WebEngineView(self)

        # 捕获 ssl 错误以防由于代理导致网页加载失败
        def handle_certificate_error(error):
            error.ignoreCertificateError()
            return True

        browser.page().certificateError.connect(handle_certificate_error)

        browser.setUrl(qurl)

        browser.urlChanged.connect(lambda q: self.update_url_bar(q, browser))
        browser.titleChanged.connect(
            lambda title: self.update_tab_title(title, browser)
        )
        browser.loadFinished.connect(lambda ok: self.on_load_finished(ok, browser))
        browser.iconChanged.connect(lambda icon: self.update_tab_icon(icon, browser))

        # 展示加载进度
        browser.loadProgress.connect(
            lambda progress: self.update_progress(progress, browser)
        )
        browser.loadStarted.connect(
            lambda: self.progress_bar.show()
            if self.tabs.currentWidget() == browser
            else None
        )

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        return browser

    def update_progress(self, progress, browser):
        if browser == self.tabs.currentWidget():
            if progress < 100:
                self.progress_bar.show()
                self.progress_bar.setValue(progress)
            else:
                self.progress_bar.hide()

    def update_tab_icon(self, icon, browser):
        index = self.tabs.indexOf(browser)
        if index != -1 and not icon.isNull():
            self.tabs.setTabIcon(index, icon)

    def on_load_finished(self, ok, browser):
        if browser == self.tabs.currentWidget():
            self.progress_bar.hide()

        if ok:
            url = browser.url().toString()
            title = browser.title()
            HistoryManager.add_history(url, title)
        else:
            self.update_tab_title("Load Error", browser)

    def update_tab_title(self, title, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            # 缩短非常长的标题
            display_title = title if len(title) < 30 else title[:27] + "..."
            self.tabs.setTabText(index, display_title)
            self.tabs.setTabToolTip(index, title)
            if browser == self.tabs.currentWidget():
                self.setWindowTitle(f"{title} - NanoBrowser")

    def current_tab_changed(self, i):
        if i == -1:
            return
        widget = self.tabs.currentWidget()
        qurl = widget.url()
        self.update_url_bar(qurl, widget)
        self.setWindowTitle(f"{widget.title()} - NanoBrowser")

    def close_tab(self, i):
        if self.tabs.count() <= 1:
            # 如果是最后一个标签页，不关闭窗口，而是跳转到主页并重置状态
            widget = self.tabs.widget(i)
            widget.setUrl(QUrl("about:blank"))  # 或者跳主页
            self.tabs.setTabText(i, "New Tab")
            self.tabs.setTabIcon(i, QIcon())
            return

        widget = self.tabs.widget(i)
        self.tabs.removeTab(i)
        widget.deleteLater()

    def show_tab_context_menu(self, point):
        index = self.tabs.tabBar().tabAt(point)
        if index == -1:
            return

        menu = QMenu(self)
        close_action = QAction("Close Tab", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        menu.addAction(close_action)

        close_others_action = QAction("Close Other Tabs", self)
        close_others_action.triggered.connect(lambda: self.close_other_tabs(index))
        menu.addAction(close_others_action)

        menu.addSeparator()

        new_action = QAction("New Tab", self)
        new_action.triggered.connect(
            lambda: self.add_new_tab(QUrl("https://www.bing.com"), "New Tab")
        )
        menu.addAction(new_action)

        menu.exec(self.tabs.tabBar().mapToGlobal(point))

    def close_other_tabs(self, keep_index):
        # 从后往前删，避免索引变化问题
        for i in range(self.tabs.count() - 1, -1, -1):
            if i != keep_index and self.tabs.count() > 1:
                self.close_tab(i)

    def navigate_home(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl("https://www.bing.com"))

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        # 简单判断是否是网址格式
        is_url = re.match(r"^(http://|https://|file://)", text) or (
            "." in text and " " not in text
        )

        if is_url:
            if not re.match(r"^[a-zA-Z]+://", text):
                text = "https://" + text
            url = text
        else:
            url = self.get_search_url(text)

        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            self.add_new_tab(QUrl(url), "Loading...")

    def update_url_bar(self, qurl, browser=None):
        if browser == self.tabs.currentWidget():
            url_str = qurl.toString()
            if url_str != "about:blank":
                self.url_bar.setText(url_str)
                self.url_bar.setCursorPosition(0)
            else:
                self.url_bar.setText("")

    def navigate_back(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().back()

    def navigate_forward(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().forward()

    def navigate_reload(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().reload()

    # ---- 下载管理功能 ----

    def on_download_requested(self, download_item):
        """处理下载请求：弹出保存文件对话框，然后开始下载并显示进度"""
        suggested_name = download_item.downloadFileName()
        suggested_dir = download_item.downloadDirectory()

        # 让用户选择保存路径
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", os.path.join(suggested_dir, suggested_name)
        )

        if not save_path:
            download_item.cancel()
            return

        # 设置下载路径
        download_item.setDownloadDirectory(os.path.dirname(save_path))
        download_item.setDownloadFileName(os.path.basename(save_path))
        download_item.accept()

        # 打开或创建进度对话框
        if (
            self.download_progress_dialog is None
            or not self.download_progress_dialog.isVisible()
        ):
            self.download_progress_dialog = DownloadProgressDialog(self)

        self.download_progress_dialog.add_download_item(download_item)
        self.download_progress_dialog.show()
        self.download_progress_dialog.raise_()

        self.statusBar().showMessage(
            f"Downloading: {os.path.basename(save_path)}", 3000
        )

    def show_download_progress(self):
        """显示下载进度对话框"""
        if (
            self.download_progress_dialog is None
            or not self.download_progress_dialog.isVisible()
        ):
            self.download_progress_dialog = DownloadProgressDialog(self)
        self.download_progress_dialog.show()
        self.download_progress_dialog.raise_()

    def show_download_history(self):
        """显示下载历史对话框"""
        dlg = DownloadHistoryDialog(self)
        dlg.exec()


def main():
    # 启用高分屏支持
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # 设置应用级的默认图标和样式
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
