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


class singer_info_ui(QWidget):
    def __init__(self, main_ui, singer_name):
        super().__init__()
        self.main_ui = main_ui  # main_ui就是我们的mainwindow,方便调用mainwindow的槽函数。
        self.singer_name = singer_name
        self.init_vars()
        self.init_ui()
        self.init_style()

    def init_style(self):
        if self.avatar_url == '':
            return
        self.avatar_label.setStyleSheet('''border-radius:10px;''')
        self.singer_name_label.setStyleSheet('''
                    font-weight:700;
                    font-size:26px;
                ''')
        # size
        self.avatar_label.setFixedSize(QSize(200, 200))

    def init_vars(self):
        self.avatar_url, self.music_id_list = artist_info(self.singer_name)
        if self.avatar_url == '':
            return
        self.avatar_img = self.get_img_from_url(self.avatar_url)
        self.musics = []
        for id in self.music_id_list:
            # while 1:
            #     music = cloudmusic.getMusic(str(id))
            #     if music != []:
            #         break
            #     print('music加载失败,网络繁忙....正在重试....')
            music = cloudmusic.getMusic(str(id))
            if music != []:
                self.musics.append(music)

    def init_ui(self):
        if self.avatar_url == '':
            return
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # 头像label
        self.avatar_label = QLabel()
        self.avatar_label.setObjectName('avatar_label')
        self.set_pixmap(self.avatar_label, self.avatar_img, 200, 200)

        # 歌手名字label
        self.singer_name_label = QLabel()
        self.singer_name_label.setObjectName('singer_name_label')
        self.singer_name_label = QLabel(self.singer_name)

        # scroll area
        self.scroll = QScrollArea()
        self.scroll.setObjectName('scroll')
        self.scroll_layout = QGridLayout()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.scroll_layout)

        # 分割线
        self.split_line = QPushButton(' ' * 11 + '序号'.ljust(8, ' ') + '音乐标题'.ljust(41, ' ')
                                      + '歌手'.ljust(45, ' ') + '专辑'.ljust(42, ' ') + '格式转换')
        self.split_line.setObjectName('split_line')
        # 布置self
        self.layout.addWidget(self.avatar_label, 0, 0, 4, 2)
        self.layout.addWidget(self.singer_name_label, 0, 2, 1, 1)
        self.layout.addWidget(QLabel(''), 0, 3, 1, 7)
        self.layout.addWidget(QLabel(''), 1, 2, 3, 8)

        self.layout.addWidget(self.split_line, 4, 0, 1, 10)

        self.layout.addWidget(self.scroll, 5, 0, 5, 10)
        self.main_ui.musics_list[1] = []
        for i, music in enumerate(self.musics):
            # song_btn为重写的QDoublePushButton,支持双击播放歌曲。
            song_btn = QDoublePushButton()
            song_btn.setObjectName('song_btn')
            song_btn.music = music
            song_btn.doubleClicked.connect(self.main_ui.song_btn_doubleClicked)
            song_btn.setFixedSize(QSize(900, 25))

            # 歌的序号、标题、歌手等信息标签
            label_seq = QLabel(str(i + 1).rjust(2, '0'))
            label_title = QLabel(self.main_ui.align_left(music.name, 20, 25))
            label_singer = QLabel(self.main_ui.align_left(music.artist[0], 20, 25))
            label_album = QLabel(self.main_ui.align_left(music.album, 20, 25))
            label_m4a_flag = QPushButton(
                qtawesome.icon('fa.check', color='red') if music.type == 'm4a' else qtawesome.icon(
                    'fa.times', color='red'), '')  # 如果是m4a类型的需要格式转化，加上下载时间，耗时较长
            self.main_ui.musics_list[1].append(music)
            label_seq.setObjectName('label_song')
            label_title.setObjectName('label_song')
            label_singer.setObjectName('label_song')
            label_album.setObjectName('label_song')

            # like_btn = QPushButton(qtawesome.icon('fa5.heart', color='red'), '')

            # 下载按钮,下载歌曲
            download_btn = QMusicPushButton(qtawesome.icon('ri.download-cloud-2-line', color='gray'), '')
            download_btn.setObjectName('operate_btn')
            download_btn.setCursor(Qt.PointingHandCursor)
            download_btn.setToolTip('下载歌曲')
            download_btn.music = music
            download_btn.setFixedSize(QSize(20, 20))
            download_btn.clicked.connect(self.main_ui.download_btn_clicked)

            # 更多信息按钮,即查看评论信息等
            more_info_btn = QMusicPushButton(qtawesome.icon('ri.more-2-fill', color='gray'), '')
            more_info_btn.setObjectName('operate_btn')
            more_info_btn.setCursor(Qt.PointingHandCursor)
            more_info_btn.setToolTip('查看详细信息')
            more_info_btn.music = music
            more_info_btn.setFixedSize(QSize(20, 20))
            more_info_btn.clicked.connect(self.main_ui.more_info_btn_clicked)

            # 打开url按钮
            open_music_url_btn = QMusicPushButton(qtawesome.icon('ph.link-simple-horizontal-fill', color='gray'), '')
            open_music_url_btn.setObjectName('operate_btn')
            open_music_url_btn.setCursor(Qt.PointingHandCursor)
            open_music_url_btn.setToolTip('打开歌曲链接')
            open_music_url_btn.music = music
            open_music_url_btn.setFixedSize(QSize(20, 20))
            open_music_url_btn.clicked.connect(self.main_ui.open_music_url_btn_clicked)

            # 布置scroll_widget
            self.scroll_layout.addWidget(download_btn, i, 0, 1, 2)
            self.scroll_layout.addWidget(more_info_btn, i, 2, 1, 2)

            self.scroll_layout.addWidget(label_seq, i, 4, 1, 6)
            self.scroll_layout.addWidget(label_title, i, 10, 1, 25)
            self.scroll_layout.addWidget(label_singer, i, 35, 1, 25)
            self.scroll_layout.addWidget(label_album, i, 60, 1, 25)
            self.scroll_layout.addWidget(label_m4a_flag, i, 85, 1, 2)

            self.scroll_layout.addWidget(QLabel(''), i, 87, 1, 8)

            # 注意song_btn放在重叠区域最上层。
            self.scroll_layout.addWidget(song_btn, i, 4, 1, 91)
            self.scroll_layout.addWidget(open_music_url_btn, i, 92, 1, 2)
        self.scroll.setWidget(self.scroll_widget)

    def set_pixmap(self, label, img, w=100, h=100):
        '''
        label_img的设置

        '''
        img = cv2.cvtColor(cv2.resize(img, (w, h)), cv2.COLOR_BGR2RGB)
        Qimg = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(Qimg))

    def get_img_from_url(self, url):
        '''
        requests爬虫从url下载图片,并转化为nparray形式

        :param url:
        :return:
        '''
        pic_bytes = requests.get(url, timeout=10).content  # 利用requests爬虫和music_pic的url获得字节序列
        nparr = np.frombuffer(pic_bytes, np.uint8)  # 将字节序转化为npaarry
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # cv2解码得到music的专辑图片。
        return img
