import pyqtgraph as pg
import numpy as np
import sys
import helpers

from PyQt5.QtWidgets import QAction, QApplication, QToolBar, QComboBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from scipy.optimize import curve_fit
from scipy import array
from scipy import exp
from graphs.BaseGraph import BaseGraph
from data_handlers.QcodesDataBuffer import QcodesData
from data_handlers.DataBuffer import DataBuffer
from data_handlers.Dummy2D import DummyBuffer
from helpers import show_error_message


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class LineTrace(BaseGraph):

    def __init__(self, data: DataBuffer = None, axis_data=None, parent=None, labels=None):
        """
        TODO: Fix documentation, i might have changed things and forgot to update documentation (axis_data)
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

        self.data_buffer = data
        self.x_values = self.data_buffer.data["x"]
        self.y_values = self.data_buffer.data["y"]

        self.active_data_set = self.y_values[0]
        self.displayed_data_set = self.active_data_set

        self.labels = labels
        self.title = self.data_buffer.name

        # indicates in which modes the window is currently working.
        self.modes = {"fit": False}
        # used in fit mode of this window, holds data about created fit curves to enable hiding and displaying them at
        # any point
        self.fit_curves = {}
        for index, data in enumerate(self.y_values):
            self.fit_curves[index] = {}

        self.init_ui()

    """
    # ###########################################
    # ############ USER INTERFACE ###############
    # ###########################################
    """
    def init_ui(self):
        """
        Method that builds user interface

        :return:
        """

        print("Creating 2d window . . .")
        # set dimensions, title and icon of the window
        self.setGeometry(50, 50, 640, 400)
        self.setWindowTitle("Line trace window")
        self.setWindowIcon(QIcon("../img/lineGraph.png"))

        # Elements for ploting data
        self.plt = pg.GraphicsView()
        self.central_item = pg.GraphicsLayout()
        self.main_subplot = pg.PlotItem(x=self.x_values, y=self.y_values[0], pen=(60, 60, 60), title=self.title)
        self.fit_plot = pg.PlotItem(pen=(60, 60, 60))
        self.fit_plot.sigRangeChanged.connect(self.update_region_area)

        self.setCentralWidget(self.plt)

        # set the color of the background and set the central widget. All other elements are added to this central
        # widget, which makes them resizable and scalable with the window size.
        self.plt.setBackground("w")
        self.plt.setCentralWidget(self.central_item)

        print("Creating axis elements . . .")
        legend = {"left": "y", "bottom": "x", "top": "extra_axis"}
        self.central_item.addItem(self.main_subplot, colspan=2)

        self.central_item.nextRow()
        self.central_item.addItem(self.fit_plot)
        self.fit_plot.hide()

        # connect the range changed signal of main subplot to a method that updates the range of the extra axis.
        self.main_subplot.sigRangeChanged.connect(self.update_extra_axis)

        print("Configuring axis data . . .")
        self.update_axis_labels()

        self.plot_elements = {"main_subplot": self.main_subplot, "fit_plot": self.fit_plot}

        self.init_toolbar()

        self.show()

    def init_toolbar(self):
        """
        Create toolbar of the line trace window

        :return: NoneType
        """
        print("Creating toolbar . . .")
        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)

        print("Filling selection combobox . . .")
        self.data_selection_combobox = QComboBox()
        for index, data in enumerate(self.data_buffer.data["y"]):
            display_member = "param{}".format(index)
            value_member = data
            self.data_selection_combobox.addItem(display_member, value_member)
        self.data_selection_combobox.currentIndexChanged.connect(lambda: self.change_active_set(
            index=self.data_selection_combobox.currentIndex()))
        self.tools.addWidget(self.data_selection_combobox)

        print("Adding actions . . .")
        self.toggle_fit_mode = QAction(QIcon("img/fit_curve_icon.png"), "Fit_mode", self)
        self.tools.addAction(self.toggle_fit_mode)
        self.toggle_fit_mode.setCheckable(True)

        self.window_toolbar = QToolBar("Window toolbar")
        self.window_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(self.window_toolbar)

        self.customize_font_btn = QAction(QIcon("img/editFontIcon.png"), "Font", self)
        self.customize_font_btn.setToolTip("Open a widget that allows user to customise font and axis values")
        self.window_toolbar.addAction(self.customize_font_btn)

        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit", self)
        self.window_toolbar.addAction(self.exit_action_Btn)

        self.init_fit_toolbar()

    def init_fit_toolbar(self):
        """
        Additional toolbar that is displayed when window is operating in "fit" mode

        :return: NoneType
        """
        print("Initialising fit toolbar . . .")
        self.fit_toolbar = QToolBar("Fitting options")
        self.fit_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(Qt.RightToolBarArea, self.fit_toolbar)
        self.fit_toolbar.hide()

        self.default_graph = QAction(QIcon("img/noneIcon.png"), "Default_graph", self)
        self.default_graph.setCheckable(True)
        self.default_graph.setChecked(True)
        self.fit_toolbar.addAction(self.default_graph)

        self.linear = QAction(QIcon("img/linear_fit_icon.png"), "Linear_fit", self)
        self.linear.setCheckable(True)
        self.fit_toolbar.addAction(self.linear)

        self.gauss = QAction(QIcon("img/gaussianIcon.png"), "Gaussian_fit", self)
        self.gauss.setCheckable(True)
        self.fit_toolbar.addAction(self.gauss)

        self.sinus = QAction(QIcon("img/sinusIcon.png"), "Sinus_fit", self)
        self.sinus.setCheckable(True)
        self.fit_toolbar.addAction(self.sinus)

    def define_plot_parameters(self):
        pass

    """
    # ###########################################
    # ################# HELPERS #################
    # ###########################################
    """
    def get_selection_area(self):
        """
        This method gets data points on x axis that are inside of the area selected by LinearRegionItem
        (self.region_select). It then also selects coresponding data points on y axis and returns two numpy arrays
        containing x and y data points.

        :return: np.array, np.array: data points on x and y axis that are inside the selected area
        """
        min_x, max_x = self.region_select.getRegion()
        x = []
        y = []
        for i, value in enumerate(self.x_values):
            if value >= min_x and value <= max_x:
                x.append(value)
                y.append(self.active_data_set[i])
        x = np.array(x)
        y = np.array(y)
        return x, y

    def change_active_set(self, index):
        """
        TODO: Write documentation

        :param index:
        :return:
        """
        data = self.y_values[index]
        self.active_data_set = data
        self.change_displayed_data_set(data, index)

    def change_displayed_data_set(self, data_set, index):
        """
        TODO: Write documentation

        :param data_set:
        :param index:
        :return:
        """
        self.displayed_data_set = data_set
        self.plot_elements["main_subplot"].clear()
        self.plot_elements["main_subplot"].plot(self.x_values, self.active_data_set, pen=(60, 60, 60))
        self.plot_elements["fit_plot"].clear()
        self.plot_elements["fit_plot"].plot(self.x_values, self.active_data_set)

        self.update_axis_labels(index)

        if self.modes["fit"]:
            self.modes["fit"] = False
            self.fit_mode_action()

    """
    # ###########################################
    # ############### ACTIONS ###################
    # ###########################################
    """
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
        plot_item = pg.PlotDataItem(self.x_values, self.active_data_set)
        self.fit_plot.addItem(plot_item)
        self.fit_curves["default"] = plot_item

        # Set button states as they should be
        self.default_graph.setChecked(True)
        self.gauss.setChecked(False)

    def font_action(self):
        """
        Opens a new widget that allows user to modify font sizes on axis of all graphs in this window

        :return: NoneType
        """

        self.eaw = helpers.Edit2DAxisWidget(self)
        self.eaw.submitted.connect(self.edit_axis_data)
        self.eaw.show()

    # ###############################
    # ############ FITS #############
    # ###############################
    def default_graph_action(self):
        """
        Mirror the source data of the window to the graph for fits. Turning off this action removes the curve from graph
        for displaying fit curves.

        :return: NoneType
        """
        if self.default_graph.isChecked():
            x = self.x_values
            y = self.active_data_set

            plot_item = pg.PlotDataItem(x, y)
            self.fit_plot.addItem(plot_item)
            self.fit_curves["default"] = plot_item
        else:
            self.fit_plot.removeItem(self.fit_curves["default"])

    def gaussian_fit_action(self):
        """
        As suggested by the name of the function, it tries to apply gaussian fit the the selected data. Data is then
        added and displayed in the graph for fir curves.

        Turning off the action that prompts this function removes curve from the graph

        :return:
        """
        def gauss(x, a, x0, sigma):
            """

            :param x:
            :param a:
            :param x0:
            :param sigma:
            :return:
            """
            return a * exp(-(x - x0) ** 2 / (2 * sigma ** 2))

        if self.gauss.isChecked():
            try:
                x, y = self.get_selection_area()
                mean = sum(x*y)/sum(y)  # https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
                sigma = np.sqrt(sum(y * (x - mean) ** 2) / sum(y))

                p0 = array([max(y), mean, sigma])
                popt, pcov = curve_fit(gauss, x, y, p0=p0)
                plot_item = pg.PlotDataItem(x, gauss(x, *popt))
                plot_item.setPen(255, 0, 0)
                self.fit_plot.addItem(plot_item)
                self.fit_curves["gauss"] = plot_item
            except Exception as e:
                print(str(e))
                show_error_message("Could not find fit", str(e))
        else:
            self.fit_plot.removeItem(self.fit_curves["gauss"])
            del self.fit_curves["gauss"]

    def sinus_fit_action(self):
        """
        As suggested by the name of the function, it tries to apply sinus fit the the selected data. Data is then
        added and displayed in the graph for fir curves.

        Turning off the action that prompts this function removes curve from the graph

        :return:
        """
        def sin(x, freq, amplitude, phase, offset):
            """

            :param x:
            :param freq:
            :param amplitude:
            :param phase:
            :param offset:
            :return:
            """
            return np.sin(x * freq + phase) * amplitude + offset

        if self.sinus.isChecked():
            x, y = self.get_selection_area()
            guess_freq = 1
            guess_amplitude = 3 * np.std(y)/(2**0.5)
            guess_phase = 0
            guess_offset = np.mean(y)
            p0 = array([guess_freq, guess_amplitude, guess_phase, guess_offset])
            fit = curve_fit(sin, x, y, p0=p0)
            fit_data = sin(x, *fit[0])
            plot_item = pg.PlotDataItem(x, fit_data)
            plot_item.setPen(0, 0, 255)
            self.fit_plot.addItem(plot_item)
            self.fit_curves["sinus"] = plot_item
        else:
            self.fit_plot.removeItem(self.fit_curves["sinus"])
            del self.fit_curves["sinus"]

    def linear_fit_action(self):
        """

        :return:
        """

        def linear(a, b, k):
            """

            :param a:
            :param b:
            :param k:
            :return:
            """
            return a*k + b

        if self.linear.isChecked():
            x, y = self.get_selection_area()
            initial_guess = np.polyfit(x, y, 1)
            fit = curve_fit(linear, x, y, initial_guess)
            fit_data = linear(x, *fit[0])
            plot_item = pg.PlotDataItem(x, fit_data)
            plot_item.setPen(0, 255, 0)
            self.fit_plot.addItem(plot_item)
            self.fit_curves["linear"] = plot_item
        else:
            self.fit_plot.removeItem(self.fit_curves["linear"])
            del self.fit_curves["linear"]

    """
    # ###########################################
    # ################# Helpers #################
    # ###########################################
    """
    def update_axis_labels(self, y_index=0):
        legend = {"left": "y", "bottom": "x", "top": "extra_axis"}
        for plot_item in [self.main_subplot, self.fit_plot]:
            for axis in ['left', 'bottom']:
                pi = plot_item
                ax = pi.getAxis(axis)
                ax.setPen((60, 60, 60))
                if self.labels is not None:
                    axis_data = self.labels[legend[axis]]
                    label_style = {'font-size': '10pt'}
                    ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)
                else:
                    axis_data = self.data_buffer.axis_values[legend[axis]]
                    label_style = {'font-size': '10pt'}
                    if axis == "left":
                        ax.setLabel(axis_data[y_index]["name"], axis_data[y_index]["unit"], **label_style)
                    else:
                        ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

            plot_item.layout.removeItem(plot_item.getAxis("top"))
            if "extra_axis" in self.data_buffer.data:
                extra_view_box = pg.ViewBox()
                extra_axis = pg.AxisItem("top")
                extra_axis.setPen((60, 60, 60))
                axis_data = self.data_buffer.axis_values[legend["top"]]
                label_style = {'font-size': '9pt'}
                extra_axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)
                plot_item.layout.addItem(extra_axis, 0, 1)
                extra_axis.linkToView(extra_view_box)
                extra_view_box.setXLink(plot_item.vb)

    """
    # ###########################################
    # ################## EVENTS #################
    # ###########################################
    """
    def update_selected_region(self):
        """
        Event that upon changing bounds of region select element changes limits of the fit graph in a way that it only
        displays the selected portion of the data.

        :return: NoneType
        """
        min_x, max_x = self.region_select.getRegion()
        self.fit_plot.setXRange(min_x, max_x, padding=0)
        return

    def update_region_area(self, element, view_range):
        """
        Method that updates region select when fit graph axis changes range.

        :param element: pyqtgraph element that sent the signal
        :param view_range: range on x and y axis
        :return: NoneType
        """
        min_x, max_x = view_range[0]
        self.region_select.setRegion([min_x, max_x])
        return

    def edit_axis_data(self, data):
        """
        Method that applies the changes to axis (font, labels, ...)

        :param data: data passed trough the signal. It contains user input (values to apply to font/label/...)
        :return: NoneType
        """
        for element, sides in data.items():
            for side, options in sides.items():
                if side != "top":
                    axis = self.plot_elements[element].getAxis(side)
                    axis.setLabel(options["name"], options["unit"], **options["label_style"])
                    if options["ticks"]["font"] != "":
                        font = QFont()
                        font.setPixelSize(int(options["ticks"]["font"]))
                        axis.tickFont = font
                        axis.setStyle(tickTextOffset=int(int(options["ticks"]["font"]) / 2))
        return

    def update_extra_axis(self):
        pass


def main():
    app = QApplication(sys.argv)
    file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\inst1_g1_set.dat"
    data = QcodesData(file_location)
    data.prepare_data()

    N = 1000
    x_values_sin_test = t = np.linspace(0, 4*np.pi, N)
    y_values_sin_test = 3.0*np.sin(t+0.001) + 0.5 + np.random.randn(N) # create artificial data with noise

    dummy = DummyBuffer("test name",
                        {"values": x_values_sin_test, "axis": {"name": "test label", "unit": "test unit"}},
                        {"values": y_values_sin_test, "axis": {"name": "y test label", "unit": "y test unit"}})

    ex = LineTrace(dummy)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
