import sys
import time

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QHBoxLayout, QWidget


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        ###### 按钮1
        # 设置文字，方式1
        button1 = QPushButton("no value")

        # 信号 Signal 绑定 Slot
        button1.clicked.connect(self.slot_clicked)        # 点击
        button1.pressed.connect(self.slot_pressed)          # 按下按钮
        button1.released.connect(self.slot_released)        # 释放按钮
        button1.show()

        ###### 按钮2
        self.button2 = QPushButton()
        # 设置文字，方式2
        self.button2.setText("on")
        self.button2.setCheckable(True)
        self.button2.clicked.connect(self.slot_on_off)   # 切换 on-off 状态

        self.button2.show()

        ###### 按钮3,4,5
        local_layout_btn345 = QHBoxLayout()
        self.button3 = QPushButton('btn3')
        self.button4 = QPushButton('Disable btn3')
        self.button5 = QPushButton('Enable btn3')
        self.button4.clicked.connect(self.slot_disable)   # 让 button3 不可按   
        self.button5.clicked.connect(self.slot_enable)   # 让 button3 可用 
        local_layout_btn345.addWidget(self.button3)
        local_layout_btn345.addWidget(self.button4)
        local_layout_btn345.addWidget(self.button5)
         


        # 自定义的组件 MyWidget 要加入到布局中，这样 QMainWindow 中才能调用 MyWidget
        layout = QVBoxLayout()
        layout.addWidget(button1)
        layout.addWidget(self.button2)
        layout.addLayout(local_layout_btn345)
        self.setLayout(layout)

    def slot_clicked(self):
        print("click the button1")

    # Slot 可以用这个标识，不带也可以
    @Slot()
    def slot_on_off(self, checkable):  # 变量名字随便起
        if checkable:
            self.button2.setText('off')
        else:
            self.button2.setText('on')

        print("button2 checkable - way 1", checkable)
        print("button2 checkable - way 2", self.button2.isChecked())  # 或者直接从 button 获取

    def slot_released(self):
        print('button 2 is released')

    def slot_pressed(self):
        print('button 2 is pressed')

    def slot_disable(self):
        self.button3.setEnabled(False)

    def slot_enable(self):
        self.button3.setEnabled(True)
        





app = QApplication(sys.argv)
window = MyWidget()
window.show()
app.exec()
