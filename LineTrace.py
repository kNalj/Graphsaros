import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph
from data_handlers.QcodesDataBuffer import QcodesData, DataBuffer


class LineTrace(BaseGraph):

    def __init__(self, data: DataBuffer):
        super().__init__()

        self.data_buffer = data
        self.setWindowTitle("Line trace window")
        self.setWindowIcon(QIcon("img/lineGraph.png"))
        self.plt = pg.PlotWidget(x=self.data_buffer.data["x"], y=self.data_buffer.data["y"], pen=(60, 60, 60))
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
    file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\inst1_g1_set.dat"
    data = QcodesData(file_location)
    print(data.get_x_axis_values())
    print(data.get_y_axis_values())
    ex = LineTrace(data)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()