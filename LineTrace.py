import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, qApp, QToolBar, QWidget, QMainWindow, QApplication, QGridLayout
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph


class LineTrace(BaseGraph):

    def __init__(self, x_data=None, y_data=None):
        super().__init__()

        self.setWindowTitle("Line trace window")
        self.setWindowIcon(QIcon("img/lineGraph.png"))
        self.plt = pg.PlotWidget(x=x_data, y=y_data, pen=(60, 60, 60))
        self.plt.setBackground('w')
        for axis in ['left', 'bottom']:
            pi = self.plt.getPlotItem()
            ax = pi.getAxis(axis)
            ax.setPen((60, 60, 60))
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

    def define_plot_parameters(self):
        pass


def main():
    app = QApplication(sys.argv)
    ex = LineTrace([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [23, 1, 12, 43, 5, 7, 8, 44, 63, 33])
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()