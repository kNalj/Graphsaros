import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph
from data_handlers.QcodesDataBuffer import QcodesData


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
    file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\qcodesGUI\\data\\2018-05-25\\#001_{name}_13-22-09\\inst1_g1_set.dat"
    data = QcodesData(file_location)
    ex = LineTrace(data.data["x"], data.data["y"])
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()