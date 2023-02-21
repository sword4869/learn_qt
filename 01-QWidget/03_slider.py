import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSlider, QVBoxLayout, QWidget


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        slider = QSlider(Qt.Horizontal) # 横向的滑动条
        # slider = QSlider(Qt.Vertical)   # 纵向的滑动条
        slider.setMinimum(1)    # 最小值
        slider.setMaximum(100)  # 最大值
        slider.setValue(25)     # 滑动条的位置

        # 信号 clicked 绑定 slot
        slider.valueChanged.connect(self.valued_change_event)
        slider.show()

        # 加入到布局中
        layout = QVBoxLayout()
        layout.addWidget(slider)
        self.setLayout(layout)
    
    def valued_change_event(self, data):
        print('slider value', data)

app = QApplication(sys.argv)
window = MyWidget()
window.show()
app.exec()