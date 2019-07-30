from PyQt5.QtWidgets import QWidget, QGridLayout, QProgressBar
from PyQt5.QtCore import pyqtSignal


class ProgressBarWidget(QWidget):

    finished = pyqtSignal(object)

    def __init__(self, title):
        super().__init__()

        self.title = title

        self.init_ui()
        self.show()

    def init_ui(self):

        self.setWindowTitle("Loading {}".format(self.title))
        self.setGeometry(200, 200, 200, 50)
        self.grid_layout = QGridLayout()
        self.progressBar = QProgressBar()
        self.grid_layout.addWidget(self.progressBar)
        self.setLayout(self.grid_layout)

    def setValue(self, val):  # Sets value
        self.progressBar.setProperty("value", val)
        if val == 100:
            self.finished.emit(self)
