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
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QInputDialog,
    QAbstractItemView,
    QCompleter,
    QStyledItemDelegate,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QListWidget,
    QStackedWidget,
    QListWidgetItem,
    QFrame,
    QWidget,
)
from PyQt6.QtCore import QUrl, Qt, QTimer, QStringListModel
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

from history_manager import HistoryManager
from bookmark_manager import BookmarkManager
from download_manager import DownloadManager
from session_manager import SessionManager

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
    支持可选的 QWebEngineProfile (用于无痕模式)。
    """

    def __init__(self, main_window, profile=None, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self._custom_profile = profile
        if profile:
            page = QWebEnginePage(profile, self)
            self.setPage(page)

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


class SourceViewDialog(QDialog):
    """页面源代码查看对话框，带简单语法高亮和搜索功能"""

    def __init__(self, html_content, page_title="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Source: {page_title}" if page_title else "Page Source")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in source code...")
        self.search_input.returnPressed.connect(self.find_next)

        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self.find_next)
        find_prev_btn = QPushButton("Find Previous")
        find_prev_btn.clicked.connect(self.find_previous)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(find_btn)
        search_layout.addWidget(find_prev_btn)
        layout.addLayout(search_layout)

        # 源代码显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFontFamily("Consolas, 'Courier New', monospace")
        self.text_edit.setFontPointSize(10)
        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_edit.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; "
            "border: 1px solid #555555; padding: 5px; }"
        )
        layout.addWidget(self.text_edit)

        # 应用简单的语法高亮后设置文本
        highlighted = self._simple_highlight(html_content)
        self.text_edit.setHtml(f"<pre style='color:#d4d4d4;'>{highlighted}</pre>")

    def _simple_highlight(self, html):
        """简单的 HTML 语法高亮（将标签、属性、字符串着色）"""
        import html as html_module

        # 先对内容进行 HTML 转义
        escaped = html_module.escape(html)

        # 高亮 HTML 标签 <...>
        escaped = re.sub(
            r"(&lt;/?)([\w\-]+)", r'<span style="color:#569cd6;">\1\2</span>', escaped
        )
        escaped = re.sub(r"(&gt;)", r'<span style="color:#569cd6;">\1</span>', escaped)
        # 高亮属性值 "..."
        escaped = re.sub(
            r"(&quot;.*?&quot;)", r'<span style="color:#ce9178;">\1</span>', escaped
        )
        # 高亮注释 <!-- ... -->
        escaped = re.sub(
            r"(&lt;!--.*?--&gt;)",
            r'<span style="color:#6a9955;">\1</span>',
            escaped,
            flags=re.DOTALL,
        )
        return escaped

    def find_next(self):
        """向下查找"""
        text = self.search_input.text()
        if text:
            self.text_edit.find(text)

    def find_previous(self):
        """向上查找"""
        from PyQt6.QtGui import QTextDocument

        text = self.search_input.text()
        if text:
            self.text_edit.find(text, QTextDocument.FindFlag.FindBackward)


class IncognitoWindow(QMainWindow):
    """无痕浏览窗口 - 使用独立的 off-the-record QWebEngineProfile"""

    def __init__(self, parent_window=None):
        super().__init__()
        self._parent_window = parent_window
        self.setWindowTitle("[Incognito] NanoBrowser")
        self.setGeometry(150, 150, 1024, 768)
        self.setStyleSheet(STYLE_SHEET)

        # 使用 off-the-record profile (不保存任何数据到磁盘)
        self._incognito_profile = QWebEngineProfile(self)
        self._incognito_profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.NoCache
        )

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # 导航栏
        nav_bar = QToolBar("Navigation")
        nav_bar.setMovable(False)
        self.addToolBar(nav_bar)

        back_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self
        )
        back_btn.triggered.connect(
            lambda: self.tabs.currentWidget() and self.tabs.currentWidget().back()
        )
        nav_bar.addAction(back_btn)

        forward_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward),
            "Forward",
            self,
        )
        forward_btn.triggered.connect(
            lambda: self.tabs.currentWidget() and self.tabs.currentWidget().forward()
        )
        nav_bar.addAction(forward_btn)

        reload_btn = QAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload),
            "Reload",
            self,
        )
        reload_btn.triggered.connect(
            lambda: self.tabs.currentWidget() and self.tabs.currentWidget().reload()
        )
        nav_bar.addAction(reload_btn)

        nav_bar.addSeparator()

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("[Incognito] Search or enter address")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        new_tab_btn = QAction("+", self)
        new_tab_btn.setToolTip("New Incognito Tab")
        new_tab_btn.triggered.connect(
            lambda: self.add_new_tab(QUrl("https://www.bing.com"), "New Tab")
        )
        nav_bar.addAction(new_tab_btn)

        # 无痕模式提示
        self.statusBar().showMessage(
            "Incognito Mode: History and cookies will not be saved.", 10000
        )

        # 初始标签页
        self.add_new_tab(QUrl("https://www.bing.com"), "Incognito Tab")

    def add_new_tab(self, qurl, label):
        browser = WebEngineView(self, profile=self._incognito_profile)

        def handle_certificate_error(error):
            error.ignoreCertificateError()
            return True

        browser.page().certificateError.connect(handle_certificate_error)
        browser.setUrl(qurl)
        browser.urlChanged.connect(lambda q: self._update_url_bar(q, browser))
        browser.titleChanged.connect(
            lambda title: self._update_tab_title(title, browser)
        )
        browser.iconChanged.connect(lambda icon: self._update_tab_icon(icon, browser))

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        return browser

    def _update_url_bar(self, qurl, browser):
        if browser == self.tabs.currentWidget():
            url_str = qurl.toString()
            if url_str != "about:blank":
                self.url_bar.setText(url_str)
                self.url_bar.setCursorPosition(0)
            else:
                self.url_bar.setText("")

    def _update_tab_title(self, title, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            display = title if len(title) < 30 else title[:27] + "..."
            self.tabs.setTabText(index, display)
            self.tabs.setTabToolTip(index, title)
            if browser == self.tabs.currentWidget():
                self.setWindowTitle(f"[Incognito] {title} - NanoBrowser")

    def _update_tab_icon(self, icon, browser):
        index = self.tabs.indexOf(browser)
        if index != -1 and not icon.isNull():
            self.tabs.setTabIcon(index, icon)

    def current_tab_changed(self, i):
        if i == -1:
            return
        widget = self.tabs.currentWidget()
        if widget:
            self._update_url_bar(widget.url(), widget)
            self.setWindowTitle(f"[Incognito] {widget.title()} - NanoBrowser")

    def close_tab(self, i):
        if self.tabs.count() <= 1:
            self.close()
            return
        widget = self.tabs.widget(i)
        self.tabs.removeTab(i)
        widget.deleteLater()

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        is_url = re.match(r"^(http://|https://|file://)", text) or (
            "." in text and " " not in text
        )
        if is_url:
            if not re.match(r"^[a-zA-Z]+://", text):
                text = "https://" + text
            url = text
        else:
            url = SEARCH_ENGINES.get("Bing", "https://www.bing.com/search?q={}").format(
                text
            )
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            self.add_new_tab(QUrl(url), "Loading...")

    def closeEvent(self, event):
        """关闭时清除无痕 profile 的所有数据"""
        self._incognito_profile.clearHttpCache()
        self._incognito_profile.clearAllVisitedLinks()
        # 关闭所有标签页
        while self.tabs.count() > 0:
            widget = self.tabs.widget(0)
            self.tabs.removeTab(0)
            widget.deleteLater()
        event.accept()


class FindInPageBar(QDialog):
    """页面内查找浮动条，类似 Chrome 的 Ctrl+F 查找栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setStyleSheet(
            "FindInPageBar { background-color: #3c3f41; border: 1px solid #555555; border-radius: 6px; }"
        )
        self.main_window = parent
        self._last_search = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find in page...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)

        self.result_label = QLabel("")
        self.result_label.setStyleSheet(
            "color: #a9b7c6; font-size: 11px; min-width: 60px;"
        )
        layout.addWidget(self.result_label)

        prev_btn = QPushButton("^")
        prev_btn.setToolTip("Previous (Shift+Enter)")
        prev_btn.setFixedWidth(30)
        prev_btn.clicked.connect(self.find_previous)
        layout.addWidget(prev_btn)

        next_btn = QPushButton("v")
        next_btn.setToolTip("Next (Enter)")
        next_btn.setFixedWidth(30)
        next_btn.clicked.connect(self.find_next)
        layout.addWidget(next_btn)

        close_btn = QPushButton("X")
        close_btn.setToolTip("Close (Esc)")
        close_btn.setFixedWidth(30)
        close_btn.clicked.connect(self.close_find)
        layout.addWidget(close_btn)

    def keyPressEvent(self, event):
        """处理 Enter/Shift+Enter 和 Esc"""
        if event.key() == Qt.Key.Key_Escape:
            self.close_find()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.find_previous()
            else:
                self.find_next()
        else:
            super().keyPressEvent(event)

    def show_bar(self):
        """显示查找栏并聚焦到输入框"""
        if self.main_window:
            # 定位在窗口右上方
            parent_rect = self.main_window.geometry()
            x = parent_rect.x() + parent_rect.width() - self.width() - 20
            y = parent_rect.y() + 80
            self.move(x, y)
        self.show()
        self.raise_()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def close_find(self):
        """关闭查找栏并清除高亮"""
        self.hide()
        # 清除页面中的查找高亮
        if self.main_window:
            browser = self.main_window.tabs.currentWidget()
            if browser:
                browser.page().findText("")

    def _on_text_changed(self, text):
        """输入文字时实时搜索"""
        self._last_search = text
        if not text:
            self.result_label.setText("")
            if self.main_window:
                browser = self.main_window.tabs.currentWidget()
                if browser:
                    browser.page().findText("")
            return
        self.find_next()

    def find_next(self):
        """向下查找"""
        text = self.search_input.text()
        if not text or not self.main_window:
            return
        browser = self.main_window.tabs.currentWidget()
        if browser:
            browser.page().findText(text, callback=self._on_find_result)

    def find_previous(self):
        """向上查找"""
        text = self.search_input.text()
        if not text or not self.main_window:
            return
        browser = self.main_window.tabs.currentWidget()
        if browser:
            from PyQt6.QtWebEngineCore import QWebEnginePage

            browser.page().findText(
                text,
                QWebEnginePage.FindFlag.FindBackward,
                callback=self._on_find_result,
            )

    def _on_find_result(self, result):
        """处理查找结果回调"""
        if hasattr(result, "numberOfMatches"):
            count = result.numberOfMatches()
            active = result.activeMatch()
            if count > 0:
                self.result_label.setText(f"{active}/{count}")
                self.result_label.setStyleSheet(
                    "color: #a9b7c6; font-size: 11px; min-width: 60px;"
                )
            else:
                self.result_label.setText("No results")
                self.result_label.setStyleSheet(
                    "color: #d9534f; font-size: 11px; min-width: 60px;"
                )
        else:
            # PyQt6 旧版本可能不支持 FindTextResult
            if result:
                self.result_label.setText("Found")
            else:
                self.result_label.setText("No results")
                self.result_label.setStyleSheet(
                    "color: #d9534f; font-size: 11px; min-width: 60px;"
                )


class ShortcutsHelpDialog(QDialog):
    """快捷键帮助对话框，显示所有可用的快捷键"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.resize(500, 450)

        layout = QVBoxLayout(self)

        header = QLabel("Keyboard Shortcuts")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(header)

        # 快捷键表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Shortcut", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        shortcuts = [
            ("Ctrl+T", "New tab"),
            ("Ctrl+W", "Close current tab"),
            ("Ctrl+Shift+T", "Reopen closed tab"),
            ("Ctrl+Tab", "Next tab"),
            ("Ctrl+Shift+Tab", "Previous tab"),
            ("Ctrl+L", "Focus address bar"),
            ("Ctrl+R", "Refresh page"),
            ("Esc", "Stop loading page"),
            ("Ctrl+D", "Bookmark current page"),
            ("Ctrl+H", "Open history"),
            ("Ctrl+F", "Find in page"),
            ("Ctrl+U", "View page source"),
            ("Ctrl++  /  Ctrl+=", "Zoom in"),
            ("Ctrl+-", "Zoom out"),
            ("Ctrl+0", "Reset zoom"),
            ("Ctrl+Shift+N", "New incognito window"),
            ("F1", "Show this help"),
            ("F11", "Toggle fullscreen"),
        ]

        self.table.setRowCount(len(shortcuts))
        for row, (key, desc) in enumerate(shortcuts):
            key_item = QTableWidgetItem(key)
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, key_item)
            self.table.setItem(row, 1, QTableWidgetItem(desc))

        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class BookmarkManagerDialog(QDialog):
    """
    完整的书签管理对话框 - 支持文件夹、添加/编辑/删除、拖拽排序、导入导出。
    使用 QTreeWidget 展示书签的层级结构。
    """

    # 自定义角色存储数据
    ROLE_TYPE = Qt.ItemDataRole.UserRole
    ROLE_URL = Qt.ItemDataRole.UserRole + 1
    ROLE_FOLDER_NAME = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmark Manager")
        self.resize(700, 500)
        self.main_window = parent
        self._changed = False

        layout = QVBoxLayout(self)

        # 工具按钮行
        toolbar_layout = QHBoxLayout()

        add_bm_btn = QPushButton("Add Bookmark")
        add_bm_btn.clicked.connect(self.add_bookmark)
        toolbar_layout.addWidget(add_bm_btn)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        toolbar_layout.addWidget(add_folder_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_item)
        toolbar_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_item)
        toolbar_layout.addWidget(delete_btn)

        toolbar_layout.addStretch()

        import_btn = QPushButton("Import HTML")
        import_btn.clicked.connect(self.import_bookmarks)
        toolbar_layout.addWidget(import_btn)

        export_btn = QPushButton("Export HTML")
        export_btn.clicked.connect(self.export_bookmarks)
        toolbar_layout.addWidget(export_btn)

        layout.addLayout(toolbar_layout)

        # 树形书签列表
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Title", "URL"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet(
            "QTreeWidget { background-color: #2b2b2b; color: #a9b7c6; "
            "alternate-background-color: #313335; border: 1px solid #555555; } "
            "QTreeWidget::item:selected { background-color: #4b6eaf; color: #ffffff; }"
        )

        # 启用拖拽排序
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.tree.itemDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.tree)

        # 底部关闭按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

        self.load_tree()

    def load_tree(self):
        """从 BookmarkManager 加载书签数据到树形控件"""
        self.tree.clear()
        bookmarks = BookmarkManager.load_bookmarks()
        self._populate_tree(self.tree.invisibleRootItem(), bookmarks)
        self.tree.expandAll()

    def _populate_tree(self, parent_item, items):
        """递归填充树形控件"""
        for item in items:
            if item.get("type") == "folder":
                node = QTreeWidgetItem(parent_item)
                node.setText(0, item["name"])
                node.setText(1, "")
                node.setData(0, self.ROLE_TYPE, "folder")
                node.setData(0, self.ROLE_FOLDER_NAME, item["name"])
                # 允许文件夹接收拖拽
                node.setFlags(
                    node.flags()
                    | Qt.ItemFlag.ItemIsDropEnabled
                    | Qt.ItemFlag.ItemIsDragEnabled
                )
                self._populate_tree(node, item.get("children", []))
            elif item.get("type") == "bookmark":
                node = QTreeWidgetItem(parent_item)
                node.setText(0, item.get("title", ""))
                node.setText(1, item.get("url", ""))
                node.setData(0, self.ROLE_TYPE, "bookmark")
                node.setData(0, self.ROLE_URL, item.get("url", ""))
                node.setFlags(node.flags() | Qt.ItemFlag.ItemIsDragEnabled)

    def _tree_to_bookmarks(self):
        """将树形控件的当前状态转换回书签数据列表"""
        root = self.tree.invisibleRootItem()
        return self._node_children_to_list(root)

    def _node_children_to_list(self, node):
        """递归将树形节点转为书签列表"""
        result = []
        for i in range(node.childCount()):
            child = node.child(i)
            item_type = child.data(0, self.ROLE_TYPE)
            if item_type == "folder":
                result.append(
                    {
                        "type": "folder",
                        "name": child.text(0),
                        "children": self._node_children_to_list(child),
                    }
                )
            elif item_type == "bookmark":
                result.append(
                    {
                        "type": "bookmark",
                        "url": child.text(1),
                        "title": child.text(0),
                        "added": "",
                    }
                )
        return result

    def add_bookmark(self):
        """添加新书签"""
        title, ok = QInputDialog.getText(self, "Add Bookmark", "Title:")
        if not ok or not title:
            return
        url, ok = QInputDialog.getText(self, "Add Bookmark", "URL:", text="https://")
        if not ok or not url:
            return

        # 添加到当前选中的文件夹节点或根节点
        selected = self.tree.currentItem()
        parent_node = self.tree.invisibleRootItem()
        if selected:
            if selected.data(0, self.ROLE_TYPE) == "folder":
                parent_node = selected
            elif selected.parent():
                parent_node = selected.parent()

        node = QTreeWidgetItem(parent_node)
        node.setText(0, title)
        node.setText(1, url)
        node.setData(0, self.ROLE_TYPE, "bookmark")
        node.setData(0, self.ROLE_URL, url)
        node.setFlags(node.flags() | Qt.ItemFlag.ItemIsDragEnabled)

        self._changed = True
        self._save_from_tree()

    def add_folder(self):
        """添加新文件夹"""
        name, ok = QInputDialog.getText(self, "Add Folder", "Folder name:")
        if not ok or not name:
            return

        selected = self.tree.currentItem()
        parent_node = self.tree.invisibleRootItem()
        if selected and selected.data(0, self.ROLE_TYPE) == "folder":
            parent_node = selected

        node = QTreeWidgetItem(parent_node)
        node.setText(0, name)
        node.setText(1, "")
        node.setData(0, self.ROLE_TYPE, "folder")
        node.setData(0, self.ROLE_FOLDER_NAME, name)
        node.setFlags(
            node.flags() | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled
        )

        self._changed = True
        self._save_from_tree()

    def edit_item(self):
        """编辑选中的书签或文件夹"""
        selected = self.tree.currentItem()
        if not selected:
            QMessageBox.information(self, "Edit", "Please select an item to edit.")
            return

        item_type = selected.data(0, self.ROLE_TYPE)
        if item_type == "bookmark":
            title, ok = QInputDialog.getText(
                self, "Edit Bookmark", "Title:", text=selected.text(0)
            )
            if not ok:
                return
            url, ok = QInputDialog.getText(
                self, "Edit Bookmark", "URL:", text=selected.text(1)
            )
            if not ok:
                return
            selected.setText(0, title)
            selected.setText(1, url)
            selected.setData(0, self.ROLE_URL, url)
        elif item_type == "folder":
            name, ok = QInputDialog.getText(
                self, "Edit Folder", "Folder name:", text=selected.text(0)
            )
            if not ok:
                return
            selected.setText(0, name)
            selected.setData(0, self.ROLE_FOLDER_NAME, name)

        self._changed = True
        self._save_from_tree()

    def delete_item(self):
        """删除选中的书签或文件夹"""
        selected = self.tree.currentItem()
        if not selected:
            QMessageBox.information(self, "Delete", "Please select an item to delete.")
            return

        item_type = selected.data(0, self.ROLE_TYPE)
        label = selected.text(0)

        if item_type == "folder":
            reply = QMessageBox.question(
                self,
                "Delete Folder",
                f"Delete folder '{label}' and all its contents?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
        else:
            reply = QMessageBox.question(
                self,
                "Delete Bookmark",
                f"Delete bookmark '{label}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

        if reply == QMessageBox.StandardButton.Yes:
            parent = selected.parent()
            if parent:
                parent.removeChild(selected)
            else:
                index = self.tree.indexOfTopLevelItem(selected)
                self.tree.takeTopLevelItem(index)

            self._changed = True
            self._save_from_tree()

    def import_bookmarks(self):
        """从 HTML 文件导入书签"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Bookmarks", "", "HTML Files (*.html *.htm);;All Files (*)"
        )
        if not filepath:
            return

        count = BookmarkManager.import_from_html(filepath)
        self.load_tree()
        self._changed = True
        QMessageBox.information(
            self, "Import Complete", f"Successfully imported {count} bookmarks."
        )

    def export_bookmarks(self):
        """导出书签为 HTML 文件"""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Bookmarks",
            "bookmarks.html",
            "HTML Files (*.html);;All Files (*)",
        )
        if not filepath:
            return

        # 先保存当前树的状态
        self._save_from_tree()

        if BookmarkManager.export_to_html(filepath):
            QMessageBox.information(
                self, "Export Complete", f"Bookmarks exported to:\n{filepath}"
            )
        else:
            QMessageBox.warning(self, "Export Error", "Failed to export bookmarks.")

    def on_double_click(self, item, column):
        """双击书签在主窗口中打开"""
        if item.data(0, self.ROLE_TYPE) == "bookmark":
            url = item.text(1)
            if url and self.main_window:
                self.main_window.add_new_tab(QUrl(url), item.text(0))

    def _save_from_tree(self):
        """将树形控件的当前状态保存回 bookmarks.json"""
        data = self._tree_to_bookmarks()
        BookmarkManager.save_bookmarks(data)
        # 通知主窗口更新书签菜单
        if self.main_window and hasattr(self.main_window, "update_bookmark_menu"):
            self.main_window.update_bookmark_menu()

    def closeEvent(self, event):
        """关闭时保存拖拽后的排序结果"""
        self._save_from_tree()
        event.accept()


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


class SettingsDialog(QDialog):
    """统一的浏览器设置对话框"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 450)
        self.settings = dict(settings)  # 工作副本
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)

        # 左侧分类列表
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(140)
        self.category_list.setSpacing(2)
        categories = ["General", "Privacy", "Appearance", "Advanced"]
        for cat in categories:
            item = QListWidgetItem(cat)
            self.category_list.addItem(item)
        self.category_list.currentRowChanged.connect(self._switch_page)
        layout.addWidget(self.category_list)

        # 右侧分页
        right_layout = QVBoxLayout()
        self.pages = QStackedWidget()

        self.pages.addWidget(self._create_general_page())
        self.pages.addWidget(self._create_privacy_page())
        self.pages.addWidget(self._create_appearance_page())
        self.pages.addWidget(self._create_advanced_page())

        right_layout.addWidget(self.pages)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        restore_btn = QPushButton("Restore Defaults")
        restore_btn.clicked.connect(self._restore_defaults)
        btn_layout.addWidget(restore_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        right_layout.addLayout(btn_layout)

        layout.addLayout(right_layout)
        self.category_list.setCurrentRow(0)

    def _switch_page(self, index):
        self.pages.setCurrentIndex(index)

    # ---- General ----
    def _create_general_page(self):
        page = QWidget()
        form = QFormLayout(page)
        form.setSpacing(12)

        # 主页
        self.homepage_edit = QLineEdit(
            self.settings.get("homepage", "https://www.bing.com")
        )
        form.addRow("Homepage:", self.homepage_edit)

        # 搜索引擎
        self.engine_combo_setting = QComboBox()
        self.engine_combo_setting.addItems(["Bing", "Google", "Baidu"])
        current_engine = self.settings.get("search_engine", "Bing")
        if current_engine in ["Bing", "Google", "Baidu"]:
            self.engine_combo_setting.setCurrentText(current_engine)
        form.addRow("Search Engine:", self.engine_combo_setting)

        # 启动行为
        self.restore_session_cb = QCheckBox("Restore previous session on startup")
        self.restore_session_cb.setChecked(self.settings.get("restore_session", True))
        form.addRow("Startup:", self.restore_session_cb)

        # 下载位置
        dl_layout = QHBoxLayout()
        self.download_dir_edit = QLineEdit(
            self.settings.get("download_dir", os.path.expanduser("~/Downloads"))
        )
        dl_browse_btn = QPushButton("Browse...")
        dl_browse_btn.clicked.connect(self._browse_download_dir)
        dl_layout.addWidget(self.download_dir_edit)
        dl_layout.addWidget(dl_browse_btn)
        form.addRow("Download folder:", dl_layout)

        return page

    def _browse_download_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.download_dir_edit.text()
        )
        if directory:
            self.download_dir_edit.setText(directory)

    # ---- Privacy ----
    def _create_privacy_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        group = QGroupBox("Privacy & Security")
        group_layout = QVBoxLayout(group)

        self.block_popups_cb = QCheckBox("Block pop-up windows")
        self.block_popups_cb.setChecked(self.settings.get("block_popups", True))
        group_layout.addWidget(self.block_popups_cb)

        self.do_not_track_cb = QCheckBox("Send 'Do Not Track' request")
        self.do_not_track_cb.setChecked(self.settings.get("do_not_track", False))
        group_layout.addWidget(self.do_not_track_cb)

        self.js_enabled_cb = QCheckBox("Enable JavaScript")
        self.js_enabled_cb.setChecked(self.settings.get("javascript_enabled", True))
        group_layout.addWidget(self.js_enabled_cb)

        layout.addWidget(group)

        # 清除数据按钮
        clear_group = QGroupBox("Clear Browsing Data")
        clear_layout = QVBoxLayout(clear_group)
        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self._clear_cache)
        clear_layout.addWidget(clear_cache_btn)
        clear_cookies_btn = QPushButton("Clear Cookies")
        clear_cookies_btn.clicked.connect(self._clear_cookies)
        clear_layout.addWidget(clear_cookies_btn)
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        clear_layout.addWidget(clear_history_btn)
        layout.addWidget(clear_group)

        layout.addStretch()
        return page

    def _clear_cache(self):
        QWebEngineProfile.defaultProfile().clearHttpCache()
        QMessageBox.information(
            self, "Cache Cleared", "Browser cache has been cleared."
        )

    def _clear_cookies(self):
        QWebEngineProfile.defaultProfile().cookieStore().deleteAllCookies()
        QMessageBox.information(
            self, "Cookies Cleared", "All cookies have been cleared."
        )

    def _clear_history(self):
        HistoryManager.clear_history()
        QMessageBox.information(
            self, "History Cleared", "Browsing history has been cleared."
        )

    # ---- Appearance ----
    def _create_appearance_page(self):
        page = QWidget()
        form = QFormLayout(page)
        form.setSpacing(12)

        # 主题选择（为 Task 29 预留扩展点）
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Default)", "Light"])
        current_theme = self.settings.get("theme", "Dark (Default)")
        if current_theme in ["Dark (Default)", "Light"]:
            self.theme_combo.setCurrentText(current_theme)
        form.addRow("Theme:", self.theme_combo)

        # 默认缩放
        self.default_zoom_combo = QComboBox()
        zoom_levels = [
            "50%",
            "75%",
            "90%",
            "100%",
            "110%",
            "125%",
            "150%",
            "175%",
            "200%",
        ]
        self.default_zoom_combo.addItems(zoom_levels)
        current_zoom = self.settings.get("default_zoom", "100%")
        if current_zoom in zoom_levels:
            self.default_zoom_combo.setCurrentText(current_zoom)
        else:
            self.default_zoom_combo.setCurrentText("100%")
        form.addRow("Default page zoom:", self.default_zoom_combo)

        return page

    # ---- Advanced ----
    def _create_advanced_page(self):
        page = QWidget()
        form = QFormLayout(page)
        form.setSpacing(12)

        # User-Agent
        self.ua_combo = QComboBox()
        ua_names = [
            "Default (NanoBrowser)",
            "Chrome (Windows)",
            "Firefox (Windows)",
            "Safari (macOS)",
            "Edge (Windows)",
            "Chrome (Android)",
            "Safari (iPhone)",
        ]
        self.ua_combo.addItems(ua_names)
        current_ua = self.settings.get("user_agent", "Default (NanoBrowser)")
        if current_ua in ua_names:
            self.ua_combo.setCurrentText(current_ua)
        form.addRow("User-Agent:", self.ua_combo)

        # 硬件加速
        self.hw_accel_cb = QCheckBox("Enable hardware acceleration")
        self.hw_accel_cb.setChecked(self.settings.get("hardware_acceleration", True))
        form.addRow("Performance:", self.hw_accel_cb)

        # 代理设置（简易文本输入）
        self.proxy_edit = QLineEdit(self.settings.get("proxy", ""))
        self.proxy_edit.setPlaceholderText(
            "e.g. http://127.0.0.1:7890 (leave empty for system proxy)"
        )
        form.addRow("HTTP Proxy:", self.proxy_edit)

        return page

    # ---- Restore Defaults ----
    def _restore_defaults(self):
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.homepage_edit.setText("https://www.bing.com")
        self.engine_combo_setting.setCurrentText("Bing")
        self.restore_session_cb.setChecked(True)
        self.download_dir_edit.setText(os.path.expanduser("~/Downloads"))
        self.block_popups_cb.setChecked(True)
        self.do_not_track_cb.setChecked(False)
        self.js_enabled_cb.setChecked(True)
        self.theme_combo.setCurrentText("Dark (Default)")
        self.default_zoom_combo.setCurrentText("100%")
        self.ua_combo.setCurrentText("Default (NanoBrowser)")
        self.hw_accel_cb.setChecked(True)
        self.proxy_edit.setText("")

    def get_settings(self):
        """返回用户修改后的设置字典"""
        return {
            "homepage": self.homepage_edit.text().strip() or "https://www.bing.com",
            "search_engine": self.engine_combo_setting.currentText(),
            "restore_session": self.restore_session_cb.isChecked(),
            "download_dir": self.download_dir_edit.text().strip(),
            "block_popups": self.block_popups_cb.isChecked(),
            "do_not_track": self.do_not_track_cb.isChecked(),
            "javascript_enabled": self.js_enabled_cb.isChecked(),
            "theme": self.theme_combo.currentText(),
            "default_zoom": self.default_zoom_combo.currentText(),
            "user_agent": self.ua_combo.currentText(),
            "hardware_acceleration": self.hw_accel_cb.isChecked(),
            "proxy": self.proxy_edit.text().strip(),
        }


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

        # 地址栏自动完成
        self._completer_model = QStringListModel()
        self._url_completer = QCompleter()
        self._url_completer.setModel(self._completer_model)
        self._url_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._url_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._url_completer.setMaxVisibleItems(10)
        self._url_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._url_completer.activated.connect(self._on_completer_activated)
        self.url_bar.setCompleter(self._url_completer)
        self.url_bar.textEdited.connect(self._refresh_completer_model)

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

        # 4. 文件菜单
        file_menu = self.menuBar().addMenu("File")

        print_action = QAction("Print...", self)
        print_action.setShortcut(QKeySequence("Ctrl+P"))
        print_action.triggered.connect(self.print_page)
        file_menu.addAction(print_action)

        save_pdf_action = QAction("Save as PDF...", self)
        save_pdf_action.triggered.connect(self.save_as_pdf)
        file_menu.addAction(save_pdf_action)

        # 5. 书签菜单
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

        # 6. 查看菜单
        view_menu = self.menuBar().addMenu("View")

        view_source_action = QAction("Page Source", self)
        view_source_action.setShortcut(QKeySequence("Ctrl+U"))
        view_source_action.triggered.connect(self.view_page_source)
        view_menu.addAction(view_source_action)

        # 6b. 无痕浏览
        self._incognito_windows = []
        incognito_action = QAction("New Incognito Window", self)
        incognito_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        incognito_action.triggered.connect(self.open_incognito_window)
        view_menu.addSeparator()
        view_menu.addAction(incognito_action)

        # 6c. Tools 菜单 - User-Agent 切换
        tools_menu = self.menuBar().addMenu("Tools")
        ua_menu = tools_menu.addMenu("User-Agent")

        self._user_agents = {
            "Default (NanoBrowser)": "",
            "Chrome (Windows)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Firefox (Windows)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Safari (macOS)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Edge (Windows)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Chrome (Android)": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.43 Mobile Safari/537.36",
            "Safari (iPhone)": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        }
        self._ua_action_group = []
        current_ua = self.settings.get("user_agent", "Default (NanoBrowser)")

        for name in self._user_agents:
            action = QAction(name, self)
            action.setCheckable(True)
            if name == current_ua:
                action.setChecked(True)
            action.triggered.connect(
                lambda checked, ua_name=name: self.set_user_agent(ua_name)
            )
            ua_menu.addAction(action)
            self._ua_action_group.append(action)

        ua_menu.addSeparator()
        custom_ua_action = QAction("Custom User-Agent...", self)
        custom_ua_action.triggered.connect(self.set_custom_user_agent)
        ua_menu.addAction(custom_ua_action)

        # 应用已保存的 UA
        self._apply_user_agent(current_ua)

        # Settings 菜单项
        tools_menu.addSeparator()
        settings_action = QAction("Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.open_settings_dialog)
        tools_menu.addAction(settings_action)

        # 7. 下载进度对话框 (单例)
        self.download_progress_dialog = None

        # 监听下载请求
        QWebEngineProfile.defaultProfile().downloadRequested.connect(
            self.on_download_requested
        )

        # 7. 页面缩放 - 每个标签页独立缩放比例
        self._tab_zoom_factors = {}  # {tab_widget_id: zoom_factor}

        # 状态栏缩放显示
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("padding: 0 8px; font-size: 12px;")
        self.statusBar().addPermanentWidget(self.zoom_label)

        # 缩放快捷键
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        zoom_in_shortcut.activated.connect(self.zoom_in)
        zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_in_shortcut2.activated.connect(self.zoom_in)
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self.zoom_out)
        zoom_reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        zoom_reset_shortcut.activated.connect(self.zoom_reset)

        # 8. 全屏浏览模式
        self._is_fullscreen = False
        self._nav_bar = nav_bar  # 保存导航栏引用
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

        # 全屏退出提示标签
        self._fullscreen_tip = QLabel("Press F11 to exit fullscreen", self)
        self._fullscreen_tip.setStyleSheet(
            "background-color: rgba(0, 0, 0, 180); color: white; "
            "padding: 10px 20px; border-radius: 8px; font-size: 14px;"
        )
        self._fullscreen_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fullscreen_tip.hide()

        # 提示自动消失定时器
        self._fullscreen_tip_timer = QTimer(self)
        self._fullscreen_tip_timer.setSingleShot(True)
        self._fullscreen_tip_timer.timeout.connect(self._fullscreen_tip.hide)

        # 9. 页面内查找
        self._find_bar = FindInPageBar(self)
        self._find_bar.hide()
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_bar)

        # 10. 会话恢复 & 关闭标签页记录
        self._closed_tabs = []  # 最近关闭的标签页 [{"url": ..., "title": ...}, ...]
        self._pinned_tabs = set()  # 固定的标签页 widget id 集合
        reopen_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        reopen_tab_shortcut.activated.connect(self.reopen_closed_tab)

        # 初始化时，先清空可能存在的缓存以解决某些情况下的网页打不开
        QWebEngineProfile.defaultProfile().clearHttpCache()

        # 会话恢复：如果设置允许且存在上次会话，则恢复
        restore_session = self.settings.get("restore_session", True)
        if restore_session and SessionManager.has_session():
            self._restore_session()
        else:
            # 默认初始标签页
            self.add_new_tab(QUrl("https://www.bing.com"), "Homepage")

        # 11. 快捷键系统
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(
            lambda: self.add_new_tab(QUrl("https://www.bing.com"), "New Tab")
        )

        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(
            lambda: self.close_tab(self.tabs.currentIndex())
        )

        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.switch_to_next_tab)

        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.switch_to_prev_tab)

        focus_url_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_url_shortcut.activated.connect(self.focus_url_bar)

        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.navigate_reload)

        stop_shortcut = QShortcut(QKeySequence("Esc"), self)
        stop_shortcut.activated.connect(self.stop_page_loading)

        bookmark_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        bookmark_shortcut.activated.connect(self.save_bookmark)

        history_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        history_shortcut.activated.connect(self.show_history)

        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.activated.connect(self.show_shortcuts_help)

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

        self._build_bookmark_menu(self.bookmark_menu, bookmarks)

        if bookmarks:
            self.bookmark_menu.addSeparator()

        manage_action = QAction("Manage Bookmarks...", self)
        manage_action.triggered.connect(self.show_bookmark_manager)
        self.bookmark_menu.addAction(manage_action)

    def _build_bookmark_menu(self, menu, items):
        """递归构建书签菜单，包含文件夹子菜单"""
        for item in items:
            if item.get("type") == "folder":
                submenu = menu.addMenu(item["name"])
                self._build_bookmark_menu(submenu, item.get("children", []))
            elif item.get("type") == "bookmark":
                action = QAction(item.get("title", item.get("url", "")), self)
                url = item.get("url", "")
                action.triggered.connect(
                    lambda checked, u=url: self.load_in_current_tab(u)
                )
                menu.addAction(action)

    def load_in_current_tab(self, url):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl(url))
        else:
            self.add_new_tab(QUrl(url), "Bookmark")

    def show_bookmark_manager(self):
        dlg = BookmarkManagerDialog(self)
        dlg.exec()
        # 刷新菜单（对话框关闭后可能有变更）
        self.update_bookmark_menu()

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
            # 固定标签页使用短标题 + 图钉图标
            if id(browser) in self._pinned_tabs:
                short_title = title[:8] + "..." if len(title) > 8 else title
                self.tabs.setTabText(index, f"\U0001f4cc {short_title}")
            else:
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
        # 更新缩放标签
        zoom = self._tab_zoom_factors.get(id(widget), 1.0)
        self._update_zoom_label(zoom)

    def close_tab(self, i):
        widget = self.tabs.widget(i)
        if widget and id(widget) in self._pinned_tabs:
            self.statusBar().showMessage(
                "Cannot close a pinned tab. Unpin it first.", 2000
            )
            return

        if self.tabs.count() <= 1:
            # 如果是最后一个标签页，不关闭窗口，而是跳转到主页并重置状态
            widget = self.tabs.widget(i)
            # 保存关闭的标签页信息以便恢复
            url_str = widget.url().toString()
            if url_str and url_str != "about:blank":
                self._closed_tabs.append(
                    {
                        "url": url_str,
                        "title": self.tabs.tabText(i),
                    }
                )
            widget.setUrl(QUrl("about:blank"))  # 或者跳主页
            self.tabs.setTabText(i, "New Tab")
            self.tabs.setTabIcon(i, QIcon())
            return

        widget = self.tabs.widget(i)
        # 保存关闭的标签页信息以便恢复
        url_str = widget.url().toString()
        if url_str and url_str != "about:blank":
            self._closed_tabs.append(
                {
                    "url": url_str,
                    "title": self.tabs.tabText(i),
                }
            )
        self.tabs.removeTab(i)
        self._tab_zoom_factors.pop(id(widget), None)
        widget.deleteLater()

    def show_tab_context_menu(self, point):
        index = self.tabs.tabBar().tabAt(point)
        if index == -1:
            return

        menu = QMenu(self)
        widget = self.tabs.widget(index)
        is_pinned = widget and id(widget) in self._pinned_tabs

        # 固定/取消固定标签页
        if is_pinned:
            unpin_action = QAction("Unpin Tab", self)
            unpin_action.triggered.connect(lambda: self.unpin_tab(index))
            menu.addAction(unpin_action)
        else:
            pin_action = QAction("Pin Tab", self)
            pin_action.triggered.connect(lambda: self.pin_tab(index))
            menu.addAction(pin_action)

        menu.addSeparator()

        close_action = QAction("Close Tab", self)
        close_action.triggered.connect(lambda: self.close_tab(index))
        if is_pinned:
            close_action.setEnabled(False)
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

    # ---- 标签页固定 ----

    def pin_tab(self, index):
        """固定标签页：移到最左侧，缩短标题，标记为固定"""
        widget = self.tabs.widget(index)
        if not widget or id(widget) in self._pinned_tabs:
            return

        self._pinned_tabs.add(id(widget))

        # 计算应插入的位置：所有已固定标签页之后
        pin_count = self._pinned_tab_count()
        target_index = pin_count - 1  # 刚加入集合，所以 -1 就是最后一个固定位置

        # 移动标签页到固定区域末尾
        if index != target_index:
            self.tabs.tabBar().moveTab(index, target_index)

        # 更新标签外观
        self._update_pinned_tab_appearance(target_index, widget, pinned=True)

    def unpin_tab(self, index):
        """取消固定标签页"""
        widget = self.tabs.widget(index)
        if not widget or id(widget) not in self._pinned_tabs:
            return

        self._pinned_tabs.discard(id(widget))

        # 移到固定区域之后（即当前固定标签页数量的位置）
        pin_count = self._pinned_tab_count()
        if index < pin_count:
            self.tabs.tabBar().moveTab(index, pin_count)
            index = pin_count

        # 恢复完整标题
        self._update_pinned_tab_appearance(index, widget, pinned=False)

    def _pinned_tab_count(self):
        """返回当前固定标签页的数量"""
        count = 0
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w and id(w) in self._pinned_tabs:
                count += 1
        return count

    def _update_pinned_tab_appearance(self, index, widget, pinned):
        """更新固定/非固定标签页的外观"""
        if pinned:
            # 显示图钉图标 + 缩短的标题
            title = widget.title() if widget.title() else self.tabs.tabText(index)
            short_title = title[:8] + "..." if len(title) > 8 else title
            self.tabs.setTabText(index, f"\U0001f4cc {short_title}")
        else:
            # 恢复完整标题
            title = widget.title() if widget.title() else "New Tab"
            self.tabs.setTabText(index, title)

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

    # ---- 页面缩放功能 ----

    def zoom_in(self):
        """放大当前标签页"""
        browser = self.tabs.currentWidget()
        if browser:
            current = browser.zoomFactor()
            new_zoom = min(current + 0.1, 5.0)
            browser.setZoomFactor(new_zoom)
            self._tab_zoom_factors[id(browser)] = new_zoom
            self._update_zoom_label(new_zoom)

    def zoom_out(self):
        """缩小当前标签页"""
        browser = self.tabs.currentWidget()
        if browser:
            current = browser.zoomFactor()
            new_zoom = max(current - 0.1, 0.25)
            browser.setZoomFactor(new_zoom)
            self._tab_zoom_factors[id(browser)] = new_zoom
            self._update_zoom_label(new_zoom)

    def zoom_reset(self):
        """重置当前标签页缩放为 100%"""
        browser = self.tabs.currentWidget()
        if browser:
            browser.setZoomFactor(1.0)
            self._tab_zoom_factors[id(browser)] = 1.0
            self._update_zoom_label(1.0)

    def _update_zoom_label(self, factor):
        """更新状态栏中的缩放比例显示"""
        self.zoom_label.setText(f"{int(factor * 100)}%")

    # ---- 全屏浏览模式 ----

    def toggle_fullscreen(self):
        """切换全屏/正常模式"""
        if self._is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        """进入全屏模式"""
        self._is_fullscreen = True
        self._nav_bar.hide()
        self.tabs.tabBar().hide()
        self.menuBar().hide()
        self.statusBar().hide()
        self.showFullScreen()

        # 显示退出提示
        self._show_fullscreen_tip()

    def exit_fullscreen(self):
        """退出全屏模式"""
        self._is_fullscreen = False
        self._nav_bar.show()
        self.tabs.tabBar().show()
        self.menuBar().show()
        self.statusBar().show()
        self.showNormal()
        self._fullscreen_tip.hide()
        self._fullscreen_tip_timer.stop()

    def _show_fullscreen_tip(self):
        """显示全屏提示，3 秒后自动消失"""
        self._fullscreen_tip.adjustSize()
        # 居中显示
        x = (self.width() - self._fullscreen_tip.width()) // 2
        y = 50
        self._fullscreen_tip.move(x, y)
        self._fullscreen_tip.show()
        self._fullscreen_tip.raise_()
        self._fullscreen_tip_timer.start(3000)

    def mouseMoveEvent(self, event):
        """全屏模式下鼠标移到顶部时暂时显示工具栏"""
        super().mouseMoveEvent(event)
        if self._is_fullscreen:
            if event.pos().y() <= 5:
                self._nav_bar.show()
                self.tabs.tabBar().show()
                self.menuBar().show()
            elif event.pos().y() > 100:
                self._nav_bar.hide()
                self.tabs.tabBar().hide()
                self.menuBar().hide()

    # ---- 查看页面源代码 ----

    def view_page_source(self):
        """获取当前页面的 HTML 源代码并显示"""
        browser = self.tabs.currentWidget()
        if not browser:
            return
        title = browser.title()
        browser.page().toHtml(lambda html: self._show_source_dialog(html, title))

    def _show_source_dialog(self, html, title):
        """在对话框中展示源代码"""
        dlg = SourceViewDialog(html, title, self)
        dlg.exec()

    # ---- 页面内查找 ----

    def show_find_bar(self):
        """显示页面内查找栏"""
        self._find_bar.show_bar()

    # ---- User-Agent 切换 ----

    def set_user_agent(self, ua_name):
        """切换 User-Agent 并保存设置"""
        # 更新 action group 的选中状态
        for action in self._ua_action_group:
            action.setChecked(action.text() == ua_name)
        self._apply_user_agent(ua_name)
        # 持久化
        self.settings["user_agent"] = ua_name
        SettingsManager.save_settings(self.settings)

    def set_custom_user_agent(self):
        """弹出对话框让用户输入自定义 User-Agent"""
        current_profile_ua = QWebEngineProfile.defaultProfile().httpUserAgent()
        text, ok = QInputDialog.getText(
            self,
            "Custom User-Agent",
            "Enter User-Agent string:",
            text=current_profile_ua,
        )
        if ok and text.strip():
            custom_name = "Custom"
            self._user_agents[custom_name] = text.strip()
            # 取消所有预设的选中
            for action in self._ua_action_group:
                action.setChecked(False)
            self._apply_user_agent(custom_name)
            self.settings["user_agent"] = custom_name
            self.settings["user_agent_custom_string"] = text.strip()
            SettingsManager.save_settings(self.settings)

    def _apply_user_agent(self, ua_name):
        """将指定的 User-Agent 应用到默认 profile"""
        ua_string = self._user_agents.get(ua_name, "")
        if ua_name == "Custom":
            ua_string = self.settings.get("user_agent_custom_string", "")
        if ua_string:
            QWebEngineProfile.defaultProfile().setHttpUserAgent(ua_string)
        # 空字符串表示使用默认 UA（不做修改）

    # ---- 设置中心 ----

    def open_settings_dialog(self):
        """打开设置对话框"""
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_settings = dlg.get_settings()
            # 保留之前可能有的额外字段
            self.settings.update(new_settings)
            SettingsManager.save_settings(self.settings)
            self._apply_settings_changes(new_settings)

    def _apply_settings_changes(self, new_settings):
        """将修改后的设置应用到运行中的浏览器"""
        # 搜索引擎
        engine = new_settings.get("search_engine", "Bing")
        if engine in ["Bing", "Google", "Baidu"]:
            self.engine_combo.setCurrentText(engine)

        # User-Agent
        ua_name = new_settings.get("user_agent", "Default (NanoBrowser)")
        self.set_user_agent(ua_name)

        # JavaScript 开关
        js_enabled = new_settings.get("javascript_enabled", True)
        default_settings = QWebEngineProfile.defaultProfile().settings()
        from PyQt6.QtWebEngineCore import QWebEngineSettings

        default_settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, js_enabled
        )

        self.statusBar().showMessage("Settings saved.", 2000)

    # ---- 无痕浏览模式 ----

    def open_incognito_window(self):
        """打开一个新的无痕浏览窗口"""
        window = IncognitoWindow(self)
        self._incognito_windows.append(window)
        window.show()

    # ---- 快捷键功能 ----

    def switch_to_next_tab(self):
        """切换到下一个标签页 (Ctrl+Tab)"""
        current = self.tabs.currentIndex()
        count = self.tabs.count()
        if count > 1:
            self.tabs.setCurrentIndex((current + 1) % count)

    def switch_to_prev_tab(self):
        """切换到上一个标签页 (Ctrl+Shift+Tab)"""
        current = self.tabs.currentIndex()
        count = self.tabs.count()
        if count > 1:
            self.tabs.setCurrentIndex((current - 1) % count)

    def focus_url_bar(self):
        """聚焦到地址栏 (Ctrl+L)"""
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    # ---- 地址栏自动完成 ----

    def _collect_suggestions(self):
        """从历史记录和书签中收集建议列表，返回去重的字符串列表。
        每条格式: "URL  |  Title  |  source" 方便用户辨别来源。
        """
        seen = set()
        suggestions = []

        # 历史记录（最近 500 条，倒序优先显示最近的）
        history = HistoryManager.load_history()
        for item in reversed(history[-500:]):
            url = item.get("url", "")
            title = item.get("title", "")
            if url and url not in seen:
                seen.add(url)
                label = (
                    f"{url}  |  {title}  |  History" if title else f"{url}  |  History"
                )
                suggestions.append(label)

        # 书签（递归展开文件夹）
        bookmarks = BookmarkManager.load_bookmarks()
        self._collect_bookmark_suggestions(bookmarks, suggestions, seen)

        return suggestions

    def _collect_bookmark_suggestions(self, items, suggestions, seen):
        """递归收集书签建议"""
        for item in items:
            if item.get("type") == "folder":
                self._collect_bookmark_suggestions(
                    item.get("children", []), suggestions, seen
                )
            else:
                url = item.get("url", "")
                title = item.get("title", "")
                if url and url not in seen:
                    seen.add(url)
                    label = (
                        f"{url}  |  {title}  |  Bookmark"
                        if title
                        else f"{url}  |  Bookmark"
                    )
                    suggestions.append(label)

    def _refresh_completer_model(self, text):
        """当用户在地址栏输入时刷新自动完成数据"""
        if len(text) < 1:
            return
        # 仅在首次输入或模型为空时重建完整列表（避免每次按键都读文件）
        if not hasattr(self, "_completer_cache") or self._completer_cache is None:
            self._completer_cache = self._collect_suggestions()
            self._completer_model.setStringList(self._completer_cache)
        # 清除缓存的定时器（2秒后自动失效，下次输入会重新加载）
        if hasattr(self, "_completer_timer") and self._completer_timer is not None:
            self._completer_timer.stop()
        self._completer_timer = QTimer()
        self._completer_timer.setSingleShot(True)
        self._completer_timer.timeout.connect(self._invalidate_completer_cache)
        self._completer_timer.start(2000)

    def _invalidate_completer_cache(self):
        """使缓存失效，下次输入时重新加载"""
        self._completer_cache = None

    def _on_completer_activated(self, text):
        """当用户从自动完成下拉列表中选择一项时，提取 URL 并导航"""
        # 格式: "URL  |  Title  |  source"
        url = text.split("  |  ")[0].strip()
        self.url_bar.setText(url)
        self.navigate_to_url()

    def stop_page_loading(self):
        """停止当前页面加载 (Esc)"""
        browser = self.tabs.currentWidget()
        if browser:
            browser.stop()

    def show_shortcuts_help(self):
        """显示快捷键帮助对话框 (F1)"""
        dlg = ShortcutsHelpDialog(self)
        dlg.exec()

    # ---- 打印与PDF功能 ----

    def print_page(self):
        """打印当前页面 (Ctrl+P)"""
        browser = self.tabs.currentWidget()
        if not browser:
            return

        try:
            from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle(f"Print Preview - {browser.title()}")
            preview.paintRequested.connect(lambda p: self._do_print(browser, p))
            preview.exec()
        except ImportError:
            # PyQt6-Qt6-Printing 不可用时，使用简单的 printToPdf 替代
            QMessageBox.information(
                self,
                "Print",
                "Print preview requires PyQt6 printing support.\n"
                "You can use 'Save as PDF' as an alternative.",
            )

    def _do_print(self, browser, printer):
        """执行打印（print preview 回调）"""
        # 使用同步方式打印：printToPdf 后由 QPrintPreviewDialog 处理
        # 实际打印通过 page().print()
        try:
            browser.page().print(printer, lambda ok: None)
        except Exception:
            pass

    def save_as_pdf(self):
        """将当前页面保存为 PDF 文件"""
        browser = self.tabs.currentWidget()
        if not browser:
            return

        title = browser.title() or "page"
        # 清理文件名中的非法字符
        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save as PDF",
            f"{safe_title}.pdf",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if not filepath:
            return

        browser.page().printToPdf(filepath)
        self.statusBar().showMessage(f"Saved PDF: {os.path.basename(filepath)}", 3000)

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

    # ---- 会话恢复功能 ----

    def _restore_session(self):
        """从 session.json 恢复上次打开的标签页"""
        tabs_data, active_index = SessionManager.load_session()
        if not tabs_data:
            self.add_new_tab(QUrl("https://www.bing.com"), "Homepage")
            return

        for tab_info in tabs_data:
            url = tab_info.get("url", "")
            title = tab_info.get("title", "Loading...")
            pinned = tab_info.get("pinned", False)
            if url and url != "about:blank":
                browser = self.add_new_tab(QUrl(url), title)
                if pinned and browser:
                    idx = self.tabs.indexOf(browser)
                    if idx != -1:
                        self.pin_tab(idx)

        # 如果没有恢复任何标签页，打开默认页面
        if self.tabs.count() == 0:
            self.add_new_tab(QUrl("https://www.bing.com"), "Homepage")
        elif 0 <= active_index < self.tabs.count():
            self.tabs.setCurrentIndex(active_index)

    def _save_session(self):
        """保存当前所有标签页到 session.json"""
        tabs_data = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if widget:
                url_str = widget.url().toString()
                title = self.tabs.tabText(i)
                if url_str and url_str != "about:blank":
                    tab_info = {"url": url_str, "title": title}
                    if id(widget) in self._pinned_tabs:
                        tab_info["pinned"] = True
                    tabs_data.append(tab_info)

        active_index = self.tabs.currentIndex()
        SessionManager.save_session(tabs_data, active_index)

    def reopen_closed_tab(self):
        """重新打开最近关闭的标签页 (Ctrl+Shift+T)"""
        if not self._closed_tabs:
            self.statusBar().showMessage("No recently closed tabs.", 2000)
            return

        tab_info = self._closed_tabs.pop()
        url = tab_info.get("url", "")
        title = tab_info.get("title", "Restored Tab")
        if url:
            self.add_new_tab(QUrl(url), title)
            self.statusBar().showMessage(f"Restored: {title}", 2000)

    def closeEvent(self, event):
        """关闭窗口时保存会话"""
        self._save_session()
        event.accept()


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
