import pyqtgraph as pg
import numpy as np
import sys

from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtGui import QIcon

from scipy.optimize import curve_fit
from scipy import array
from scipy import exp
from graphs.BaseGraph import BaseGraph
from data_handlers.QcodesDataBuffer import QcodesData, DataBuffer


class LineTrace(BaseGraph):

    def __init__(self, data: DataBuffer=None, axis_data=None):
        super().__init__()

        if axis_data is None:
            self.data_buffer = data
            self.x_values = self.data_buffer.data["x"]
            self.y_values = self.data_buffer.data["y"]
        else:
            self.x_values = axis_data["x"]
            self.y_values = axis_data["y"]

        self.plt = pg.GraphicsView()

        self.central_item = pg.GraphicsLayout()

        self.main_subplot = pg.PlotItem(x=self.x_values, y=self.y_values, pen=(60, 60, 60))

        self.fit_plot = pg.PlotItem(pen=(60, 60, 60))

        self.modes = {"fit": False}

        self.init_ui()

    def init_ui(self):

        self.setGeometry(50, 50, 640, 400)
        self.setWindowTitle("Line trace window")
        self.setWindowIcon(QIcon("../img/lineGraph.png"))
        self.setCentralWidget(self.plt)

        self.plt.setBackground("w")
        self.plt.setCentralWidget(self.central_item)

        self.central_item.addItem(self.main_subplot, colspan=2)
        for plot_item in [self.main_subplot, self.fit_plot]:
            for axis in ['left', 'bottom']:
                pi = plot_item
                ax = pi.getAxis(axis)
                ax.setPen((60, 60, 60))

        self.central_item.nextRow()
        self.central_item.addItem(self.fit_plot)
        self.fit_plot.hide()

        self.show()

    def init_toolbar(self):

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)

        self.toggle_fit_mode = QAction(QIcon("img/fit_curve_icon.png"), "Fit_mode")
        self.tools.addAction(self.toggle_fit_mode)

        self.gauss = QAction(QIcon("img/gaussianIcon.png"), "Gaussian_fit")
        self.tools.addAction(self.gauss)

        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit")
        self.tools.addAction(self.exit_action_Btn)

    def define_plot_parameters(self):
        pass

    def fit_mode_action(self):

        if self.modes["fit"]:
            self.modes["fit"] = False
            self.main_subplot.removeItem(self.region_select)
            del self.region_select
            self.fit_plot.hide()
            self.fit_plot.clear()
        else:
            self.modes["fit"] = True
            self.region_select = pg.LinearRegionItem([0, 1])
            self.region_select.sigRegionChanged.connect(self.update_selected_region)
            self.region_select.setZValue(10)
            self.region_select.setRegion([self.x_values[0], self.x_values[-1]])
            self.main_subplot.addItem(self.region_select, ignoreBounds=True)
            self.fit_plot.show()
            # add only selected data to graph

    def gaussian_fit_action(self):

        x = self.x_values
        y = self.y_values
        mean = sum(x*y)/sum(y)  # https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
        sigma = np.sqrt(sum(y * (x - mean) ** 2) / sum(y))

        def gauss(x, a, x0, sigma):
            return a * exp(-(x - x0) ** 2 / (2 * sigma ** 2))

        p0 = array([max(y), mean, sigma])
        popt, pcov = curve_fit(gauss, x, y, p0=p0)
        plot_item = pg.PlotDataItem(x, gauss(x, *popt))
        plot_item.setPen(255, 0, 0)
        self.fit_plot.addItem(plot_item)
        # has to also be removed

    def update_selected_region(self):
        min_x, max_x = self.region_select.getRegion()
        self.fit_plot.setXRange(min_x, max_x)



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
