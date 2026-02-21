import sys
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QToolBar, QLineEdit, 
                             QTabWidget, QDialog, QVBoxLayout, QListWidget, QMessageBox, QMenu)
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QAction
from history_manager import HistoryManager
from bookmark_manager import BookmarkManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NanoBrowser")
        self.setGeometry(100, 100, 1024, 768)

        # 默认搜索引擎设置
        self.search_engine = "https://www.bing.com/search?q={}"

        # 1. 多标签页组件
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # 2. 导航栏
        nav_bar = QToolBar("Navigation")
        self.addToolBar(nav_bar)

        self.back_btn = QAction("Back", self)
        self.back_btn.triggered.connect(self.navigate_back)
        nav_bar.addAction(self.back_btn)

        self.forward_btn = QAction("Forward", self)
        self.forward_btn.triggered.connect(self.navigate_forward)
        nav_bar.addAction(self.forward_btn)

        self.reload_btn = QAction("Reload", self)
        self.reload_btn.triggered.connect(self.navigate_reload)
        nav_bar.addAction(self.reload_btn)

        self.home_btn = QAction("Home", self)
        self.home_btn.triggered.connect(self.navigate_home)
        nav_bar.addAction(self.home_btn)

        nav_bar.addSeparator()

        # 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # 收藏按钮
        bookmark_btn = QAction("★", self)
        bookmark_btn.triggered.connect(self.save_bookmark)
        nav_bar.addAction(bookmark_btn)

        # 新建标签页
        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab(QUrl("https://www.bing.com"), "New Tab"))
        nav_bar.addAction(new_tab_btn)

        # 历史记录按钮
        history_btn = QAction("History", self)
        history_btn.triggered.connect(self.show_history)
        nav_bar.addAction(history_btn)
        
        # 3. 书签栏 / 菜单
        self.bookmark_menu = self.menuBar().addMenu("Bookmarks")
        self.update_bookmark_menu()

        # 初始标签页
        self.add_new_tab(QUrl("https://www.bing.com"), "Homepage")

    def update_bookmark_menu(self):
        self.bookmark_menu.clear()
        bookmarks = BookmarkManager.load_bookmarks()
        for bm in bookmarks:
            action = QAction(bm["title"], self)
            action.triggered.connect(lambda checked, url=bm["url"]: self.add_new_tab(QUrl(url), "Bookmark"))
            self.bookmark_menu.addAction(action)

    def save_bookmark(self):
        if self.tabs.currentWidget():
            url = self.tabs.currentWidget().url().toString()
            title = self.tabs.tabText(self.tabs.currentIndex())
            if BookmarkManager.add_bookmark(url, title):
                QMessageBox.information(self, "Success", f"Saved: {title}")
                self.update_bookmark_menu()
            else:
                QMessageBox.warning(self, "Warning", "Already bookmarked or failed to save.")

    def show_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("History")
        dlg.resize(400, 300)
        layout = QVBoxLayout()
        list_widget = QListWidget()
        
        history = HistoryManager.load_history()
        for item in reversed(history):
            list_widget.addItem(f"{item['time']} - {item['title']} ({item['url']})")
            
        layout.addWidget(list_widget)
        dlg.setLayout(layout)
        dlg.exec()

    def add_new_tab(self, qurl, label):
        browser = QWebEngineView()
        browser.setUrl(qurl)
        
        browser.urlChanged.connect(lambda q: self.update_url_bar(q, browser))
        browser.titleChanged.connect(lambda title: self.update_tab_title(title, browser))
        browser.loadFinished.connect(lambda ok: self.on_load_finished(ok, browser))

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def on_load_finished(self, ok, browser):
        if ok:
            url = browser.url().toString()
            title = browser.title()
            HistoryManager.add_history(url, title)

    def update_tab_title(self, title, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabText(index, title)
            self.setWindowTitle(f"{title} - NanoBrowser")

    def current_tab_changed(self, i):
        if i == -1:
            self.close()
            return
        qurl = self.tabs.currentWidget().url()
        self.update_url_bar(qurl, self.tabs.currentWidget())

    def close_tab(self, i):
        if self.tabs.count() < 2:
            self.close()
            return
        widget = self.tabs.widget(i)
        self.tabs.removeTab(i)
        widget.deleteLater()

    def navigate_home(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl("https://www.bing.com"))

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        # 简单判断是否是网址格式 (包含 . 的非纯数字 或 以 http 开始)
        is_url = re.match(r'^(http://|https://)', text) or ('.' in text and not ' ' in text)
        
        if is_url:
            if not text.startswith("http://") and not text.startswith("https://"):
                text = "https://" + text
            url = text
        else:
            # 不是网址，调用搜索引擎
            url = self.search_engine.format(text)
            
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl(url))

    def update_url_bar(self, qurl, browser=None):
        if browser == self.tabs.currentWidget():
            self.url_bar.setText(qurl.toString())
            self.url_bar.setCursorPosition(0)

    def navigate_back(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().back()

    def navigate_forward(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().forward()

    def navigate_reload(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().reload()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
