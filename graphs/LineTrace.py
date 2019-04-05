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
    def __init__(self, data: DataBuffer = None, axis_data=None, parent=None):
        """
        Inherits: BaseGraph()

        Used to display 2D type of graphs. Enables user to to transformations to 2D type of data (x, y)

        :param data: DataBuffer(): If DataBuffer is being opened, this is a reference to that data buffer
        :param axis_data [Optional]: If what is being open is a line trace created from Heatmap window, then there is
                                    no actual data buffer rather just x and y axis data
        """
        print("Instantiating 2d window . . .")
        super().__init__(parent=parent)

        # Axis data exists when what is being opened is a line trace created by Heatmap window. In that case no
        # reference to data buffer is made.
        if axis_data is None:
            self.data_buffer = data
            self.x_values = self.data_buffer.data["x"]
            self.y_values = self.data_buffer.data["y"]
        else:
            self.x_values = axis_data["x"]
            self.y_values = axis_data["y"]

        # Elements for ploting data
        self.plt = pg.GraphicsView()
        self.central_item = pg.GraphicsLayout()
        self.main_subplot = pg.PlotItem(x=self.x_values, y=self.y_values, pen=(60, 60, 60))
        self.fit_plot = pg.PlotItem(pen=(60, 60, 60))

        # indicates in which modes the window is currently working.
        self.modes = {"fit": False}

        # used in fit mode of this window, holds data about created fit curves to enable hiding and displaying them at
        # any point
        self.fit_curves = {}

        self.init_ui()

    def init_ui(self):

        print("Creating 2d window . . .")
        # set dimensions, title and icon of the window
        self.setGeometry(50, 50, 640, 400)
        self.setWindowTitle("Line trace window")
        self.setWindowIcon(QIcon("../img/lineGraph.png"))
        self.setCentralWidget(self.plt)

        self.plt.setBackground("w")
        self.plt.setCentralWidget(self.central_item)

        print("Creating axis elements . . .")
        self.central_item.addItem(self.main_subplot, colspan=2)
        for plot_item in [self.main_subplot, self.fit_plot]:
            for axis in ['left', 'bottom']:
                pi = plot_item
                ax = pi.getAxis(axis)
                ax.setPen((60, 60, 60))

        self.central_item.nextRow()
        self.central_item.addItem(self.fit_plot)
        self.fit_plot.hide()

        self.init_toolbar()

        self.show()

    def init_toolbar(self):
        """
        Create toolbar of the line trace window

        :return: NoneType
        """
        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)

        self.toggle_fit_mode = QAction(QIcon("img/fit_curve_icon.png"), "Fit_mode", self)
        self.tools.addAction(self.toggle_fit_mode)
        self.toggle_fit_mode.setCheckable(True)

        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit", self)
        self.tools.addAction(self.exit_action_Btn)

        self.init_fit_toolbar()

    def init_fit_toolbar(self):
        """
        Additional toolbar that is displayed when window is operating in "fit" mode

        :return: NoneType
        """
        self.fit_toolbar = QToolBar("Fitting options")
        self.fit_toolbar.actionTriggered[QAction].connect(self.perform_action)

        self.default_graph = QAction(QIcon("img/noneIcon.png"), "Default_graph", self)
        self.default_graph.setCheckable(True)
        self.default_graph.setChecked(True)
        self.fit_toolbar.addAction(self.default_graph)

        self.gauss = QAction(QIcon("img/gaussianIcon.png"), "Gaussian_fit", self)
        self.gauss.setCheckable(True)
        self.fit_toolbar.addAction(self.gauss)
        self.addToolBar(Qt.RightToolBarArea, self.fit_toolbar)
        self.fit_toolbar.hide()

    def define_plot_parameters(self):
        pass

    def fit_mode_action(self):
        """
        TODO: This might have a memory leak, i keep creating new LinerRegionItems. Probably should reuse the old one

        Called when user clicks on an action that activates fit mode of the window. Shows / hides additional toolbar
        used to fit different kinds of curves to the displayed data.

        :return: NoneType
        """

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
        """
        Default state of the fit mode displays only mirrored source of the data. Other fits need to be manually turned
        on for them to be displayed.

        :return: NoneType
        """

        self.fit_plot.clear()
        plot_item = pg.PlotDataItem(self.x_values, self.y_values)
        self.fit_plot.addItem(plot_item)
        self.fit_curves["default"] = plot_item

        # Set button states as they should be
        self.default_graph.setChecked(True)
        self.gauss.setChecked(False)

    def gaussian_fit_action(self):
        """
        As suggested by the name of the function, it tries to apply gaussian fit the the selected data. Data is then
        added and displayed in the graph for fir curves.

        Turning of this function removes curve from the graph

        :return:
        """
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
        """
        Mirror the source data of the window to the graph for fits. Turning off this action removes the curve from graph
        for displaying fit curves.

        :return: NoneType
        """
        if self.default_graph.isChecked():
            x = self.x_values
            y = self.y_values

            plot_item = pg.PlotDataItem(x, y)
            self.fit_plot.addItem(plot_item)
            self.fit_curves["default"] = plot_item
        else:
            self.fit_plot.removeItem(self.fit_curves["default"])

    def update_selected_region(self):
        """
        Event that upon changing bounds of regen select element changes limits of the fit graph in a way that it only
        displays the selected portion of the data.

        :return: NoneType
        """
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
