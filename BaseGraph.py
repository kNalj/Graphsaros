import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, QMainWindow, QApplication
from PyQt5.QtGui import QIcon


class BaseGraph(QMainWindow):

    def __init__(self):
        super().__init__()

        # plot object, can be 2D or 3D
        self.plt = None
        self.init_toolbar()

    def init_ui(self):
        # implemented in child classes
        raise NotImplementedError

    def init_toolbar(self):
        # implemented in child classes
        raise NotImplementedError

    def perform_action(self, action):

        method_name = action.text().lower()
        method_name = method_name + "_action"
        action_method = getattr(self, method_name)
        action_method()

    def exit_action(self):
        self.close()
