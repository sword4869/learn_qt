'''

非阻塞式的无限录音

'''


import sys
import wave

import pyaudio
from PySide6.QtCore import Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        toolbar = QToolBar('Toolbar')

        record_start_action = QAction('开始录制', self, triggered=self._record_start)
        toolbar.addAction(record_start_action)

        record_stop_action = QAction('录制结束', self, triggered=self._record_stop)
        toolbar.addAction(record_stop_action)

        record_play_action = QAction('播放', self, triggered=self._record_play)
        toolbar.addAction(record_play_action)


        self.addToolBar(toolbar)



        # 定义音频属性
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.audio_path_record = "output.wav"        
        self.audio_path_play = "output.wav"        



    @Slot()
    def _record_start(self):
        # 创建PyAudio对象
        self.p = pyaudio.PyAudio()

        # 创建wave对象        
        self.wf = wave.open(self.audio_path_record, 'wb')
        self.wf.setnchannels(self.CHANNELS)
        self.wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        self.wf.setframerate(self.RATE)


        def callback(in_data, frame_count, time_info, status):
            self.wf.writeframes(in_data)
            return (in_data, pyaudio.paContinue)

        # 打开数据流
        self.stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK,
                        stream_callback=callback)

        print("* recording")

        # 开始录音
        self.stream.start_stream()


    @Slot()
    def _record_stop(self):
        print("* done recording")

        # 停止数据流
        self.stream.stop_stream()
        self.stream.close()

        # 关闭PyAudio
        self.p.terminate()

        # 关闭 wave
        self.wf.close()

    @Slot()
    def _record_play(self):
        wf=wave.open(self.audio_path_play,'rb')

        p=pyaudio.PyAudio()
        stream=p.open(
            format=p.get_format_from_width(width=wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        while True:
            data=wf.readframes(self.CHUNK)
            if data==b"":
                break
            stream.write(data)
        
        # 停止数据流
        stream.close()

        # 关闭PyAudio
        p.terminate()

        # 关闭 wave
        wf.close()

        print("* done play")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Qapp')
    main_win = MainWindow()

    # 应用全屏
    available_geometry = main_win.screen().availableGeometry()
    # my_size = available_geometry.width(), available_geometry.height()
    my_size = available_geometry.width()/2, available_geometry.height()/2
    main_win.resize(my_size[0], my_size[1])
    main_win.show()
    sys.exit(app.exec())