import sys
import wave

from PySide6.QtCore import QByteArray
from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget


class MyWidget(QWidget):
    def __init__(self):
        ###
        # QMediaDevices → QAudioDevice
        # QAudioSource(QAudioDevice, QAudioFormat)
        # QAudioSource.start() → QIODevice
        ###
        super().__init__()

        # QMediaDevices
        self.media_devices = QMediaDevices(self)

        # QAudioDevice
        self.audio_device = self.media_devices.defaultAudioInput()

        # QAudioFormat
        self.audio_format = QAudioFormat()
        self.audio_format = QAudioFormat()
        self.audio_format.setSampleRate(16000)     # 采样频率
        self.audio_format.setChannelCount(1)       # 通道数
        self.audio_format.setSampleFormat(QAudioFormat.Int16)  # 采样格式，QAudioFormat.UInt8，QAudioFormat.Int16

        # QAudioSource
        self.audio_source = QAudioSource(self.audio_device, self.audio_format)

        # QIODevice
        # io_device = self.audio_source.start()

        # 存储录音内容
        self.buffer = QByteArray()

        button1 = QPushButton('start')
        button1.clicked.connect(self.click_start)
        button1.show()

        button2 = QPushButton('stop')
        button2.clicked.connect(self.click_stop)
        button2.show()

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(button1)
        layout.addWidget(button2)
        self.setLayout(layout)

    def click_start(self):
        io_device = self.audio_source.start()

        def push_mode_slot():
            length = self.audio_source.bytesAvailable()
            # 这是个缓存机制，保证实时性
            buffer_size = 4096
            # length = min(length, buffer_size)
            if length > buffer_size:
                length = buffer_size
            # 从 QIODevice 中读取
            buffer: QByteArray = io_device.read(length)
            # 实时事件
            if length > 0:
                self.buffer.append(buffer)
        
        # io_device 准备好连接
        io_device.readyRead.connect(push_mode_slot)

    def click_stop(self):
        self.audio_source.stop()

        if self.buffer.size() != 0:
            audio_path = 'test/test.wav'
            wf = wave.open(audio_path, 'wb')
            wf.setframerate(16000)
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.writeframes(self.buffer)
            wf.close()

            self.buffer.clear()

        

app = QApplication(sys.argv)
window = MyWidget()
window.show()
app.exec()