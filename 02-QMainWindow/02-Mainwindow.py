# version of function
'''
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton

import sys

app = QApplication(sys.argv)

window = QMainWindow()
# 窗口标题
window.setWindowTitle('Window')

'加入按钮'
button = QPushButton()
button.setText('Press')
# 放到窗口中间
window.setCentralWidget(button)

window.show()
app.exec()
'''


# version of class

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 会覆盖 app.setApplicationName("QApp")
        # self.setWindowTitle('Window')


        '加入按钮'
        button = QPushButton()
        button.setText('Press')
        # 放到窗口中间
        self.setCentralWidget(button)
    

app = QApplication(sys.argv)
app.setApplicationName("QApp")


# 继承 QMainWindow 的 MainWindow
window = MainWindow()

window.show()
app.exec()