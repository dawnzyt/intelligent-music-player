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


class music_info_ui(QWidget):
    def __init__(self, music):
        super().__init__()
        self.music = music
        self.init_vars()
        self.init_ui()
        self.init_style()

    def init_vars(self):
        # music_url即歌曲的网页地址
        self.music_url = "https://music.163.com/#/song?id=" + str(self.music.id)  # 歌曲原链接
        self.img = self.get_img_from_url(self.music.picUrl)  # 歌曲图片
        self.comment_flag = 0  # 记录是否加载了评论区

    def init_style(self):
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)  # 隐藏边框
        self.setWindowOpacity(0.95)  # 设置窗口不透明度
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.main_layout.setSpacing(0)
        self.main_widget.setStyleSheet('''
            QWidget{
                border:none; 
            }
            QWidget#main_widget{
                background:white;
                border-top:2px solid black;
                border-right:2px solid black;
                border-left:2px solid black;
                border-bottom:2px solid black;
                border-radius:18px; 
            }
        ''')
        self.song_info_widget.setStyleSheet('''
            QLabel#name_label{
                font-size:30px;
                font-weight:1000;
            }
            QLabel#title_album_label{
                font-size:12px;
                color:gray;
                font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;
            }
            QPushButton#comment_btn:hover{
                font-weight:700;
                font-size:16px;
                color:red;
            }
        ''')

    def init_ui(self):
        self.setFixedSize(QSize(800, 600))
        self.setObjectName('self')
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # main_widget初始化
        self.main_widget = QWidget()
        self.main_layout = QGridLayout()  # main_widget layout
        self.main_widget.setLayout(self.main_layout)
        self.main_widget.setObjectName('main_widget')
        self.layout.addWidget(self.main_widget)
        # 布置self
        self.init_main_widget()

    def init_main_widget(self):
        # 在未布置评论区部件内容时,main_layout中添加一个song_info_widget;不显示评论区内容
        self.song_info_widget = QWidget()
        self.song_info_layout = QGridLayout()
        self.song_info_widget.setLayout(self.song_info_layout)
        self.main_layout.addWidget(self.song_info_widget)

        # name_label
        self.name_label = QLabel(self.music.name)
        self.name_label.setObjectName('name_label')

        # title_label
        self.title_album_label = QLabel(self.music.artist[0] + ' - ' + self.music.album)
        self.title_album_label.setObjectName('title_album_label')

        # 音乐的图片 img_label
        self.img_label = self.draw_circle_label(QLabel(), self.img, mx_w=300, mx_h=300)
        self.img_label.setObjectName('img_label')
        # close_btn
        self.close_btn = QPushButton(qtawesome.icon('fa.close', color='red'), '')
        self.close_btn.setObjectName('close_btn')
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)

        # 显示评论区内容的 comment_btn
        self.comment_btn = QPushButton(qtawesome.icon('fa5.circle', color='purple'), '查看评论')
        self.comment_btn.setObjectName('comment_btn')
        self.comment_btn.setFixedSize(QSize(725, 30))
        self.comment_btn.clicked.connect(self.comment_btn_clicked)
        self.comment_btn.setCursor(Qt.OpenHandCursor)

        # 布置song_info_layout
        self.song_info_layout.addWidget(QLabel(''), 0, 0, 5, 1)
        self.song_info_layout.addWidget(self.close_btn, 0, 11, 1, 1)
        self.song_info_layout.addWidget(QLabel(''), 1, 11, 4, 1)
        self.song_info_layout.addWidget(self.img_label, 0, 1, 5, 10)
        self.song_info_layout.addWidget(self.name_label, 5, 0, 2, 12)
        self.song_info_layout.addWidget(self.title_album_label, 7, 0, 1, 12)
        self.song_info_layout.addWidget(QLabel(''), 8, 0, 2, 12)
        self.song_info_layout.addWidget(self.comment_btn, 10, 0, 2, 12)
        # 居中对齐
        self.song_info_layout.setAlignment(self.img_label, QtCore.Qt.AlignCenter)
        self.song_info_layout.setAlignment(self.name_label, QtCore.Qt.AlignCenter)
        self.song_info_layout.setAlignment(self.title_album_label, QtCore.Qt.AlignCenter)

    @pyqtSlot()
    def comment_btn_clicked(self, num=10):
        '''
        评论按钮单击事件槽函数
        当comment_btn激活时，我们获取前10hot comments来展示评论区的内容。
        定义一个scrollArea并将song_info_widget添加进来。
        后面在scroll_layout陆续添加评论区的内容部件

        :param num:
        :return:
        '''
        if self.comment_flag:
            # 这里是判断是否已经加载过评论区了。
            return
        self.comment_flag = 1
        self.song_info_widget.setMaximumWidth(705)  # 限制宽度,防止出现左右滑动滚轮。
        self.main_layout.removeWidget(self.song_info_widget)  # remove song_info_widget,我们将其添加到scrollArea内。
        # 初始化滑动区域
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout()
        self.scroll_widget.setLayout(self.scroll_layout)

        self.scroll_layout.addWidget(self.song_info_widget, 0, 0, 8, 12)

        # 获取评论及其相关内容
        comment_count = self.music.getCommentsCount()
        comments = self.music.getHotComments(number=5)
        self.comment_label = QLabel('评论数(' + str(comment_count) + ')')
        self.scroll_layout.addWidget(self.comment_label, 9, 0)
        self.scroll_layout.setAlignment(self.comment_label, QtCore.Qt.AlignLeft)
        for i, comment in enumerate(comments):
            comment_widget = QWidget()
            comment_layout = QGridLayout()
            comment_widget.setLayout(comment_layout)

            # 获取评论相关内容
            avatarUrl = comment['avatarUrl']  # 头像地址
            avatar_img = self.get_img_from_url(avatarUrl)
            likes = comment['likeCount']
            tim = comment['time']
            user_name = comment['nickName']
            text = comment['content']

            # 利用相关内容对comment_widget进行布置
            avatar_label = self.draw_circle_label(QLabel(), avatar_img)  # 头像

            # 评论内容
            pl_text = QPlainTextEdit()
            pl_text.setPlainText(text)
            pl_text.setMinimumWidth(600)
            pl_text.setMaximumWidth(600)
            pl_text.verticalScrollBar().setStyleSheet('''QScrollBar:vertical{width:0px;}''')
            pl_text.setStyleSheet(
                '''font-family: "lucida grande", "lucida sans unicode", lucida, helvetica, "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif;''')
            # 透明化text框
            pl = pl_text.palette()
            pl.setBrush(QPalette.Base, QBrush(QColor(255, 0, 0, 0)))
            pl_text.setPalette(pl)
            pl_text.setFixedHeight(self.countPlainTextEditFixedHeight(pl_text))

            likes_label = QPushButton(qtawesome.icon('fa.thumbs-up', color='red'), str(likes))  # 点赞数
            likes_label.setStyleSheet('''text-align:right;''')

            user_label = QPushButton(qtawesome.icon('fa5s.user', color='red'), user_name + ':')  # 用户名
            user_label.setStyleSheet('''color:blue;text-align:left;''')
            time_label = QLabel(str(tim))  # time
            time_label.setStyleSheet('''color:gray;''')

            # 对comment_widget进行布局
            comment_layout.addWidget(avatar_label, 0, 0, 2, 1)  # 头像
            comment_layout.addWidget(user_label, 0, 1, 2, 3)
            comment_layout.addWidget(QLabel(''), 0, 4, 2, 8)
            comment_layout.addWidget(pl_text, 2, 0, 2, 12)

            comment_layout.addWidget(time_label, 4, 0, 1, 2)
            comment_layout.addWidget(QLabel(''), 4, 2, 1, 8)
            comment_layout.addWidget(likes_label, 4, 10, 1, 2)

            comment_widget.setMaximumWidth(700)
            self.scroll_layout.addWidget(comment_widget, i + 10, 0)

        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

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

    def set_pixmap(self, label, img, w=100, h=100):
        '''

        label_img的设置
        '''
        img = cv2.cvtColor(cv2.resize(img, (w, h)), cv2.COLOR_BGR2RGB)
        Qimg = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(Qimg))

    def countPlainTextEditFixedHeight(self, pl_text):
        '''
        pl_text装载评论区内容,该函数自适应计算出PlainTextEdit的高度，反之其出现滚动条。

        :param pl_text:
        :return: 自适应高度
        '''
        blockCount = pl_text.blockCount()  # 有多少个块。就代表有多少个空行
        plain_text = pl_text.toPlainText()
        nSumWidth = pl_text.fontMetrics().width(plain_text)  # 计算所有字体的宽度
        nUiWidth = pl_text.width()  # pl_text的宽度,不包括滚动条
        nHeight = pl_text.fontMetrics().lineSpacing()  # 字体高度
        # 所有字体宽度/每一行的宽度 为字体占据多少行
        nRowCount = int(np.ceil(nSumWidth * 1.0 / nUiWidth))
        nRowCount += blockCount
        return nHeight * nRowCount

    def draw_circle_label(self, label, img, mx_w=50, mx_h=50):
        '''
        填充img于label并绘制为圆形。

        :param label: QLabel实例
        :param img: np.array(h,w,3)
        :param mx_w: 设置label的最大w
        :param mx_h: 最大h,即设置圆的半径,一般mx_w、mx_h相等
        :return: 填充了img且绘制为圆形的label
        '''
        # label.setStyleSheet("background-color:transparent;border:0px") # 这里不用设置
        label.setMaximumWidth(mx_w)
        label.setMaximumHeight(mx_h)  # 固定label大小

        # 获取pixmap,这里需要根据实际情况调整cv2.resize,这里相当于从(100,100)的img里面裁剪圆
        img = cv2.cvtColor(cv2.resize(img, (mx_w * 2, mx_h * 2)), cv2.COLOR_BGR2RGB)
        Qimg = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
        pixmapa = QPixmap.fromImage(Qimg)
        pixmap = QPixmap(mx_w, mx_h)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.begin(self)  # 要将绘制过程用begin(self)和end()包起来
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)  # 一个是平滑，一个是缩放保持比例
        path = QPainterPath()
        path.addEllipse(0, 0, mx_w, mx_h)  # 绘制椭圆
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, mx_w, mx_h, pixmapa)
        painter.end()
        label.setPixmap(pixmap)
        return label

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
            # self._isTracking = True
            self._startPos = QtCore.QPoint(e.x(), e.y())

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.LeftButton:
            # self._isTracking = False
            self._startPos = None
            self._endPos = None
