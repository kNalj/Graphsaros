import pyqtgraph as pg
import numpy as np
import sys

from PyQt5.QtWidgets import QAction, QApplication, QToolBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

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

        self.fit_curves = {}

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
        self.toggle_fit_mode.setCheckable(True)

        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit")
        self.tools.addAction(self.exit_action_Btn)

        self.init_fit_toolbar()

    def init_fit_toolbar(self):
        self.fit_toolbar = QToolBar("Fitting options")
        self.fit_toolbar.actionTriggered[QAction].connect(self.perform_action)

        self.default_graph = QAction(QIcon("img/noneIcon.png"), "Default_graph")
        self.default_graph.setCheckable(True)
        self.default_graph.setChecked(True)
        self.fit_toolbar.addAction(self.default_graph)

        self.gauss = QAction(QIcon("img/gaussianIcon.png"), "Gaussian_fit")
        self.gauss.setCheckable(True)
        self.fit_toolbar.addAction(self.gauss)
        self.addToolBar(Qt.RightToolBarArea, self.fit_toolbar)
        self.fit_toolbar.hide()

    def define_plot_parameters(self):
        pass

    def fit_mode_action(self):

        if self.modes["fit"]:
            self.modes["fit"] = False
            self.fit_toolbar.hide()
            self.main_subplot.removeItem(self.region_select)
            del self.region_select
            self.fit_plot.hide()
            self.fit_plot.clear()
        else:
            self.modes["fit"] = True
            self.fit_toolbar.show()
            self.region_select = pg.LinearRegionItem([0, 1])
            self.region_select.sigRegionChanged.connect(self.update_selected_region)
            self.region_select.setZValue(10)
            self.region_select.setRegion([self.x_values[0], self.x_values[-1]])
            self.main_subplot.addItem(self.region_select, ignoreBounds=True)
            self.set_initial_fit_graph_state()
            self.fit_plot.show()
            # add only selected data to graph

    def set_initial_fit_graph_state(self):

        self.fit_plot.clear()
        plot_item = pg.PlotDataItem(self.x_values, self.y_values)
        self.fit_plot.addItem(plot_item)
        self.fit_curves["default"] = plot_item

        # Set button states as they should be
        self.default_graph.setChecked(True)
        self.gauss.setChecked(False)

    def gaussian_fit_action(self):

        def gauss(x, a, x0, sigma):
            return a * exp(-(x - x0) ** 2 / (2 * sigma ** 2))

        if self.gauss.isChecked():
            x = self.x_values
            y = self.y_values
            mean = sum(x*y)/sum(y)  # https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
            sigma = np.sqrt(sum(y * (x - mean) ** 2) / sum(y))

            p0 = array([max(y), mean, sigma])
            popt, pcov = curve_fit(gauss, x, y, p0=p0)
            plot_item = pg.PlotDataItem(x, gauss(x, *popt))
            plot_item.setPen(255, 0, 0)
            self.fit_plot.addItem(plot_item)
            self.fit_curves["gauss"] = plot_item
            # has to also be removed
        else:
            self.fit_plot.removeItem(self.fit_curves["gauss"])

    def default_graph_action(self):

        if self.default_graph.isChecked():
            x = self.x_values
            y = self.y_values

            plot_item = pg.PlotDataItem(x, y)
            self.fit_plot.addItem(plot_item)
            self.fit_curves["default"] = plot_item
        else:
            self.fit_plot.removeItem(self.fit_curves["default"])

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
