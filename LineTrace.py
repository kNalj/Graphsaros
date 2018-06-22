import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, qApp, QToolBar, QWidget, QMainWindow, QApplication, QGridLayout
from PyQt5.QtGui import QIcon


class LineTrace(QMainWindow):

    def __init__(self, x_data=None, y_data=None):
        super().__init__()

        self.setWindowTitle("Line trace window")
        self.setWindowIcon(QIcon("img/lineGraph.png"))
        self.plt = pg.PlotWidget()
        self.init_ui()
        self.init_toolbar()

    def init_ui(self):

        # add toolbar to the window

        self.setCentralWidget(self.plt)

        self.show()

    def init_toolbar(self):

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)

        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit")
        self.tools.addAction(self.exit_action_Btn)

    def perform_action(self, action):

        method_name = action.text().lower()
        method_name = method_name + "_action"

        action_method = getattr(self, method_name)
        action_method()

    def exit_action(self):
        self.close()


def main():
    app = QApplication(sys.argv)
    ex = LineTrace()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()