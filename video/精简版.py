import os
import sys

from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QAction
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QApplication, QMainWindow, QToolBar,
                               QVBoxLayout, QWidget)


class MyVideoWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.initialize_window()
        self.initialize_video()

    def initialize_window(self):
        layout = QVBoxLayout()

        # 视频widget
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        
        self.setLayout(layout)

    def initialize_video(self):
        # 媒体播放器
        self.media_player = QMediaPlayer()

        # 设置媒体播放器的音频输出
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
    

        # 设置媒体播放器的视频输出
        self.media_player.setVideoOutput(self.video_widget)  

        # 媒体情况
        self.media_player.mediaStatusChanged.connect(self.slot_media_status_changed)
        # 视频播放进度
        self.media_player.positionChanged.connect(self.slot_position_changed)

    @Slot()
    def slot_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            print('* media finished.')
        print(f'[slot_media_status_changed] status = {status}')        
        print(f'[slot_media_status_changed] self.media_player.playbackState() = {self.media_player.playbackState()}')

 
    @Slot()
    def slot_position_changed(self, position):
        ###
        # 正常来说，播放完视频就黑屏了，现在我们检测到即将播放完毕时，暂定在最后一帧上。
        ###
        # print(f'[slot_position_changed] position = {position} / {self.media_player.duration()}')    
        if (self.media_player.duration()- position) < 150:
            self.media_player.setPosition(self.media_player.duration()-1)
            self.media_player.pause()    

   

    def playVideo(self, file_path):
        self.ensure_stopped()

        # 设置媒体播放器的视频源
        print(f"{file_path} exist: {os.path.exists(file_path)}")
        url = QUrl.fromLocalFile(file_path)
        self.media_player.setSource(url)
        
        # 媒体播放器，执行播放
        self.media_player.play()


    def ensure_stopped(self):
        if self.media_player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.media_player.stop()
            print('[ensure_stopped] stop it')
        else:
            print('[ensure_stopped] is stopped')


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()


        toolbar = QToolBar('Toolbar')
        open_action = QAction('play', self, triggered=self.slot_play_video2)
        toolbar.addAction(open_action)
        self.addToolBar(toolbar)

        central_widget = QWidget()
        # 布局是建立在中心组件中
        layout = QVBoxLayout(central_widget)

        self.myVideoWidget = MyVideoWidget()
        layout.addWidget(self.myVideoWidget)

        self.setCentralWidget(central_widget)

    @Slot()
    def slot_play_video2(self):
        video_file = r'test\7.mp4'

        ########## 为什么报错！！！！！
        # handleSessionEvent: serious error =  0x80004005
        # Media session serious error.
        # # video_file = r'E:\CodeProject\Git\learn_qt\out_vid\001-5000-rec-audio.mp4'
        # # video_file = r'E:/CodeProject/Git/learn_qt/out_vid/001-5000-rec-audio [最优化的质量和大小].mp4'

        self.myVideoWidget.playVideo(video_file)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()

    # 应用全屏
    available_geometry = mainWindow.screen().availableGeometry()
    mainWindow.resize(available_geometry.width()/2,
                    available_geometry.height()/2)
    mainWindow.show()
    sys.exit(app.exec())