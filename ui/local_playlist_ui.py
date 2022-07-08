import cloudmusic
import qtawesome, time
from qtawesome import icon_browser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtMultimedia import *
from PyQt5.Qt import *
from PyQt5.QtWidgets import (QApplication, QMessageBox, QLabel, QWidget,
                             QHBoxLayout, QVBoxLayout, QMainWindow, QGridLayout, QPushButton, QScrollArea,
                             QStackedWidget)
from PyQt5.QtGui import QFont, QIcon, QImage, QPixmap, QPen
from PyQt5.QtCore import QCoreApplication, QTimer, QSize
import logging
import sys, cv2
import requests
import numpy as np
import os
from crawl.get_artist_info import artist_info
from ui.rewriting_btns import QDoublePushButton, QMusicPushButton


class local_playlist_ui(QWidget):
    def __init__(self, main_ui, folder_path):
        # main_ui是主界面
        super(local_playlist_ui, self).__init__()
        self.main_ui = main_ui
        self.folder_path = folder_path  # 文件夹路径
        self.init_vars()
        self.init_ui()
        self.init_style()

    def init_vars(self):
        if self.folder_path == '':
            self.music_file_names = []
        else:
            self.music_file_names = os.listdir(self.folder_path)

    def init_style(self):
        pass

    def init_ui(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # split line
        self.split_line = QPushButton(' ' * 7 + '序号'.ljust(8, ' ') + '音乐标题'.ljust(42, ' ')
                                      + '歌手'.ljust(42, ' ') + '专辑'.ljust(42, ' ') + '格式转换')
        self.split_line.setObjectName('split_line')

        # scroll area
        self.scroll = QScrollArea()
        self.scroll.setObjectName('scroll')
        self.scroll_layout = QGridLayout()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.scroll_layout)

        self.main_ui.musics_list[2] = []
        for i, music_file_name in enumerate(self.music_file_names):
            # song_btn为重写的QDoublePushButton,支持双击播放歌曲。
            if music_file_name[-4:] != '.mp3':  # 格式不符合。
                continue
            song_btn = QDoublePushButton()
            song_btn.setObjectName('song_btn')
            song_btn.music_path = self.folder_path + '/' + music_file_name
            song_btn.doubleClicked.connect(self.main_ui.local_song_btn_doubleClicked)
            song_btn.setFixedSize(QSize(900, 25))

            # 歌的序号、标题、歌手等信息标签
            try:
                singer_name, music_name = music_file_name[:-4].split(sep='-')[0:2]
            except:
                continue
            label_seq = QLabel(str(i + 1).rjust(2, '0'))
            label_title = QLabel(self.main_ui.align_left(music_name, 20, 25))
            label_singer = QLabel(self.main_ui.align_left(singer_name, 20, 25))
            label_album = QLabel(self.main_ui.align_left('-', 20, 25))
            label_m4a_flag = QPushButton(qtawesome.icon('fa.times', color='red'), '')
            self.main_ui.musics_list[2].append(self.folder_path + '/' + music_file_name)

            label_seq.setObjectName('label_song')
            label_title.setObjectName('label_song')
            label_singer.setObjectName('label_song')
            label_album.setObjectName('label_song')

            # 布置scroll_widget
            self.scroll_layout.addWidget(QLabel(''), i, 0, 1, 2)
            self.scroll_layout.addWidget(QLabel(''), i, 2, 1, 2)

            self.scroll_layout.addWidget(label_seq, i, 4, 1, 6)
            self.scroll_layout.addWidget(label_title, i, 10, 1, 25)
            self.scroll_layout.addWidget(label_singer, i, 35, 1, 25)
            self.scroll_layout.addWidget(label_album, i, 60, 1, 25)
            self.scroll_layout.addWidget(label_m4a_flag, i, 85, 1, 2)

            self.scroll_layout.addWidget(QLabel(''), i, 87, 1, 8)

            # 注意song_btn放在重叠区域最上层。
            self.scroll_layout.addWidget(song_btn, i, 4, 1, 91)
            self.scroll_layout.addWidget(QLabel(''), i, 92, 1, 2)
        self.scroll.setWidget(self.scroll_widget)

        # 布置layout
        self.layout.addWidget(self.split_line, 0, 0, 1, 10)
        self.layout.addWidget(self.scroll, 1, 0, 9, 10)
