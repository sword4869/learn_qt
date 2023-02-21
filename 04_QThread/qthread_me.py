#!/usr/bin/env python2

import sys
import time

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
                               QVBoxLayout, QWidget)


class MySignal(QObject):
    sig = Signal(str)


class MyThread(QThread):
    def __init__(self):
        super().__init__()
        self.exiting = False

    def run(self):
        while self.exiting:
            sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1)


class MyLongThread(QThread):
    def __init__(self):
        super().__init__()
        self.exiting = False
        self.signal = MySignal()

    def run(self):
        end = time.time() + 10
        while self.exiting == False:
            sys.stdout.write("*")
            sys.stdout.flush()
            time.sleep(1)
            now = time.time()
            if now >= end:
                self.exiting = True
        self.signal.sig.emit("OK")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        centralwidget = QWidget(self)

        self.batchbutton = QPushButton("Start batch")
        self.batchbutton.clicked.connect(self.handletoggle)

        self.longbutton = QPushButton("Start long (10 seconds) operation")
        self.longbutton.clicked.connect(self.longoperation)
        
        self.label1 = QLabel("Continuos batch")
        self.label2 = QLabel("Long batch")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.batchbutton)
        self.layout.addWidget(self.longbutton)
        self.layout.addWidget(self.label1)
        self.layout.addWidget(self.label2)
        centralwidget.setLayout(self.layout)

        self.thread = MyThread()
        self.thread.started.connect(self.started)
        self.thread.finished.connect(self.finished)
        
        self.longthread = MyLongThread()
        self.longthread.signal.sig.connect(self.longoperationcomplete)

        self.setCentralWidget(centralwidget)
        


    def started(self):
        self.label1.setText("Continuous batch started")

    def finished(self):
        self.label1.setText("Continuous batch stopped")

    def handletoggle(self):
        if self.thread.isRunning(): # 线程正在执行
            self.thread.exiting = False
            self.batchbutton.setEnabled(False)
            while self.thread.isRunning():
                time.sleep(0.01)
                continue
            self.batchbutton.setText("Start batch")
            self.batchbutton.setEnabled(True)
        else:
            self.thread.exiting = True
            self.thread.start()
            self.batchbutton.setEnabled(False)
            while not self.thread.isRunning():
                time.sleep(0.01)
                continue
            self.batchbutton.setText("Stop batch")
            self.batchbutton.setEnabled(True)

    def longoperation(self):
        if not self.longthread.isRunning():
            self.longthread.exiting = False
            self.longthread.start()
            self.label2.setText("Long operation started")
            self.longbutton.setEnabled(False)

    def longoperationcomplete(self, data):
        self.label2.setText("Long operation completed with: " + data)
        self.longbutton.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
