import sys

from PySide6.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout,
                               QWidget)


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Hello")

        # 改变 label 内容的按钮
        button1 = QPushButton('button1')
        button1.clicked.connect(self.click_event)
        button1.show()

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(button1)
        self.setLayout(layout)

    def click_event(self):
        self.label.setText("World")

app = QApplication(sys.argv)
window = MyWidget()
window.show()
app.exec()