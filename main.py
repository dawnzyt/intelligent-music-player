import random
import os
import time
import sys
import utils.format_cvt
from utils.reader import load_audio
from utils.record import RecordAudio
import torch
import numpy as np
from crawl.id import id_dict
from crawl.search_for_list import get_playlist
from crawl.generate_info import get_info
from cloudmusic.musicObj import Music
from ui.local_playlist_ui import local_playlist_ui
from ui.music_info_ui import music_info_ui
from ui.singer_info_ui import singer_info_ui
from ui.rewriting_btns import QDoublePushButton, QMusicPushButton
import qtawesome
from PyQt5.QtMultimedia import *
from PyQt5 import QtCore, QtGui
from PyQt5.Qt import *
from PyQt5.QtWidgets import (QApplication, QMessageBox, QLabel, QWidget,
                             QMainWindow, QGridLayout, QPushButton, QScrollArea,
                             QStackedWidget)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, QSize


class MainUi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_vars()
        self.init_ui()
        self.init_style()
        self.init_slot()

    def init_vars(self):
        '''
        init_vars用来初始化一些变量、参数、实例对象等。

        :return:
        '''
        self.playlist_cls = [
            ['语言', '华语', '欧美', '日语', '粤语', '韩语', '粤语'],
            ['风格', '流行', '摇滚', '民谣', '电子', '舞曲', '说唱', '轻音乐', '爵士', '乡村', 'R&B/Soul', '古典', '民族', '英伦', '金属', '朋克',
             '蓝调', '雷鬼', '世界音乐', '拉丁', 'New Age', '古风', '后摇', 'Bossa Nova'],
            ['场景', '清晨', '夜晚', '学习', '工作', '午休', '下午茶', '地铁', '驾车', '运动', '旅行', '散步', '酒吧'],
            ['情感', '怀旧', '清新', '浪漫', '伤感', '治愈', '放松', '孤独', '感动', '兴奋', '快乐', '安静', '思念'],
            ['主题', '综艺', '影视原声', 'ACG', '儿童', '校园', '游戏', '70后', '80后', '90后', ' 00后', '网络歌曲', 'KTV', '经典', '翻唱', '吉他',
             '钢琴', '器乐', '榜单']
        ]
        # 播放相关
        self.is_pause = 1  # 记录歌曲播放是否暂停
        self.sound_player = QMediaPlayer()  # 音效播放媒体流
        self.player = QMediaPlayer()  # 当前页面的播放媒体流,用来播放音乐。
        self.download_flag = dict()  # {music_id:1/0} 1表示已下载临时文件。同理0
        self.bar_mxValue = 1000  # 播放进度/音量slider的最大值,固定。
        self.play_timer = QTimer()  # 定时器,动态跟踪self.player.position,从而动态设置time_bar。一个简单的比例关系:timer_bar_pos=(player.position/player.duration)*self.bar_mxValue
        self.play_timer.timeout.connect(self.play_timer_timeout)
        self.mode = 0  # 播放模式:0代表单曲播放,1代表顺序播放,2代表随机播放。对应由mode_btn改变。
        self.page_now = 0  # 0:代表“分类歌单界面”;1:”声纹识别界面“。
        self.musics_list = [[], [], []]  # 对应界面的可播放歌单,前两个list由于是在线爬虫存储的是Music实例;第三个list由于是本地歌单因此只存储音频的绝对路径。
        self.play_seq = []  # play_seq[i]对应第i次播放的音乐在musics_list[now_page]列表的下标,以实现上一首、下一首播放的功能。
        self.play_seq_cursor = -1  # play_seq的指针,指向当前播放的音乐。
        self.now_play_music = None  # 记录当前播放音乐

        # 爬虫爬取歌单
        self.id_dict = id_dict
        # 声纹识别模型相关
        model_path = 'models/resnet34.pth'  # 声纹识别模型路径
        self.device = torch.device("cuda")  # torch_device初始化
        self.model = torch.jit.load(model_path)  # torch声纹识别模型初始化
        self.model.to(self.device)
        self.model.eval()
        # 加载本地数据库
        _ = np.loadtxt('./otherFiles/audio_data.txt', dtype=np.str, delimiter=',')  # 本地音频载入数据库
        self.local_audio_features = _[:, 0:-1].astype(np.float)  # 本地数据库歌手音频特征向量
        self.singer_name = _[:, -1]  # 本地数据库歌手名
        # 录音相关
        self.record_audio = RecordAudio()  # 定义为录音相关类的实例
        self.rec_path = ''  # 声纹识别音频路径

    def init_style(self):
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)  # 隐藏边框
        self.setWindowOpacity(0.9)  # 设置窗口透明度
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明

        self.left_widget.setStyleSheet('''
            QWidget#left_widget{
                background:gray;
                border-bottom:1px solid white;
                border-left:1px solid white;
                border-bottom-left-radius:20px;
            }
            QPushButton#left_btn{
                color:white;
                text-align:left;
            }
            QPushButton#left_btn:hover{
                border-left:3px solid red;
                font-weight:700;
            }
            QPushButton#close_btn{
                border-radius:7px;
                background:#F76677;
            }
            QPushButton#close_btn:hover{
                background:red;
            }
        ''')
        self.top_widget.setStyleSheet('''
            QWidget#top_widget{
                background:red;
                border-top:1px solid white;
                border-left:1px solid white;
                border-right:1px solid white;
                border-top-left-radius:20px;
                border-top-right-radius:20px;
            }
            QPushButton#top_label{
                color:white;
                font-size:24px;
                font-weight:700;
            }
        ''')
        self.main_widget.setStyleSheet('''
            QWidget{
                border:none;
            }
            QWidget#right_widget{
                background:white;
                border-bottom:1px solid white;
                border-right:1px solid white;
            }
        ''')
        self.right_play_widget.setStyleSheet('''
            QWidget#right_widget{
                border-bottom-right-radius:20px;
            }
            QPushButton#music_name_label{
                text-align:middle;
                font-size:20px;
                font-weight:420;
                font-family: STXingkai;
            }
            QPushButton#music_name_label:hover{
                font-weight:500;
            }
            QLabel#music_album_label{
                text-align:middle;
                font-size:12px;
                color:gray;
            }
        ''')
        self.right_playlist_widget.setStyleSheet('''
            QPushButton#operate_btn:hover{
                border-left:2px solid black;
            }
            QPushButton#type_label{
                border-right:4px solid red;
                font-weight:700;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QPushButton#cls_btn{
                font-size:16px;
                font-family: STXingkai;
            }
            QPushButton#cls_btn:hover{
                border-top:4px solid blue;
                border-right:4px solid blue;
                font-weight:1000;
                color:blue;
            }
            QPushButton#split_line{
                border-top:1px solid gray;
                text-align:left;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QPushButton#song_btn{
                text-align:left;
                border-radius:5px;
            }
            QPushButton#song_btn:hover{
                background:rgba(120,120,120,0.5);
            }
            QLabel#label_song{
                text-aligh:left;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QScrollArea{
                background:transparent;
                border-bottom:1px solid black;
            }
        ''')
        self.right_local_widget.setStyleSheet('''
            QPushButton#split_line{
                border-top:1px solid gray;
                text-align:left;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QPushButton#song_btn{
                text-align:left;
                border-radius:5px;
            }
            QPushButton#song_btn:hover{
                background:rgba(120,120,120,0.5);
            }
            QLabel#label_song{
                text-aligh:left;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QScrollArea{
                background:transparent;
                border-bottom:1px solid black;
            }
            QLabel#title_label{
                font-size:18px;
                font-weight:700;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
        ''')
        self.right_rec_widget.setStyleSheet('''
            QPushButton#split_line{
                border-top:1px solid gray;
                text-align:left;
                font-weight=700;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QPushButton#song_btn{
                text-align:left;
                border-radius:5px;
            }
            QPushButton#song_btn:hover{
                background:rgba(120,120,120,0.5);
            }
            QLabel#label_song{
                text-aligh:left;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QLabel#rec_label{
                font-weight:700;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QProgressBar{
                border-radius:8px;
                border:1px solid black;
                text-align:center;
                padding:1px;
                background-color:#F1F1F1;
                }
            }
            QProgressBar::chunk{
                background-color:#05B8CC;
                border-radius:8px;
            }
        ''')

        self.right_playlist_layout.setSpacing(2)
        self.main_layout.setSpacing(0)
        self.right_playlist_layout.setSpacing(0)

        # Size设置
        self.play_btn.setIconSize(QSize(25, 25))
        self.volume_label.setFixedSize(QSize(16, 16))
        self.time_bar.setFixedWidth(400)
        self.volume_bar.setFixedWidth(100)
        self.left_time_label.setFixedWidth(40)
        self.right_time_label.setFixedWidth(40)
        self.close_btn.setIconSize(QSize(16, 16))
        self.path_set_btn.setIconSize(QSize(25, 25))
        self.record_btn.setIconSize(QSize(40, 40))
        self.rec_btn.setIconSize(QSize(25, 25))
        self.search_singer_btn.setIconSize(QSize(25, 25))
        self.music_name_label.setFixedWidth(300)
        self.music_album_label.setFixedWidth(300)
        self.nxt_btn.setIconSize(QSize(25, 25))
        self.previous_btn.setIconSize(QSize(25, 25))

        # 图标
        self.setWindowIcon(QIcon('otherFiles/icon.jpg'))

    def init_slot(self):
        self.playlist_btn.clicked.connect(self.playlist_btn_clicked)
        self.rec_interface_btn.clicked.connect(self.rec_interface_btn_clicked)
        self.local_btn.clicked.connect(self.local_btn_clicked)

    def init_ui(self):
        # main_widget初始化
        self.setFixedSize(1200, 720)
        self.main_widget = QWidget()  # main_widget
        self.setCentralWidget(self.main_widget)  # 设置中心widget为main_widget
        self.main_layout = QGridLayout()  # main_widget layout
        self.main_widget.setLayout(self.main_layout)

        # top_widget初始化
        self.top_widget = QWidget()
        self.top_layout = QGridLayout()
        self.top_widget.setLayout(self.top_layout)
        self.top_widget.setObjectName('top_widget')
        # left_widget初始化
        self.left_widget = QWidget()
        self.left_layout = QGridLayout()
        self.left_widget.setLayout(self.left_layout)
        self.left_widget.setObjectName('left_widget')

        # right_play_widget初始化 播放按钮+调节音量等
        self.right_play_widget = QWidget()
        self.right_play_layout = QGridLayout()
        self.right_play_widget.setLayout(self.right_play_layout)
        self.right_play_widget.setObjectName('right_widget')
        # right_playlist_widget初始化 分类+歌单展示
        self.right_playlist_widget = QWidget()
        self.right_playlist_layout = QGridLayout()
        self.right_playlist_widget.setLayout(self.right_playlist_layout)
        self.right_playlist_widget.setObjectName('right_widget')
        # right_rec_widget初始化 声纹识别widget
        self.right_rec_widget = QWidget()
        self.right_rec_layout = QGridLayout()
        self.right_rec_widget.setLayout(self.right_rec_layout)
        self.right_rec_widget.setObjectName('right_widget')
        # right_local_widget初始化 本地歌单widget
        self.right_local_widget = QWidget()
        self.right_local_layout = QGridLayout()
        self.right_local_widget.setLayout(self.right_local_layout)
        self.right_local_widget.setObjectName('right_widget')

        # right栈widget,按钮控制显示不同的right_widget
        self.right_stackedwidget = QStackedWidget()
        self.right_stackedwidget.addWidget(self.right_playlist_widget)
        self.right_stackedwidget.addWidget(self.right_rec_widget)
        self.right_stackedwidget.addWidget(self.right_local_widget)

        # main_layout设置
        self.main_layout.addWidget(self.top_widget, 0, 0, 2, 48)
        self.main_layout.addWidget(self.left_widget, 2, 0, 10, 5)
        self.main_layout.addWidget(self.right_stackedwidget, 2, 5, 7, 43)
        self.main_layout.addWidget(self.right_play_widget, 9, 5, 3, 43)
        # left_layout设置
        self.init_left_widget()

        # top_layout设置
        self.init_top_widget()

        # right_rec_layout设置
        self.init_rec_widget()

        # right_playlist_layout设置
        self.init_playlist_widget()

        # right_local_layout设置
        self.init_local_widget()

        # right_play_layout设置
        self.init_play_widget()

    def init_rec_widget(self):
        # 录音进度条
        self.record_progress_bar = QProgressBar()
        self.record_progress_bar.setValue(100)
        self.record_progress_bar.setObjectName('record_progress_bar')

        # 录音按钮
        self.record_btn = QPushButton(qtawesome.icon('mdi.record-rec', color='red'), '')
        self.record_btn.setObjectName('rec_widget_btn')
        self.record_btn.clicked.connect(self.record_btn_clicked)
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.setToolTip('录制')

        # 识别按钮
        self.rec_btn = QPushButton(qtawesome.icon('msc.run-all', color='red'), '')
        self.rec_btn.setObjectName('rec_widget_btn')
        self.rec_btn.clicked.connect(self.rec_btn_clicked)
        self.rec_btn.setCursor(Qt.PointingHandCursor)
        self.rec_btn.setToolTip('识别')

        # 音频文件路径选择按钮
        self.path_set_btn = QPushButton(qtawesome.icon('ri.settings-3-fill', color='red'), '')
        self.path_set_btn.setObjectName('rec_widget_btn')
        self.path_set_btn.clicked.connect(self.path_set_btn_clicked)
        self.path_set_btn.setCursor(Qt.PointingHandCursor)
        self.path_set_btn.setToolTip('音频文件选择')

        # 识别结果标签
        self.rec_name_label = QLabel('识别结果:')
        self.rec_name_label.setObjectName('rec_label')
        self.similarity_label = QLabel('相似度:')
        self.similarity_label.setObjectName('rec_label')

        # 歌手信息搜索按钮
        self.search_singer_btn = QPushButton(qtawesome.icon('ri.search-2-line', color='red'), '')
        self.search_singer_btn.setObjectName('rec_widget_btn')
        self.search_singer_btn.setToolTip('搜索歌手信息')
        self.search_singer_btn.clicked.connect(self.search_singer_btn_clicked)
        self.search_singer_btn.setCursor(Qt.PointingHandCursor)

        # 布置right_rec_widget
        self.right_rec_layout.addWidget(self.record_progress_bar, 0, 0, 1, 7)
        self.right_rec_layout.addWidget(QLabel(''), 1, 0, 1, 2)
        self.right_rec_layout.addWidget(self.path_set_btn, 1, 2, 1, 1)
        self.right_rec_layout.addWidget(self.record_btn, 1, 3, 1, 1)
        self.right_rec_layout.addWidget(self.rec_btn, 1, 4, 1, 1)
        self.right_rec_layout.addWidget(QLabel(''), 1, 5, 1, 2)
        self.right_rec_layout.addWidget(self.rec_name_label, 0, 7, 1, 2)
        self.right_rec_layout.addWidget(self.search_singer_btn, 0, 9, 1, 1)
        self.right_rec_layout.addWidget(self.similarity_label, 1, 7, 1, 3)

        self.singer_info_ui = QLabel('')  # 初始化singer_info_ui为空。
        self.right_rec_layout.addWidget(self.singer_info_ui, 2, 0, 10, 10)

    def init_top_widget(self):
        self.top_label = QPushButton(qtawesome.icon('fa.meetup', color='white'), '智能音乐系统SongForYou')
        self.top_label.setIconSize(QSize(50, 50))
        self.top_label.setObjectName('top_label')
        self.top_layout.addWidget(self.top_label, 0, 0, 4, 2)
        self.top_layout.addWidget(QLabel(''), 0, 4, 4, 8)

        # self.close_btn=QPushButton(qtawesome.icon('fa.close'))

    def init_left_widget(self):
        # close_btn
        self.close_btn = QPushButton(qtawesome.icon('fa.times', color='white'), '')
        self.close_btn.setObjectName('close_btn')
        self.close_btn.setToolTip('关闭播放器')
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close_btn_clicked)

        # 分类歌单btn
        self.playlist_btn = QPushButton(qtawesome.icon('ei.music', color='red'), '分类歌单')
        self.playlist_btn.setObjectName('left_btn')
        self.playlist_btn.setCursor(Qt.PointingHandCursor)
        # 声纹识别btn
        self.rec_interface_btn = QPushButton(qtawesome.icon('mdi.account-music', color='red'), '声纹识别')
        self.rec_interface_btn.setObjectName('left_btn')
        self.rec_interface_btn.setCursor(Qt.PointingHandCursor)
        # 本地歌单btn
        self.local_btn = QPushButton(qtawesome.icon('fa5b.ethereum', color='red'), '本地歌单')
        self.local_btn.setObjectName('left_btn')
        self.local_btn.setCursor(Qt.PointingHandCursor)

        self.left_layout.addWidget(self.close_btn, 0, 1, 3, 1)
        self.left_layout.addWidget(self.playlist_btn, 3, 0, 3, 3)
        self.left_layout.addWidget(self.rec_interface_btn, 6, 0, 3, 3)
        self.left_layout.addWidget(self.local_btn, 9, 0, 3, 3)
        self.left_layout.addWidget(QLabel(''), 12, 0, 57, 3)

    def init_play_widget(self):
        # 播放音量进度条
        self.volume_bar = QSlider(Qt.Horizontal)
        self.volume_bar.setObjectName('slider_bar')
        self.volume_bar.setFocusPolicy(Qt.NoFocus)  # 表示不接收键盘角点
        self.volume_bar.setMinimum(0)
        self.volume_bar.setMaximum(self.bar_mxValue)
        self.volume_bar.setValue(self.bar_mxValue / 5)
        # 播放时间进度条
        self.time_bar = QSlider(Qt.Horizontal)
        self.time_bar.setObjectName('slider_bar')
        self.time_bar.setFocusPolicy(Qt.NoFocus)  # 表示不接收键盘焦点
        self.time_bar.setMinimum(0)
        self.time_bar.setMaximum(self.bar_mxValue)

        # 进度条槽函数连接,我们还重写了eventFilter函数来拦截bar的点击事件,然后setValue和self.player.position。
        self.time_bar.sliderMoved.connect(self.time_bar_slider_moved)  # 拖动时间进度条的指针来改变媒体流播放位置
        self.volume_bar.sliderMoved.connect(self.volume_bar_slider_moved)  # 拖动音量进度条的指针来改变媒体流音量大小

        # 进度条左右的时间标签,格式为minites:seconds
        self.left_time_label = QLabel('')
        self.left_time_label.setObjectName('left_time_label')
        self.right_time_label = QLabel('')
        self.left_time_label.setObjectName('right_time_label')

        # 音量图标
        self.volume_label = QPushButton(qtawesome.icon('ri.volume-up-fill', color='red'), '')
        # 播放按钮
        self.play_btn = QPushButton(qtawesome.icon('fa5s.play', color='red'), '')
        self.play_btn.setObjectName('play_widget_btn')
        self.play_btn.setToolTip('播放')
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.setShortcut('space')
        self.play_btn.clicked.connect(self.play_btn_clicked)
        # 播放mode按钮（包括一次性、单曲、随机、顺序）
        self.mode_btn = QPushButton(qtawesome.icon('ph.repeat-once-bold', color='red'), '')
        self.mode_btn.setObjectName('play_widget_btn')
        self.mode_btn.setCursor(Qt.PointingHandCursor)
        self.mode_btn.clicked.connect(self.mode_btn_clicked)
        self.mode_btn.setToolTip('单曲播放')
        # 上一首、下一首按钮
        self.nxt_btn = QPushButton(qtawesome.icon('mdi6.skip-next', color='red'), '')
        self.nxt_btn.setObjectName('play_widget_btn')
        self.nxt_btn.setCursor(Qt.PointingHandCursor)
        self.nxt_btn.clicked.connect(self.nxt_btn_clicked)
        self.nxt_btn.setToolTip('下一首')

        self.previous_btn = QPushButton(qtawesome.icon('mdi6.skip-previous', color='red'), '')
        self.previous_btn.setObjectName('play_widget_btn')
        self.previous_btn.setCursor(Qt.PointingHandCursor)
        self.previous_btn.clicked.connect(self.previous_btn_clicked)
        self.previous_btn.setToolTip('上一首')

        # 音乐名按钮标签、专辑标签
        self.music_name_label = QMusicPushButton('')
        self.music_name_label.clicked.connect(self.more_info_btn_clicked)  # 点击正在播放的歌曲名字也可以调出更多信息
        self.music_name_label.setCursor(Qt.PointingHandCursor)
        self.music_name_label.setObjectName('music_name_label')

        self.music_album_label = QLabel('')
        self.music_album_label.setObjectName('music_album_label')
        # 布置right_play_widget
        self.right_play_layout.addWidget(self.music_name_label, 0, 0, 1, 5)
        self.right_play_layout.addWidget(QLabel(''), 0, 5, 1, 2)
        self.right_play_layout.addWidget(self.left_time_label, 0, 7, 1, 1)
        self.right_play_layout.addWidget(self.time_bar, 0, 8, 1, 8)
        self.right_play_layout.addWidget(self.right_time_label, 0, 16, 1, 1)
        self.right_play_layout.addWidget(QLabel(''), 0, 17, 1, 7)

        self.right_play_layout.addWidget(self.music_album_label, 1, 0, 1, 5)
        self.right_play_layout.addWidget(self.previous_btn, 1, 10, 1, 1)
        self.right_play_layout.addWidget(self.play_btn, 1, 11, 1, 1)
        self.right_play_layout.addWidget(self.nxt_btn, 1, 12, 1, 1)
        self.right_play_layout.addWidget(self.mode_btn, 1, 18, 1, 1)
        self.right_play_layout.addWidget(self.volume_label, 1, 20, 1, 1)
        self.right_play_layout.addWidget(self.volume_bar, 1, 21, 1, 3)

    def init_local_widget(self):
        # 文件路径设置btn
        self.folder_path_set_btn = QPushButton(qtawesome.icon('fa5s.folder-open', color='red'), '')
        self.folder_path_set_btn.clicked.connect(self.folder_path_set_btn_clicked)
        self.folder_path_set_btn.setObjectName('folder_path_set_btn')
        self.folder_path_set_btn.setCursor(Qt.PointingHandCursor)
        self.folder_path_set_btn.setToolTip('设置文件夹路径')
        # label
        self.local_title_label = QLabel('本地歌单列表')
        self.local_title_label.setObjectName('title_label')

        # 布置local_layout
        self.right_local_layout.addWidget(self.folder_path_set_btn, 0, 0, 1, 1)
        self.right_local_layout.addWidget(self.local_title_label, 0, 1, 1, 2)
        self.right_local_layout.addWidget(QLabel(''), 0, 3, 1, 7)
        self.local_playlist_ui = local_playlist_ui(self, '')
        self.right_local_layout.addWidget(self.local_playlist_ui, 1, 0, 12, 10)

    def init_playlist_widget(self):
        '''
        init self.right_playlist_widget
        该widget布置了所有歌的分类，以及布置playlist的QscrollArea

        :return:
        '''
        # 初始化歌单类别选择界面
        self.language_label = QPushButton(qtawesome.icon('ri.earth-fill', color='red'), '语言')
        self.right_playlist_layout.addWidget(self.language_label, 0, 0, 1, 1)
        self.language_label.setFixedSize(QSize(80, 30))
        self.language_label.setObjectName('type_label')

        self.style_label = QPushButton(qtawesome.icon('mdi.piano', color='red'), '风格')
        self.right_playlist_layout.addWidget(self.style_label, 1, 0, 1, 1)
        self.style_label.setFixedSize(QSize(80, 30))
        self.style_label.setObjectName('type_label')

        self.scene_label = QPushButton(qtawesome.icon('ph.coffee-fill', color='red'), '场景')
        self.right_playlist_layout.addWidget(self.scene_label, 3, 0, 1, 1)
        self.scene_label.setFixedSize(QSize(80, 30))
        self.scene_label.setObjectName('type_label')

        self.emotion_label = QPushButton(qtawesome.icon('ph.smiley-x-eyes', color='red'), '情感')
        self.right_playlist_layout.addWidget(self.emotion_label, 4, 0, 1, 1)
        self.emotion_label.setFixedSize(QSize(80, 30))
        self.emotion_label.setObjectName('type_label')

        self.theme_label = QPushButton(qtawesome.icon('ph.music-note-simple', color='red'), '主题')
        self.right_playlist_layout.addWidget(self.theme_label, 5, 0, 1, 1)
        self.theme_label.setFixedSize(QSize(80, 30))
        self.theme_label.setObjectName('type_label')

        # 设置所有cls button
        self.cls_btns = []
        row = [0, 1, 3, 4, 5]
        for i, cls_list in enumerate(self.playlist_cls):
            now = 0
            for cls in cls_list[1:]:
                new_btn = QPushButton(cls)
                new_btn.setObjectName('cls_btn')
                # 连接槽函数。
                new_btn.clicked.connect(self.cls_btn_clicked)
                new_btn.setCursor(Qt.PointingHandCursor)
                new_btn.setFixedSize(QSize(70, 25))
                self.right_playlist_layout.addWidget(new_btn, row[i] + now // 12, now % 12 + 1, 1, 1)
                self.cls_btns.append(new_btn)
                now += 1
        # 设置分割线
        self.split_line = QPushButton(' ' * 11 + '序号'.ljust(8, ' ') + '音乐标题'.ljust(41, ' ')
                                      + '歌手'.ljust(45, ' ') + '专辑'.ljust(42, ' ') + '格式转换')
        self.split_line.setObjectName('split_line')
        self.right_playlist_layout.addWidget(self.split_line, 7, 0, 1, 13)
        self.split_line.setMinimumHeight(30)
        self.cls_btns[-1].click()
        # 歌单区域

    @pyqtSlot()
    def nxt_btn_clicked(self):
        '''
        下一首按钮单击槽函数。
        下一首的逻辑很简单，维护一个seq和seq_cursor,如果seq_cursor在中间，就播放seq_cursor+1对应index的音乐。
        如果seq_cursor在末，就根据当前模式获取下一首，注意如果是单曲播放会按顺序模式的方法播放下一首。
        这个flag=1就是强制将单曲模式下点击nxt_btn变为顺序的情况，因为自动播放下一首对于单曲播放模式而言是循环同一首歌曲。

        :return:
        '''
        if self.now_play_music == None:
            msg = QMessageBox.warning(self, 'error', "请先双击一首音乐....", buttons=QMessageBox.Ok)
            return
        if 0 <= self.play_seq_cursor < len(self.play_seq) - 1:
            self.play_seq_cursor += 1
            music = self.musics_list[self.page_now][self.play_seq[self.play_seq_cursor]]
            if self.page_now != 2:  # 分类歌单和歌手热门歌单music是Music的实例对象。
                path = self.get_music_file_path(music)
                self.set_player_media(path, music=music)
            else:  # 如果是本地歌单,music就是对应音乐的绝对路径。
                self.set_player_media(music, music_name=music.split(sep='/')[-1][:-4])
        else:
            nxt_music, nxt_seq = self.get_nxtmusic(flag=1)
            if self.page_now != 2:
                path = self.get_music_file_path(nxt_music)
                if path != '':
                    self.set_player_media(path, nxt_music)
                    self.play_seq.append(nxt_seq)
                    self.play_seq_cursor = len(self.play_seq) - 1
            else:
                self.set_player_media(nxt_music, music_name=nxt_music.split(sep='/')[-1][:-4])
                self.play_seq.append(nxt_seq)
                self.play_seq_cursor = len(self.play_seq) - 1

    @pyqtSlot()
    def previous_btn_clicked(self):
        '''
        上一首播放按钮单击槽函数
        实现逻辑与下一首播放按钮的逻辑相同，这里不再阐述

        :return:
        '''
        if self.now_play_music == None:
            msg = QMessageBox.warning(self, 'error', "请先双击一首音乐....", buttons=QMessageBox.Ok)
            return
        if 1 <= self.play_seq_cursor <= len(self.play_seq) - 1:
            self.play_seq_cursor -= 1
            music = self.musics_list[self.page_now][self.play_seq[self.play_seq_cursor]]
            if self.page_now != 2:
                path = self.get_music_file_path(music)
                self.set_player_media(path, music)
            else:
                self.set_player_media(music, music_name=music.split(sep='/')[-1][:-4])
        else:  # cursor在play_seq的首地址上的情况
            nxt_music, nxt_seq = self.get_nxtmusic(flag=1, offset=-1)
            if self.page_now != 2:
                path = self.get_music_file_path(nxt_music)
                if path != '':
                    self.set_player_media(path, nxt_music)
                    self.play_seq.insert(0, nxt_seq)
                    self.play_seq_cursor = self.play_seq_cursor  # 即0
            else:
                self.set_player_media(nxt_music, music_name=nxt_music.split(sep='/')[-1][:-4])  # nxt_music就是路径
                self.play_seq.insert(0, nxt_seq)
                self.play_seq_cursor = self.play_seq_cursor  # 即0

    @pyqtSlot()
    def mode_btn_clicked(self):
        '''
        模式切换btn
        0单曲,1顺序,2随机

        :return:
        '''
        self.mode = (self.mode + 1) % 3
        icon_tag = ['ph.repeat-once-bold', 'ri.order-play-fill', 'fa.random']
        hints = ['单曲播放', '顺序播放', '随机播放']
        self.mode_btn.setIcon(qtawesome.icon(icon_tag[self.mode], color='red'))
        self.mode_btn.setToolTip(hints[self.mode])

    @pyqtSlot()  # 歌手信息搜索,展示歌手信息
    def search_singer_btn_clicked(self):
        '''
        歌手信息搜索,展示歌手信息

        :return:
        '''
        txt = self.rec_name_label.text()
        if len(self.rec_name_label.text()) == 5:
            msg = QMessageBox.warning(self, 'error', "尚未识别....", buttons=QMessageBox.Ok)
            return
        self.right_rec_layout.removeWidget(self.singer_info_ui)
        self.singer_info_ui = singer_info_ui(self, self.rec_name_label.text()[5:])
        self.right_rec_layout.addWidget(self.singer_info_ui, 2, 0, 10, 10)

    @pyqtSlot()
    def folder_path_set_btn_clicked(self):
        '''
        本地播放歌单文件夹的选择

        :return:
        '''
        path = QFileDialog.getExistingDirectory(self, '选择音频文件目录(务必为mp3类型)', r'./')
        if path == '':
            return
        self.right_local_layout.removeWidget(self.local_playlist_ui)
        self.local_playlist_ui = local_playlist_ui(self, path)
        self.right_local_layout.addWidget(self.local_playlist_ui, 2, 0, 10, 12)

    @pyqtSlot()  # 音频文件路径选择
    def path_set_btn_clicked(self):
        '''
        音频文件路径选择

        :return:
        '''
        path = QFileDialog.getOpenFileName(self, '请选择wav音频文件', r'./')[0]
        if path == '':
            return
        if not path[-4:] == '.wav':  # 格式错误
            msg = QMessageBox.warning(self, 'error', '文件格式错误....', buttons=QMessageBox.Ok)
            return
        self.rec_path = path
        print('已设置音频文件为' + path)

    @pyqtSlot()  # 识别按钮
    def rec_btn_clicked(self):
        '''
        识别按钮槽函数,对self.rec_path路径的音频文件进行相似度检测识别。

        :return:
        '''
        if self.rec_path == '':
            msg = QMessageBox.warning(self, 'error', "未录制或者未选择音频路径....", buttons=QMessageBox.Ok)
            return
        if not os.path.exists(self.rec_path):
            msg = QMessageBox.warning(self, 'error', "路径错误....", buttons=QMessageBox.Ok)
            return
        print('正在识别......')
        name, similarity = self.recognition(self.rec_path)
        self.rec_name_label.setText('识别结果:' + name)
        self.similarity_label.setText('相似度:' + str("%.4f" % (similarity)))
        print('识别成功！')
        self.sound_player.setMedia(QMediaContent(QUrl('./otherFiles/sounds/ding.mp3')))
        self.sound_player.play()

    @pyqtSlot()
    def record_btn_clicked(self):
        '''
        录制按钮单击事件槽函数，单击进行录音，与录音模块对接

        :return:
        '''
        print('开始录制......')
        record_audio_path = self.record_audio.record(self.record_progress_bar, './otherFiles/temp.wav', record_seconds=3)
        self.rec_path = record_audio_path

    @pyqtSlot()
    def close_btn_clicked(self):
        '''
        关闭按钮单击事件槽函数，单击后删除临时音乐文件并关闭主窗口

        :return:
        '''
        rt_path = './temp_music_file'
        id_list = os.listdir(rt_path)
        for music_id in id_list:
            son_path = rt_path + '/' + music_id
            music_name_list = os.listdir(son_path)
            for music_name in music_name_list:
                os.remove(son_path + '/' + music_name)
            os.rmdir('./temp_music_file/' + music_id)
        print('已成功释放临时文件，并退出主窗口！')
        self.close()

    @pyqtSlot()
    def time_bar_slider_pressed(self, value):
        if self.player.isAudioAvailable():
            self.player.setPosition(self.player.duration() * value / self.bar_mxValue)
        self.time_bar.setValue(value)

    @pyqtSlot()
    def volume_bar_slider_moved(self):
        '''
        音量进度条拖动槽函数，将媒体流音量大小改变为拖动时音量进度条的相应位置

        :return:
        '''
        value = self.volume_bar.value()
        if self.player.isAudioAvailable():
            self.player.setVolume(int(value / self.bar_mxValue * 100))

    @pyqtSlot()
    def time_bar_slider_moved(self):
        '''
        播放进度条拖动槽函数，将播放媒体流位置改变为拖动时进度条的相应位置

        :return:
        '''
        value = self.time_bar.value()
        if self.player.isAudioAvailable():
            self.player.setPosition(self.player.duration() * value / self.bar_mxValue)

    @pyqtSlot()
    def play_timer_timeout(self):
        '''
        媒体流播放计时器超时槽函数，用来动态跟踪播放进度条

        :return:
        '''
        # 根据当前媒体流播放的positon/ms 获得left、right time。
        left_time = time.strftime('%M:%S', time.localtime(self.player.position() / 1000))
        right_time = time.strftime('%M:%S', time.localtime(self.player.duration() / 1000))
        self.left_time_label.setText(left_time)
        self.right_time_label.setText(right_time)

        try:
            time_bar_pos = self.player.position() / self.player.duration() * self.bar_mxValue
        except ZeroDivisionError:
            time_bar_pos = 0
        self.time_bar.setValue(int(time_bar_pos))

        # 特判播放结束的情况
        if self.player.position() == self.player.duration():
            self.is_pause = 1
            self.play_timer.stop()
            self.play_btn.setIcon(qtawesome.icon('fa5s.play', color='red'))
            self.play_btn.setToolTip('播放')
            self.player.pause()

            # 超时后将根据mode播放模式设置nxt即新的音乐进行播放
            music, seq = self.get_nxtmusic(flag=0)
            if self.page_now != 2:
                path = self.get_music_file_path(music)
                if path != '':
                    self.set_player_media(path, music)
            else:  # 本地歌单,music即音乐路径
                self.set_player_media(music, music_name=music.split(sep='/')[-1][:-4])
            if self.mode != 0:  # 单曲循环play_seq不用改变。
                self.play_seq = self.play_seq[:self.play_seq_cursor + 1]
                self.play_seq.append(seq)
                self.play_seq_cursor = len(self.play_seq) - 1

    @pyqtSlot()
    def cls_btn_clicked(self):
        '''
        cls_btn单击事件槽函数,爬取对应分类歌单歌曲并布置scrollArea以显示歌单

        :return:
        '''
        cls_name = self.sender().text()
        self.scroll = QScrollArea()
        self.scroll.setFixedHeight(300)  # 给play_widget腾出空间。
        self.scroll.setObjectName('scroll')

        self.scroll_layout = QGridLayout()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.right_playlist_layout.addWidget(self.scroll, 8, 0, 16, 13)
        # # selenium实时爬虫
        # ids=get_playlist(cls_name)
        # musics = get_info([ids])

        # 静态歌曲id
        ids = id_dict[cls_name]
        rdm = random.randint(1, 20)
        musics = get_info([str(ids[rdm])])
        self.musics_list[0] = []
        for i, music in enumerate(musics):
            # song_btn为重写的QDoublePushButton,支持双击播放歌曲。
            song_btn = QDoublePushButton()
            song_btn.setObjectName('song_btn')
            song_btn.music = music  # 绑定music对象。
            song_btn.doubleClicked.connect(self.song_btn_doubleClicked)
            song_btn.setFixedSize(QSize(900, 25))

            # 歌的序号、标题、歌手等信息标签
            label_seq = QLabel(str(i + 1).rjust(2, '0'))
            label_title = QLabel(self.align_left(music.name, 20, 25))
            label_singer = QLabel(self.align_left(music.artist[0], 20, 25))
            label_album = QLabel(self.align_left(music.album, 20, 25))
            label_m4a_flag = QPushButton(
                qtawesome.icon('fa.check', color='red') if music.type == 'm4a' else qtawesome.icon(
                    'fa.times', color='red'), '')  # 如果是m4a类型的需要格式转化，加上下载时间，耗时较长
            self.musics_list[0].append(music)
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
            download_btn.clicked.connect(self.download_btn_clicked)

            # 更多信息按钮,即查看评论信息等
            more_info_btn = QMusicPushButton(qtawesome.icon('ri.more-2-fill', color='gray'), '')
            more_info_btn.setObjectName('operate_btn')
            more_info_btn.setCursor(Qt.PointingHandCursor)
            more_info_btn.setToolTip('查看详细信息')
            more_info_btn.music = music
            more_info_btn.setFixedSize(QSize(20, 20))
            more_info_btn.clicked.connect(self.more_info_btn_clicked)

            # 打开url按钮
            open_music_url_btn = QMusicPushButton(qtawesome.icon('ph.link-simple-horizontal-fill', color='gray'), '')
            open_music_url_btn.setObjectName('operate_btn')
            open_music_url_btn.setCursor(Qt.PointingHandCursor)
            open_music_url_btn.setToolTip('打开歌曲链接')
            open_music_url_btn.music = music
            open_music_url_btn.setFixedSize(QSize(20, 20))
            open_music_url_btn.clicked.connect(self.open_music_url_btn_clicked)

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

    @pyqtSlot()
    def download_btn_clicked(self):
        '''
        下载按钮单击事件槽函数,单击以下载歌曲到指定的本地文件

        :return:
        '''
        music = self.sender().music
        path = './cloudmusic'
        limit_try_download = 100
        while 1:  # 这里可能网络不好需要多次请求下载
            limit_try_download -= 1
            if not limit_try_download:
                print('下载失败....')
                return
            b = music.download(path, level='standard')
            if b != None:
                if music.type == 'm4a':  # 将m4a格式转化为mp3格式,并删除m4a格式的歌曲。
                    song_file_names = os.listdir(path)
                    song_file_name = [x for x in song_file_names if x[-3:] == 'm4a'][0]
                    utils.format_cvt.trans_m4a_to_other(rt_path=path, file_name=song_file_name)
                    os.remove(path + '/' + song_file_name)
                break
        print(music.name + ' 下载成功至./cloudmusic....')

    @pyqtSlot()
    def local_song_btn_doubleClicked(self):
        '''
        该槽函数针对本地歌单的音乐双击进行处理。
        本地歌单每个音乐按钮由于只有音乐的路径信息,因此播放相关的操作和分类歌单以及声纹识别歌单相异,不过他们都是使用主窗口的媒体流即self.player进行播放。
        同样的,他们下一首、上一首，随机、顺序播放的逻辑相同。只是我们在设置媒体流时需要根据是否是本地歌单来做一些调整。

        :return:
        '''
        self.page_now = 2
        # 双击了音乐，相当于到了一个新的位置，我们跟踪的play_seq就得清空。
        self.play_seq = []
        self.play_seq_cursor = -1
        # 初始化play_seq,便于实现上一首、下一首逻辑。
        path = self.sender().music_path
        self.set_player_media(path, music_name=path.split(sep='/')[-1][:-4])
        seq = self.musics_list[self.page_now].index(path)
        self.play_seq.append(seq)
        self.play_seq_cursor = 0

    @pyqtSlot()
    def song_btn_doubleClicked(self):
        '''
        该槽函数只针对分类歌单和歌手热门歌单歌曲的音乐双击。
        双击按钮双击事件槽函数获得music。同时获得当前正在播放音乐的主界面是谁？因为只有播放了音乐才算切换了主界面,方便我们定位musics_list。

        :return:
        '''
        if self.right_stackedwidget.currentWidget() == self.right_playlist_widget:
            self.page_now = 0
        else:
            self.page_now = 1
        music = self.sender().music

        # 双击了音乐，相当于到了一个新的位置，我们跟踪的play_seq就得清空。
        self.play_seq = []
        self.play_seq_cursor = -1
        # 初始化play_seq,便于实现上一首、下一首逻辑。
        path = self.get_music_file_path(music)
        if path != '':  # path为''是临时文件下载失败的原因,不为''才能播放。
            self.set_player_media(path, music)
            seq = self.musics_list[self.page_now].index(music)
            self.play_seq.append(seq)
            self.play_seq_cursor = 0

    @pyqtSlot()
    def play_btn_clicked(self):
        '''
        播放按钮单击事件槽函数
        控制当前媒体流播放音乐的 播放/暂停 动作。

        :return:
        '''
        if not self.player.isAudioAvailable():  # 查看媒体流
            msg = QMessageBox.warning(self, 'error', "没选中任何音乐进行播放！", buttons=QMessageBox.Ok)
            return
        if self.is_pause:
            # 当前媒体流是暂停状态,点击play_btn后进入播放状态
            self.is_pause = 0
            self.play_btn.setIcon(qtawesome.icon('fa.pause-circle-o', color='red'))
            self.play_btn.setToolTip('暂停')
            self.play_timer.start(100)  # 跟踪进度条
            self.player.play()
        else:
            self.is_pause = 1
            self.play_timer.stop()
            self.play_btn.setIcon(qtawesome.icon('fa5s.play', color='red'))
            self.play_btn.setToolTip('播放')
            self.player.pause()

    @pyqtSlot()
    def open_music_url_btn_clicked(self):
        '''
        源连接按钮单击事件槽函数，单击打开歌曲原链接

        :return:
        '''
        url = "https://music.163.com/#/song?id=" + str(self.sender().music.id)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    @pyqtSlot()
    def more_info_btn_clicked(self):
        '''
        详细信息单击事件槽函数，单击按钮将利用爬虫爬取歌曲信息并构造窗口music_info_ui进行可视化

        :return:
        '''
        music = self.sender().music
        if music == None:
            return
        self.song_widget = music_info_ui(music)
        self.song_widget.show()

    @pyqtSlot()
    def playlist_btn_clicked(self):
        '''
        分类歌单单击事件槽函数，切换分类歌单功能模块

        :return:
        '''
        self.right_stackedwidget.setCurrentWidget(self.right_playlist_widget)

    @pyqtSlot()
    def local_btn_clicked(self):
        self.right_stackedwidget.setCurrentWidget(self.right_local_widget)

    @pyqtSlot()
    def rec_interface_btn_clicked(self):
        '''
        声纹识别单击事件槽函数，切换分类声纹识别模块

        :return:
        '''
        self.right_stackedwidget.setCurrentWidget(self.right_rec_widget)

    def get_nxtmusic(self, flag=0, offset=1):
        '''
        根据当前模式和当前播放音乐在musics_list的index找到下一首要播放的音乐以及其index。

        :param flag: flag=1；将单曲模式下的单曲循环变为顺序播放的方法(自动播放下一首时是单曲循环,单击下一首按钮时采取后者的方法)。
        :param offset: 我们这个nxt是广义上的,可以是+1，也可以是-1。offset=-1对应单击上一首按钮的情况。
        :return: 注意,本地歌单返回的music,seq,其中music并非Music实例,而是音乐的绝对路径。
        '''
        seq = self.play_seq[self.play_seq_cursor]  # 当前播放的音乐在musics_list[now_page]下的index。
        if self.mode == 0:  # 单曲
            if flag == 1:  # 播放musics_list[now_page]的seq+1首音乐。
                nxt_seq = (seq + offset) % len(self.musics_list[self.page_now])
                return self.musics_list[self.page_now][nxt_seq], nxt_seq
            return self.now_play_music, seq
        elif self.mode == 1:  # 顺序
            nxt_seq = (seq + offset) % len(self.musics_list[self.page_now])
            return self.musics_list[self.page_now][nxt_seq], nxt_seq
        else:
            rdm = random.randint(0, len(self.musics_list[self.page_now]) - 1)
            return self.musics_list[self.page_now][rdm], rdm

    def get_music_file_path(self, music):
        '''
        该方法针对分类歌单和歌手热门歌单

        :param music: Music实例对象
        :return: 返回临时音乐文件的绝对路径,以设置媒体流。如果返回'',则说明下载失败。

        '''
        music_id, music_type = music.id, music.type
        path = './temp_music_file' + '/' + music_id  # music的临时dir
        if not self.download_flag.get(music_id, 0):  # 没有下载过
            if not os.path.exists(path):
                os.makedirs(path)
            limit_try_download = 10000
            while 1:  # 这里可能网络不好需要多次请求下载
                limit_try_download -= 1
                if not limit_try_download:
                    print('播放失败....')
                    return ''
                b = music.download(path, level='standard')
                if b != None:
                    break
            self.download_flag[music_id] = 1
            if music.type == 'm4a':  # 将m4a格式转化为mp3格式,并删除m4a格式的歌曲。
                song_file_name = os.listdir(path)[0]
                utils.format_cvt.trans_m4a_to_other(rt_path=path, file_name=song_file_name)
                os.remove(path + '/' + song_file_name)
        song_file_name = os.listdir(path)[0]  # 注意这是一个list
        return path + '/' + song_file_name

    def set_player_media(self, music_file_path, music=None, music_name='', artist=''):
        '''
        self.player的媒体流设置为music_file_path所在路径的音频,务必保证为mp3文件。

        :param music_file_path: 音频绝对路径,必须的参数
        :param music: Music实例
        :param music_name:
        :param artist_and_album:
        :return:
        '''

        self.player = QMediaPlayer()  # 创建新的媒体流
        self.player.setMedia(QMediaContent(QUrl(music_file_path)))  # 设置媒体流为该当前music
        self.player.setVolume(int(self.volume_bar.value() / self.bar_mxValue * 100))
        self.player.play()
        # 跟踪播放时间
        self.play_timer.start(100)
        # 设置播放的名称和专辑名
        if music != None:  # 在线播放,用Music实例设置相关label。
            self.now_play_music = music
            self.music_name_label.setText(music.name)
            self.music_name_label.setToolTip(music.name)
            self.music_name_label.music = music
            self.music_album_label.setText('   ' + music.artist[0] + ' - ' + music.album)
        else:  # 没有Music实例,对应本地歌单的情况,只使用音乐文件的绝对地址来设置相关信息
            self.now_play_music = music_file_path
            self.music_name_label.setText(music_name)
            self.music_name_label.setToolTip(music_name)
            self.music_name_label.music = None
            self.music_album_label.setText(artist)
        self.play_btn.setIcon(qtawesome.icon('fa.pause-circle-o', color='red'))
        self.play_btn.setToolTip('暂停')
        self.is_pause = 0

    def recognition(self, audio_path):
        '''
        录音音频和本地数据库计算余弦距离。返回余弦距离最小的本地数据库歌手名称。

        :param audio_path: 当前要识别的音频绝对路径
        :return:
        '''
        name = ''
        pro = 0
        feature = self.infer(audio_path)[0]
        for i, person_f in enumerate(list(self.local_audio_features)):
            dist = np.dot(feature, person_f) / (np.linalg.norm(feature) * np.linalg.norm(person_f))
            if dist > pro:
                pro = dist
                name = self.singer_name[i]
        return name, pro

    def infer(self, audio_path):
        '''
        声纹识别函数,返回audio_path音频文件提取的(512.)维特征向量。

        :param audio_path:wav文件的地址
        :return:
        '''
        input_shape = (1, 257, 257)
        data = load_audio(audio_path, mode='infer', spec_len=input_shape[2])
        data = data[np.newaxis, :]
        data = torch.tensor(data, dtype=torch.float32, device=self.device)
        # 执行预测
        feature = self.model(data)
        return feature.data.cpu().numpy()

    def align_left(self, s, limit_width, total_width):
        '''
        自定义左对齐函数。这里假设width:中文=2英文
        limit_width的单位是一个英文
        :param s:
        :param limit_width:限制s的宽度,超过的用...填充
        :param total_width:总宽度,超过limit_width以及...的用' '填充
        :return:
        '''
        cut_pos = 0
        w = 0
        for i in range(len(s)):
            t = 2 if ord(s[i]) > 255 else 1
            if w + t > limit_width:
                break
            w += t
            cut_pos = i
        if cut_pos == len(s) - 1:  # 没有超过规定宽度;根据total_width和w算出填充的0即可。
            return s + ' ' * (int(total_width - w))
        # 超过宽度,省略号加上
        return s[:cut_pos + 1] + '...' + ' ' * (int(total_width - w - 3))

    # 无边框的拖动
    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        # 重写移动事件
        try:
            self._endPos = e.pos() - self._startPos
            self.move(self.pos() + self._endPos)
        except:
            return

    def mousePressEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.LeftButton:
            self._isTracking = True
            self._startPos = QtCore.QPoint(e.x(), e.y())

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None

    def eventFilter(self, obj, event):
        '''
        重写事件过滤函数,在本项目中用来点击time_bar和volume_bar时，直接将对应的slider的value设置为鼠标点击位置。

        :param obj:
        :param event:
        :return:
        '''
        if obj.inherits('QPushButton'):
            if obj.objectName() in ['cls_btn', 'left_btn', 'play_widget_btn', 'operate_btn', 'rec_widget_btn',
                                    'folder_path_set_btn','close_btn']:
                if event.type() == QEvent.MouseButtonPress:
                    mouse_e = event
                    if mouse_e.button() == Qt.LeftButton:
                        self.sound_player.setMedia(QMediaContent(QUrl('./otherFiles/sounds/btn.mp3')))
                        self.sound_player.play()
        if obj.objectName() == 'slider_bar':
            if event.type() == QEvent.MouseButtonPress:
                mouse_e = event
                if mouse_e.button() == Qt.LeftButton:
                    value = QStyle.sliderValueFromPosition(obj.minimum(), obj.maximum(),
                                                           mouse_e.pos().x(), obj.width())
                    obj.setValue(value)
                    if self.player.isAudioAvailable():  # 如果有播放源媒体流
                        if obj == self.time_bar:  # 将播放位置设置为当前点击位置
                            self.player.setPosition(value / self.bar_mxValue * self.player.duration())
                        else:  # 将播放音量设置为当前点击位置对应音量
                            self.player.setVolume(value / self.bar_mxValue * 100)
        return super().eventFilter(obj, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainUi()
    mainWindow.show()
    app.installEventFilter(mainWindow)
    sys.exit(app.exec_())
