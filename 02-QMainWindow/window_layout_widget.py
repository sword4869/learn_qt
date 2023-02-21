'''
### QMainWindow 套 QWidget 的 layout

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QSlider, QVBoxLayout
from PySide6.QtCore import Qt

import sys
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        button1 = QPushButton('change window title')
        button1.show()

        layout = QVBoxLayout()
        layout.addWidget(button1)
        self.setLayout(layout)
    
    def slot_change_window_title(self):
        self.setWindowTitle('hello')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 窗口标题
        self.setWindowTitle('Window')

        # 放到窗口中间
        self.setCentralWidget(MyWidget())
    

app = QApplication(sys.argv)

window = MainWindow()

window.show()
app.exec()
'''


### QMainWindow 的 layout 套 QWidget 的 layout

import sys

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget)


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        button1 = QPushButton('change window title')
        button1.clicked.connect(self.slot_change_window_title)
        button1.show()
        layout.addWidget(button1)
        
        self.setLayout(layout)
    
    def slot_change_window_title(self):
        self.setWindowTitle('hello')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        central_widget = QWidget()
        # 布局是建立在中心组件中
        layout = QVBoxLayout(central_widget)
        layout.addWidget(MyWidget())
        layout.addWidget(MyWidget())

        self.setCentralWidget(central_widget)
    

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()