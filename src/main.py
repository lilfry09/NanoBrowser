import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QStyle
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NanoBrowser")
        self.setGeometry(100, 100, 1024, 768)

        # 1. 核心 WebView 组件
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.bing.com"))
        self.setCentralWidget(self.browser)

        # 2. 导航栏 (QToolBar)
        nav_bar = QToolBar("Navigation")
        self.addToolBar(nav_bar)

        # 后退按钮
        back_btn = QAction("Back", self)
        back_btn.triggered.connect(self.browser.back)
        nav_bar.addAction(back_btn)

        # 前进按钮
        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(self.browser.forward)
        nav_bar.addAction(forward_btn)

        # 刷新按钮
        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(self.browser.reload)
        nav_bar.addAction(reload_btn)

        # 主页按钮
        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.navigate_home)
        nav_bar.addAction(home_btn)

        nav_bar.addSeparator()

        # 3. 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # 绑定网页加载完成或网址改变事件更新地址栏
        self.browser.urlChanged.connect(self.update_url_bar)

    def navigate_home(self):
        self.browser.setUrl(QUrl("https://www.bing.com"))

    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))

    def update_url_bar(self, qurl):
        self.url_bar.setText(qurl.toString())


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
