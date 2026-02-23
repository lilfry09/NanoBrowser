import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)
window = QMainWindow()
view = QWebEngineView()
# 用一个更简单的测试页面，看是否是网络或者SSL问题
view.setUrl(QUrl("http://example.com"))
window.setCentralWidget(view)
window.show()

sys.exit(app.exec())
