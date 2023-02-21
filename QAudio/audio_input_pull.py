# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""
PySide6 port of Qt6 example examples/multimedia/audiosources

Audio Devices demonstrates how to create a simple application to list and test
the configuration for the various audio devices available on the target device
or desktop PC.

Note: This Python example is not fully complete as compared to its C++ counterpart.
Only the push mode works at the moment. For the pull mode to work, the class
QIODevice have python bindings that needs to be fixed.
"""

import sys
from typing import Optional

import PySide6
from PySide6.QtCore import QByteArray, QMargins, Qt, Slot
from PySide6.QtGui import QPainter, QPalette
from PySide6.QtMultimedia import (QAudio, QAudioDevice, QAudioFormat,
                                  QAudioSource, QMediaDevices)
from PySide6.QtWidgets import (QApplication, QComboBox, QPushButton, QSlider,
                               QVBoxLayout, QHBoxLayout, QWidget)


class AudioInfo:
    def __init__(self, format: QAudioFormat):
        super().__init__()
        self.channel_bytes: int = int(format.bytesPerSample())          # 一个采样的字节数
        self.sample_bytes: int = int(format.bytesPerFrame())            # 一帧的字节数
        self.channel_count = format.channelCount()                      # 通道数
        self.normalizedSampleValue = format.normalizedSampleValue       # 归一化到-1到1
        self.sample_rate = format.sampleRate()                          # 采样频率


    def calculate_level(self, data: bytes, length: int) -> float:
        ''' 
        data是音频
        length就是len(data)音频的总字节数 
        '''

        # print(channel_bytes,sample_bytes,length , num_samples)
        # 2 2 640 320
        # 2 2 3200 1600

        num_samples: int = int(length / self.sample_bytes)                   # 音频的总字节数 / 一帧的字节数 = 音频的总帧数


        maxValue: float = 0
        m_offset: int = 0

        for i in range(num_samples):    # 遍历data的每帧
            for j in range(self.channel_count):   # 遍历每个通道
                value = 0
                if len(data) > m_offset:
                    data_sample = data[m_offset:]   # data从头到尾
                    value = self.normalizedSampleValue(data_sample)
                maxValue = max(value, maxValue)
                m_offset = m_offset + self.channel_bytes
        return maxValue


class RenderArea(QWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.m_level = 0
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        self.setMinimumHeight(30)
        self.setMinimumWidth(200)

    def set_level(self, value):
        self.m_level = value
        self.update()

    def paintEvent(self, event: PySide6.QtGui.QPaintEvent) -> None:
        with QPainter(self) as painter:
            painter.setPen(Qt.black)
            frame = painter.viewport() - QMargins(10, 10, 10, 10)

            painter.drawRect(frame)

            if self.m_level == 0.0:
                return

            pos: int = round((frame.width() - 1) * self.m_level)
            painter.fillRect(
                frame.left() + 1, frame.top() + 1, pos, frame.height() - 1, Qt.red
            )



class InputTest(QWidget):
    # 音频格式
    audio_format = QAudioFormat()
    audio_format.setSampleRate(16000)     # 采样频率
    audio_format.setChannelCount(1)       # 通道数
    audio_format.setSampleFormat(QAudioFormat.Int16)  # 采样格式

    def __init__(self) -> None:
        super().__init__()
        self.media_devices = QMediaDevices(self)
        self.m_pullMode = False


        self.initialize_window()
        self.initialize_audio(self.media_devices.defaultAudioInput())

    def initialize_window(self):
        self.layout = QHBoxLayout(self)

        ### 监测声音状态条
        self.m_canvas = RenderArea(self)
        self.layout.addWidget(self.m_canvas)

        ### 设备多选框
        self.m_device_box = QComboBox(self)
        # 默认设备
        default_audio_input = self.media_devices.defaultAudioInput()
        self.m_device_box.addItem(
            default_audio_input.description(), default_audio_input
        )
        # 其他设备
        for audio_input in self.media_devices.audioInputs():
            if default_audio_input != audio_input:
                self.m_device_box.addItem(audio_input.description(), audio_input)

        self.m_device_box.activated[int].connect(self.device_changed)
        self.layout.addWidget(self.m_device_box)

        ### 调节音量大小的滑动条
        self.m_volume_slider = QSlider(Qt.Horizontal, self)
        self.m_volume_slider.setRange(0, 100)
        self.m_volume_slider.setValue(100)
        self.m_volume_slider.valueChanged.connect(self.slider_changed)
        self.layout.addWidget(self.m_volume_slider)

        # pull mode button
        self.m_mode_button = QPushButton(self)
        self.m_mode_button.clicked.connect(self.toggle_mode)
        self.layout.addWidget(self.m_mode_button)

        # 暂停/恢复
        self.m_suspend_resume_button = QPushButton(self)
        self.m_suspend_resume_button.clicked.connect(self.toggle_suspend)
        self.layout.addWidget(self.m_suspend_resume_button)

    def initialize_audio(self, audio_device: QAudioDevice):
        ##### 音频信息 AudioInfo
        self.m_audio_info = AudioInfo(self.audio_format)

        ##### 音频输入 QAudioSource
        # 绑定音频设备和音频格式
        self.audio_source = QAudioSource(audio_device, self.audio_format)
        # 将声音的音量和slider联系在一起
        initial_volume = QAudio.convertVolume(
            self.audio_source.volume(),
            QAudio.LinearVolumeScale,
            QAudio.LogarithmicVolumeScale,
        )
        self.m_volume_slider.setValue(int(round(initial_volume * 100)))
        self.toggle_mode()

    @Slot()
    def toggle_mode(self):
        # 停止输入
        self.audio_source.stop()
        # 从 StoppedState 激活到 ActivateState
        self.toggle_suspend()

        self.m_mode_button.setText("Enable pull mode")

        # io
        # 输入启动
        io = self.audio_source.start()

        def push_mode_slot():
            len = self.audio_source.bytesAvailable()
            # 这是个缓存机制，保证实时性
            buffer_size = 4096
            # len = min(len, buffer_size)
            if len > buffer_size:
                len = buffer_size
            # 读取
            buffer: QByteArray = io.read(len)
            # 实时事件
            if len > 0:
                level = self.m_audio_info.calculate_level(buffer, len)
                self.m_canvas.set_level(level)
        # io准备好连接
        io.readyRead.connect(push_mode_slot)

    @Slot()
    def toggle_suspend(self):
        # toggle suspend/resume
        state = self.audio_source.state()
        print(state)
        if (state == QAudio.SuspendedState) or (state == QAudio.StoppedState):
            self.audio_source.resume()
            self.m_suspend_resume_button.setText("Suspend recording")
        elif state == QAudio.ActiveState:
            self.audio_source.suspend()
            self.m_suspend_resume_button.setText("Resume recording")
        # else no-op

    @Slot(int)
    def device_changed(self, index):
        ### 解联和重新初始化，是因为 QAudioSource 需要重新绑定音频设备
        # 先停止音频输入
        self.audio_source.stop()
        # 解联
        self.audio_source.disconnect(self)
        # 重新初始化
        self.initialize_audio(self.m_device_box.itemData(index))

    @Slot(int)
    def slider_changed(self, value):
        # 调节音量
        linearVolume = QAudio.convertVolume(
            value / float(100), QAudio.LogarithmicVolumeScale, QAudio.LinearVolumeScale
        )
        self.audio_source.setVolume(linearVolume)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Sources Example")
    input = InputTest()
    input.show()
    app.exec()