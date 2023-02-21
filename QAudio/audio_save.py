import math
import sys
from typing import Optional

import wave

import numpy as np
from PySide6.QtCore import QByteArray, QMargins, Qt, Slot
from PySide6.QtGui import QPainter, QPaintEvent, QPalette
from PySide6.QtMultimedia import (QAudio, QAudioDevice, QAudioFormat,
                                  QAudioSource, QMediaDevices)
from PySide6.QtWidgets import (QMainWindow, QApplication, QComboBox, QHBoxLayout,
                               QPushButton, QSlider, QVBoxLayout, QWidget)


class AudioInfo:
    def __init__(self, format: QAudioFormat):
        super().__init__()
        self.bytes_per_sample: int = int(format.bytesPerSample())       # 一个采样的字节数
        self.bytes_per_frame: int = int(format.bytesPerFrame())         # 一帧的字节数 = 一个采样的字节数 * 通道数
        self.n_channels = format.channelCount()                         # 通道数
        self.normalizedSampleValue = format.normalizedSampleValue       # 归一化到-1到1
        self.sample_rate = format.sampleRate()                          # 采样频率


    def calculate_level(self, data: bytes) -> float:
        ''' 
        data是音频
        '''
        n_bytes = len(data)
        n_frames: int = int(n_bytes / self.bytes_per_frame)                   # 音频的总字节数 / 一帧的字节数 = 音频的总帧数

        
        # print(self.bytes_per_sample,self.bytes_per_frame,n_bytes , n_frames)


        maxValue: float = 0
        m_offset: int = 0

        # 这样是为了交替声道
        for i in range(n_frames):    # 遍历data的每帧
            for j in range(self.n_channels):   # 遍历每个通道
                # 某个声道音量
                value = 0
                if n_bytes > m_offset:
                    data_sample = data[m_offset:]   # data从头到尾
                    value = self.normalizedSampleValue(data_sample)
                maxValue = max(value, maxValue)
                # 加bytes_per_sample是对的，因为一帧的字节数 = 一个采样的字节数 * 通道数
                m_offset = m_offset + self.bytes_per_sample
        return maxValue

    # from http://stackoverflow.com/questions/13728392/moving-average-or-running-mean
    def running_mean(self, x, windowSize):
        cumsum = np.cumsum(np.insert(x, 0, 0)) 
        return (cumsum[windowSize:] - cumsum[:-windowSize]) / windowSize

    def filter(self, data: bytes):
        

        if self.bytes_per_sample == 1:
            dtype = np.uint8 # unsigned char
        elif self.bytes_per_sample == 2:
            dtype = np.int16 # signed 2-byte short
        else:
            raise ValueError("Only supports 8 and 16 bit audio formats.")

        signal_array = np.frombuffer(data, dtype=dtype)


        # get window size
        # from http://dsp.stackexchange.com/questions/9966/what-is-the-cut-off-frequency-of-a-moving-average-filter
        cutOffFrequency = 400.0
        freqRatio = cutOffFrequency / self.sample_rate
        N = int(math.sqrt(0.196196 + freqRatio**2) / freqRatio)

        # Use moviung average (only on first channel)
        filtered = self.running_mean(signal_array, N).astype(signal_array.dtype)
        alter_bytes = filtered.tobytes()

        return alter_bytes



class RenderArea(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.m_level = 0
        
        # 用白色填充背景
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        
        # 高宽
        self.setMinimumHeight(30)   # 高度
        self.setMaximumHeight(30)   
        self.setMinimumWidth(200)   # 宽度

    def set_level(self, value):
        self.m_level = value
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        ### 
        # 会自动调用
        # 作用就是画个矩形框，矩形框里再填充红色矩形条
        ###
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



class MyAudioWidget(QWidget):
    # 音频格式
    audio_format = QAudioFormat()
    audio_format.setSampleRate(16000)     # 采样频率
    audio_format.setChannelCount(1)       # 通道数
    audio_format.setSampleFormat(QAudioFormat.Int16)  # 采样格式，QAudioFormat.UInt8，QAudioFormat.Int16
    audio_output_path = 'test/myqt5.wav'


    def __init__(self, parent: QMainWindow = None) -> None:
        super().__init__()

        self.parent = parent
        self.initialize_window()
        self.initialize_audio(self.media_devices.defaultAudioInput())

    def initialize_window(self):
        layout = QHBoxLayout(self)

        ### 监测声音状态条
        self.m_canvas = RenderArea(self)
        layout.addWidget(self.m_canvas)

        ### 设备多选框
        self.m_device_box = QComboBox(self)
        
        ### 媒体
        self.media_devices = QMediaDevices(self)
                
        ## 默认设备与其他设备：方法1
        # for audio_input in self.media_devices.audioInputs():
        #     self.m_device_box.addItem(audio_input.description(), audio_input)
        # default_audio_input = self.media_devices.audioInputs()[0]
        # if not default_audio_input.isFormatSupported(self.audio_format):
        #     qWarning("Default format not supported - trying to use nearest")
        #     self.audio_format = default_audio_input.nearestFormat(self.audio_format)

        
        ## 默认设备与其他设备：方法2
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
        layout.addWidget(self.m_device_box)

        ### 调节音量大小的滑动条
        self.m_volume_slider = QSlider(Qt.Horizontal, self)
        self.m_volume_slider.setRange(0, 100)
        self.m_volume_slider.setValue(100)
        self.m_volume_slider.valueChanged.connect(self.slider_changed)
        layout.addWidget(self.m_volume_slider)

        ### 暂停/恢复
        self.m_suspend_resume_button = QPushButton(self)
        self.m_suspend_resume_button.clicked.connect(self.toggle_suspend)
        layout.addWidget(self.m_suspend_resume_button)

        ### 存储
        btn_save = QPushButton('save')
        btn_save.clicked.connect(self.slot_save)
        layout.addWidget(btn_save)

        ### 清空
        btn_clear = QPushButton('clear')
        btn_clear.clicked.connect(self.slot_clear)
        layout.addWidget(btn_clear)

    def initialize_audio(self, audio_device: QAudioDevice):
        ##### 存储实时音频
        self.output_buffers = QByteArray()

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

        
        # 确保停止输入
        self.audio_source.stop()
        # 从 StoppedState 激活到 ActivateState
        self.toggle_suspend()

        # io
        # 输入启动
        io = self.audio_source.start()

        def push_mode_slot():
            length = self.audio_source.bytesAvailable()
            # 这是个缓存机制，保证实时性
            buffer_size = 4096
            # length = min(length, buffer_size)
            if length > buffer_size:
                length = buffer_size
            # 读取
            buffer: QByteArray = io.read(length)
            # 实时事件
            if length > 0:
                filted_buffer = self.m_audio_info.filter(buffer)
                self.output_buffers.append(filted_buffer)
                level = self.m_audio_info.calculate_level(filted_buffer)
                self.m_canvas.set_level(level)
        
        # io准备好连接
        io.readyRead.connect(push_mode_slot)

    @Slot()
    def toggle_suspend(self):
        # toggle suspend/resume
        state = self.audio_source.state()
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

    @Slot()
    def slot_save(self):
        wf = wave.open(self.audio_output_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(self.output_buffers.data())
        wf.close()

    @Slot()
    def slot_clear(self):
        self.output_buffers.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initialize_window()
        
    def initialize_window(self):
        central_widget = QWidget()
        # 布局是建立在中心组件中
        layout = QVBoxLayout(central_widget)

        self.myAudioWidget = MyAudioWidget(self)
        layout.addWidget(self.myAudioWidget)

        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()    
    mainWindow.show()
    app.exec()