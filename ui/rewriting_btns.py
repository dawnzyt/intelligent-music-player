import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from cloudmusic.musicObj import Music


# 简单来说通过一个QTimer来判断是否是双击。
# 用户点击一次开始计时,如果两次点击时间小于我们规定的时间,就认为是双击
class QDoublePushButton(QPushButton):
    doubleClicked = pyqtSignal()
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clicked.emit)
        info = {'name': '', 'artist': [], 'album': '', 'artistId': [], 'albumId': '', 'picUrl': ''}
        self.music = Music('', '', '', 0, '', info)
        self.music_path = ''
        self.music_name = ''
        self.artist = ''
        super().clicked.connect(self.checkDoubleClick)

    @pyqtSlot()
    def checkDoubleClick(self):
        if self.timer.isActive():
            self.doubleClicked.emit()
            self.timer.stop()
        else:
            self.timer.start(250)


class QMusicPushButton(QPushButton):
    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        info = {'name': '', 'artist': [], 'album': '', 'artistId': [], 'albumId': '', 'picUrl': ''}
        self.music = Music('', '', '', 0, '', info)


class Window(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.button = QDoublePushButton("Test", self)
        self.button.clicked.connect(self.on_click)
        self.button.doubleClicked.connect(self.on_doubleclick)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.button)

        self.setLayout(self.layout)
        self.resize(120, 50)
        self.show()

    @pyqtSlot()
    def on_click(self):
        print("Click")

    @pyqtSlot()
    def on_doubleclick(self):
        print("Doubleclick")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    sys.exit(app.exec_())
