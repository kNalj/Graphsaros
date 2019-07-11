from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, QPoint, QRectF, QThreadPool
from PyQt5.QtGui import QIcon, QPixmap
from PIL import ImageGrab
from ThreadWorker import Worker

import sys
import numpy as np
import pyqtgraph as pg
import cv2


class VideoPlayer(QWidget):
    """
    A class used to display a video being recorded as a result of using video exporter.

    """

    recordig_started = pyqtSignal(object)

    def __init__(self, width=200, height=200, position=None):
        """


        :param width: integer: width of the selected area
        :param height: integer: height of the selected area
        :param position: QPoint: coordinates of the top left corner of the selected area
        """
        super(QWidget, self).__init__()

        self.recording = False
        self.paused = False

        self.width = width
        self.height = height
        self.position = position

        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.out = cv2.VideoWriter("Untitled.avi", self.fourcc, 30.0, (int(self.width), int(self.height)))

        self.image_data = None

        self.thread_pool = QThreadPool()

        self.init_ui()

    def init_ui(self):
        """
        User interface for the video window.

        :return:
        """
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.7 * width), int(0.1 * height), 1.3 * self.width, 1.3 * self.height)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.image_data = self.get_image()
        corr = np.rot90(np.flip(self.image_data, 1))
        gv = pg.GraphicsView()
        gv.setBackground("w")
        self.image_item = pg.ImageItem(border="k")
        self.image_item.setImage(corr)
        gv.addItem(self.image_item)
        gv.setRange(QRectF(0, 0, self.width, self.height))
        main_layout.addWidget(gv)

        btns_layout = QHBoxLayout()

        self.play_btn = QPushButton()
        self.play_btn.setCheckable(True)
        play_btn_icon = QIcon()
        play_btn_icon.addPixmap(QPixmap("img/play_icon.png"))
        play_btn_icon.addPixmap(QPixmap("img/pause_icon.png"), QIcon.Normal, QIcon.On)
        self.play_btn.setIcon(play_btn_icon)
        self.play_btn.clicked.connect(self.toggle_play)

        self.stop_btn = QPushButton()
        record_btn_icon = QIcon()
        record_btn_icon.addPixmap(QPixmap("img/stop_icon.png"))
        self.stop_btn.setIcon(record_btn_icon)
        self.stop_btn.clicked.connect(self.stop_recording)

        btns_layout.addWidget(self.play_btn)
        btns_layout.addWidget(self.stop_btn)

        main_layout.addLayout(btns_layout)

        self.show()

    def get_image(self):
        """
        Get the selected area as np array of [R, G, B] arrays.

        :return:
        """
        img = ImageGrab.grab(bbox=(int(self.position.x()), int(self.position.y()),
                                   int(self.position.x() + self.width),
                                   int(self.position.y() + self.height)))
        img_np = np.array(img)
        return img_np

    def get_frame(self, img=None):
        """
        Since RGB is not the default color scheme in PIL library, the data needs to be transformed to it.

        :param img:
        :return:
        """
        if img is None:
            img = self.get_image()
        frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return frame

    def update_image(self, img=None):
        """
        Gets the selected area, then flips and rotates it so it can be displayed as an image.


        :return:
        """
        if img is None:
            self.image_data = self.get_image()
        else:
            self.image_data = img
        corr = np.rot90(np.flip(self.image_data, 1))
        self.image_item.setImage(corr)

    def toggle_play(self):
        """
        A method that allows pausing. If the recording is started you can pause it, and resume it.

        :return: NoneType
        """
        if self.play_btn.isChecked():
            if self.recording is False:
                self.recording = True
                self.start_recording_loop()
            self.paused = False
        else:
            self.paused = True

    def start_recording_loop(self):
        """
        Gets called when the play button is pressed for the first time. It starts a thread that constantly gets the
        selected area and saves it to a file.

        :return:
        """
        def loop():
            while True:
                if not self.paused:
                    img_np = self.get_image()
                    frame = self.get_frame(img_np)
                    self.update_image(img_np)

                    self.out.write(frame)

                if not self.recording:
                    self.stop_recording()
                    break

        worker = Worker(loop)
        worker.signals.finished.connect(self.stop_recording)
        self.thread_pool.start(worker)

    def stop_recording(self):
        """
        Stop recording, release the opened file where the video is being saved to and close all cv2 windows.

        :return:
        """
        if self.recording:
            self.recording = False
            self.paused = False
            self.play_btn.toggle()
            self.stop_recording()
            self.out.release()
            cv2.destroyAllWindows()


def main():
    print("GO")
    app = QApplication(sys.argv)
    ex = VideoPlayer(400, 300, QPoint(20, 20))
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
