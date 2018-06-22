import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, qApp, QToolBar, QWidget, QMainWindow, QApplication, QGridLayout
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph


class Heatmap(BaseGraph):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Heatmap window")
        self.setWindowIcon(QIcon("img/heatmapIcon.png"))
        # need to keep track of number of opened windows and position the newly created one accordingly
        self.plt = pg.ImageView()
        self.init_ui()

    def init_ui(self):

        self.setGeometry(50, 50, 640, 400)
        self.setCentralWidget(self.plt)
        self.show()

    def init_toolbar(self):

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)
        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit")
        self.tools.addAction(self.exit_action_Btn)


def main():
    app = QApplication(sys.argv)
    ex = Heatmap()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()