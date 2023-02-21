# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

""" 非多线程版本 """

import os
import numpy as np
import random
import sys
import wave
import pyaudio
import time
import threading 
import json

''' 人像系统 '''
import torch
import yaml
from train_mfcc2coe import Lm_encoder, Ct_encoder, Decoder
from vqgan_single import VQModel
from test_talking_with_wav import test_model_with_wav


''' 语音系统 '''
import qa_main
from qmc import run_qmc
# import wenetruntime as wenet
from paddlespeech.cli.asr.infer import ASRExecutor



''' qt '''
from PySide6.QtCore import QStandardPaths, Qt, QUrl, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QScreen
from PySide6.QtMultimedia import (QAudio, QAudioOutput, QMediaFormat,
                                  QMediaPlayer)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QMainWindow,
                               QSlider, QStyle, QToolBar)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('3D human')

        toolbar = QToolBar('Toolbar')

        record_start_action = QAction('开始录制', self, triggered=self._record_start)
        toolbar.addAction(record_start_action)

        record_stop_action = QAction('录制结束', self, triggered=self._record_stop)
        toolbar.addAction(record_stop_action)

        record_play_action = QAction('播放录音', self, triggered=self._record_play)
        toolbar.addAction(record_play_action)


        self.addToolBar(toolbar)

        # 媒体播放器
        self._player = QMediaPlayer()
        # 设置媒体播放器的音频输出
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
    
        # 视频widget
        self._video_widget = QVideoWidget()
        self.setCentralWidget(self._video_widget)
        # 设置媒体播放器的视频输出
        self._player.setVideoOutput(self._video_widget)

        
        # 定义音频属性
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.WAVE_OUTPUT_FILENAME = "output.wav"        


        ''' 网络初始化 '''
        saved_time_begin = time.time()

        # 随机设置
        torch.manual_seed(10)
        torch.cuda.manual_seed_all(10)
        np.random.seed(10)
        random.seed(10)
        torch.backends.cudnn.deterministic = True

        # 配置        
        self.img_path = "./data/template_face.png"
        self.vq_key = 5000
        self.vq_path = f"./checkpoint/vq_path-{self.vq_key}.pth"
        self.out_coe_path = f'./checkpoint/mfcc2coe-{self.vq_key}.pth'
        print(f'vq_path = {self.vq_path}')
        print(f'out_coe_path = {self.out_coe_path}')
        self.device = torch.device('cuda:0')
        print(f'device = {self.device}')

        
        # ------------------人像系统----------------
        # 加载配置
        with open("./config/mead_singal_gan.yaml", 'r') as stream:
            cfg = yaml.safe_load(stream)
        self.gen_cfg = cfg['model']['params']
        print(f"* done gen_cfg")


        # generator
        self.generator = VQModel(**self.gen_cfg)
        dic = torch.load(self.vq_path, map_location="cpu")
        self.generator.load_state_dict(dic["generator"])
        self.generator.eval().to(self.device)
        print(f"* done generator")


        # lm_encoder
        self.lm_encoder = Lm_encoder()
        dic_au = torch.load(self.out_coe_path, map_location="cpu")
        self.lm_encoder.load_state_dict(dic_au["lm_encoder"])
        self.lm_encoder.eval().to(self.device)
        print(f"* done lm_encoder")

        
        # encoder
        self.encoder = Ct_encoder()
        self.encoder.load_state_dict(dic_au["encoder"])
        self.encoder.eval().to(self.device)
        print(f"* done encoder")


        # decoder
        self.decoder = Decoder()
        self.decoder.load_state_dict(dic_au["decoder"])
        self.decoder.eval().to(self.device)
        print(f"* done decoder")

        del dic, dic_au


        
        # def generate_file_path(video_key):
        #     file_path = test_model_with_wav(
        #         video_key=video_key,
        #         img=self.img_path,
        #         vq_key=self.vq_key,
        #         device=self.device,
        #         is_test=False,
        #         is_fusion=False,
        #         generator=self.generator,
        #         lm_encoder=self.lm_encoder, 
        #         encoder=self.encoder, 
        #         decoder=self.decoder
        #     )
        #     return file_path
        # idxs = [str(idx + 1).zfill(3) for idx in range(10)]
        # file_paths = [
        #     generate_file_path(i) for i in idxs
        # ]

        self.file_paths = ['./out_vid/001-5000-rec-audio.mp4', './out_vid/002-5000-rec-audio.mp4', './out_vid/003-5000-rec-audio.mp4', './out_vid/004-5000-rec-audio.mp4', './out_vid/005-5000-rec-audio.mp4', './out_vid/006-5000-rec-audio.mp4', './out_vid/007-5000-rec-audio.mp4', './out_vid/008-5000-rec-audio.mp4', './out_vid/009-5000-rec-audio.mp4', './out_vid/010-5000-rec-audio.mp4']
        print(self.file_paths)
        self.continue_idx = 0




        return 
        
        # ----------------问答系统----------------
        # run_qmc
        self.qa = run_qmc()
        print(f"* done run_qmc")

        self.model_dir = os.path.join(os.path.dirname(__file__), 'speech_recognition/models/chs')

        saved_time_end = time.time()
        print(f'we save time: {saved_time_end - saved_time_begin} seconds.')
        self.wedecoder = ASRExecutor()



    @Slot()
    def _record_start(self):


        # 创建PyAudio对象
        self.p = pyaudio.PyAudio()

        # 创建wave对象        
        self.wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
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
        # 停止数据流
        self.stream.stop_stream()
        self.stream.close()

        # 关闭PyAudio
        self.p.terminate()

        # 关闭 wave
        self.wf.close()

        print("* done recording")


        time.sleep(int(random.randrange(5,10)))
        self.playVideo(self.file_paths[self.continue_idx])
        self.continue_idx += 1
        return 


        ''' 播放视频 '''
        self.play_network_video()

    @Slot()
    def _record_play(self):
        audio_path = 'test/test-dang-an-shi-shen-me.wav'
        # audio_path = 'test/test-something.wav'
        # audio_path = self.WAVE_OUTPUT_FILENAME
        wf=wave.open(audio_path,'rb')
        # width=wf.getsampwidth()
        # channels=wf.getnchannels()
        # rate=wf.getframerate()
        # frames = wf.getnframes()
        # print(width, channels, rate, frames)

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
        

    def play_network_video(self):
        file_path = self.network()
        print(f"* done network...{file_path}")
        if file_path != None:
            self.playVideo(file_path)

    

        
    def network(self):
        ''' 返回视频的路径 '''

        def fetch_audio(txt):
            with open('data/语料库.txt', 'r') as f:
                lines = f.readlines()
                for idx, line in enumerate(lines):
                    if txt in line:
                        # data 从 001 开始
                        return str(idx + 1).zfill(3)
            return None

        # audio_path = self.WAVE_OUTPUT_FILENAME
        audio_path = 'test/test-dang-an-shi-shen-me.wav'
        # audio_path = 'test/test-something.wav'

        print(f'audio_path : {audio_path}')

        print(f"* starting network...")
        t1 = time.time()
        
        # decode
        txt = self.wedecoder(audio_file=audio_path)
        print(txt)
        txt = json.loads(txt)['nbest'][0]['sentence']
        t4 = time.time()
        print(f"* done decode: {txt}...{t4-t1} seconds")

        # q_matching
        _, ans = self.qa.q_matching(txt)
        t5 = time.time()
        print(f"* done matching: {ans}...{t5-t1} seconds")
        
        # 人像系统
        if ans == '对不起，您的问题无法检索':
            print('return None')
            return None

        video_key = fetch_audio(ans)
        file_path = test_model_with_wav(
                        video_key=video_key,
                        img=self.img_path,
                        vq_key=self.vq_key,
                        device=self.device,
                        is_test=False,
                        is_fusion=False,
                        generator=self.generator,
                        lm_encoder=self.lm_encoder, 
                        encoder=self.encoder, 
                        decoder=self.decoder
        )
        t6 = time.time()
        print(f"* done talking_head: {file_path}...{t6-t1} seconds")
        assert file_path != None   
        return file_path
        


    def playVideo(self, file_path):
        self.ensure_stopped()

        # 设置媒体播放器的视频源
        url = QUrl.fromLocalFile(file_path)
        self._player.setSource(url)
        
        # 媒体播放器，执行播放
        self._player.play()

    def ensure_stopped(self):
        if self._player.playbackState() != QMediaPlayer.StoppedState:
            self._player.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()

    # 应用全屏
    available_geometry = main_win.screen().availableGeometry()
    my_size = available_geometry.width(), available_geometry.height()
    # my_size = available_geometry.width()/2, available_geometry.height()/2
    main_win.resize(my_size[0], my_size[1])
    main_win.show()
    sys.exit(app.exec())