import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QToolBar, QLineEdit, 
                             QTabWidget, QToolButton)
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NanoBrowser")
        self.setGeometry(100, 100, 1024, 768)

        # 1. 多标签页核心组件 QTabWidget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.setCentralWidget(self.tabs)

        # 2. 导航栏 (QToolBar)
        nav_bar = QToolBar("Navigation")
        self.addToolBar(nav_bar)

        # 后退按钮
        self.back_btn = QAction("Back", self)
        self.back_btn.triggered.connect(self.navigate_back)
        nav_bar.addAction(self.back_btn)

        # 前进按钮
        self.forward_btn = QAction("Forward", self)
        self.forward_btn.triggered.connect(self.navigate_forward)
        nav_bar.addAction(self.forward_btn)

        # 刷新按钮
        self.reload_btn = QAction("Reload", self)
        self.reload_btn.triggered.connect(self.navigate_reload)
        nav_bar.addAction(self.reload_btn)

        # 主页按钮
        self.home_btn = QAction("Home", self)
        self.home_btn.triggered.connect(self.navigate_home)
        nav_bar.addAction(self.home_btn)

        nav_bar.addSeparator()

        # 3. 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # 添加新标签页按钮 ('+')
        new_tab_btn = QAction("+", self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab(QUrl("https://www.bing.com"), "New Tab"))
        nav_bar.addAction(new_tab_btn)

        # 初始标签页
        self.add_new_tab(QUrl("https://www.bing.com"), "Homepage")

    def add_new_tab(self, qurl, label):
        browser = QWebEngineView()
        browser.setUrl(qurl)
        
        # 将网页标题和URL变更事件连接起来
        browser.urlChanged.connect(lambda q: self.update_url_bar(q, browser))
        browser.titleChanged.connect(lambda title: self.update_tab_title(title, browser))

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def update_tab_title(self, title, browser):
        # 找到发出信号的 browser 的 index
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabText(index, title)
            self.setWindowTitle(f"{title} - NanoBrowser")

    def current_tab_changed(self, i):
        # 当没有标签页时，关闭程序或添加新主页
        if i == -1:
            self.close()
            return
            
        # 更新地址栏
        qurl = self.tabs.currentWidget().url()
        self.update_url_bar(qurl, self.tabs.currentWidget())

    def close_tab(self, i):
        # 如果只剩一个标签页则退出，或选择留至少一个
        if self.tabs.count() < 2:
            self.close()
            return
            
        widget = self.tabs.widget(i)
        self.tabs.removeTab(i)
        widget.deleteLater()

    # --- 导航栏动作，始终作用于当前的标签页 ---
    def navigate_home(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl("https://www.bing.com"))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl(url))

    def update_url_bar(self, qurl, browser=None):
        # 只有当发出信号的browser是当前活动browser时才更新地址栏
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
