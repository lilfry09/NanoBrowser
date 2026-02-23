import sys
from PyQt6.QtWidgets import QApplication
from src.main import MainWindow

def test_startup():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # 模拟等待 5 秒，然后正常退出
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(5000, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    test_startup()
