import pyqtgraph as pg
import numpy as np
import sys

from PyQt5.QtWidgets import QAction, QApplication, QPushButton, QGraphicsProxyWidget, QToolBar
from PyQt5.QtGui import QIcon

import helpers
from graphs.BaseGraph import BaseGraph
from graphs.LineTrace import LineTrace
from data_handlers.DataBuffer import DataBuffer
from data_handlers.QtLabDataBuffer import QtLabData
from LineROI import LineROI


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class Heatmap(BaseGraph):

    def __init__(self, data: DataBuffer):
        super().__init__()

        # setting the window title, i would have never guessed its this
        self.setWindowTitle("Heatmap window")

        # khm khm ... setting window icon ...
        self.setWindowIcon(QIcon("img/heatmapIcon.png"))

        # set status bar msg to nothing, just to have it there, later its used to show coordinates of mouse
        self.statusBar().showMessage("")

        # need to keep track of number of opened windows and position the newly created one accordingly
        self.plt = pg.GraphicsView()

        # instance of DataBuffer class, holds all data required to draw a graph
        self.data_buffer = data

        # np.array, this is what pyqtgraph wants to draw stuff
        self.plt_data = self.data_buffer.get_matrix()

        # to be able to switch between gauss, lorentz, normal, ...
        self.active_data = self.plt_data

        # gauss data
        self.plt_data_gauss = pg.gaussianFilter(self.plt_data, (2, 2))

        # indicates currently displayed data
        self.display = "normal"

        # references to all widgets in this window
        self.plot_elements = {}

        # reference to ROI
        self.line_segment_roi = {}

        # dictionary to keep track of options that have been turned on/off
        self.modes = {"ROI": False}

        self.init_ui()

    def init_ui(self):

        self.setGeometry(50, 50, 640, 400)
        self.setCentralWidget(self.plt)
        self.show()
        # proxy = QGraphicsProxyWidget()
        # line_trace_button = QPushButton("Line trace")
        # proxy.setWidget(line_trace_button)

        central_item = pg.GraphicsLayout()
        main_subplot = central_item.addPlot()
        img = pg.ImageItem()
        img.setImage(self.plt_data)
        img.translate(self.data_buffer.get_x_axis_values()[0], self.data_buffer.get_y_axis_values()[0])
        (x_scale, y_scale) = self.data_buffer.get_scale()
        img.scale(x_scale, y_scale)
        main_subplot.addItem(img)
        legend = {"left": "y", "bottom": "x"}
        for side in ('left', 'bottom'):
            ax = main_subplot.getAxis(side)
            ax.setPen((60, 60, 60))
            axis_data = self.data_buffer.axis_values[legend[side]]
            label_style = {'font-size': '10pt'}
            ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)
            # ax.setTickSpacing(major=500, minor=250)

        iso = pg.IsocurveItem(level=0.8, pen='g')
        iso.setParentItem(img)
        iso.setData(pg.gaussianFilter(self.plt_data, (2, 2)))

        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.gradient.loadPreset("thermal")
        histogram.setFixedWidth(128)
        axis_data = self.data_buffer.axis_values["z"]
        label_style = {'font-size': '8pt'}
        histogram.axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        histogram.vb.addItem(isoLine)
        histogram.vb.setMouseEnabled(y=False)  # makes user interaction a little easier
        isoLine.setValue(self.plt_data.mean())
        isoLine.setZValue(1000)  # bring iso line above contrast controls
        isoLine.sigDragged.connect(self.update_iso_curve)

        central_item.addItem(histogram)
        self.plt.setCentralItem(central_item)
        self.plt.setBackground('w')
        central_item.nextRow()
        line_trace_graph = central_item.addPlot(colspan=2, pen=(60, 60, 60))
        line_trace_graph.setMaximumHeight(256)
        legend = {"left": "z", "bottom": "x"}
        for axis in ["left", "bottom"]:
            ax = line_trace_graph.getAxis(axis)
            ax.setPen((60, 60, 60))
            axis_data = self.data_buffer.axis_values[legend[axis]]
            label_style = {'font-size': '9pt'}
            ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)
        self.plot_elements = {"central_item": central_item, "main_subplot": main_subplot,
                              "img": img, "histogram": histogram, "line_trace_graph": line_trace_graph,
                              "iso": iso, "isoLine": isoLine}

        main_subplot.scene().sigMouseMoved.connect(self.mouse_moved)

        # histogram.hide()
        """gl = pg.GradientLegend((15, 200), (-5, -20))
        gl.gradient.setColorAt(0, QColor(0, 0, 0))
        gl.gradient.setColorAt(1, QColor(255, 255, 255))
        gl.gradient.setColorAt(0.33, QColor(255, 0, 0))
        gl.gradient.setColorAt(0.66, QColor(255, 255, 0))
        low_value = self.data_buffer.get_matrix().min()
        high_value = self.data_buffer.get_matrix().max()
        first_third = low_value + ((high_value - low_value) * 0.33)
        second_third = low_value + ((high_value - low_value) * 0.66)
        gl.setLabels({str(round(low_value, 3)): 0, str(round(first_third, 3)): 0.33,
                      str(round(second_third, 3)): 0.66, str(round(high_value, 3)): 1})
        gl.setParentItem(central_item)"""

    def init_toolbar(self):
        """
        Create toolbar and add actions to it

        :return: NoneType
        """

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)
        self.line_trace_btn = QAction(QIcon("img/lineGraph"), "Line_Trace", self)
        self.tools.addAction(self.line_trace_btn)
        self.gaussian_filter_btn = QAction(QIcon("img/gaussianIcon.png"), "Gaussian_filter", self)
        self.tools.addAction(self.gaussian_filter_btn)
        self.der_x = QAction(QIcon(), "xDerivative")
        self.tools.addAction(self.der_x)
        self.der_y = QAction(QIcon(), "yDerivative")
        self.tools.addAction(self.der_y)

        self.matrix_manipulation_toolbar = QToolBar("Matrix manipulation")
        self.matrix_manipulation_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.create_matrix_file_btn = QAction(QIcon("img/matrix-512.png"), "Matrix", self)
        self.matrix_manipulation_toolbar.addAction(self.create_matrix_file_btn)
        self.data_correction_action = QAction(QIcon("img/line-chart.png"), "Correct_data", self)
        self.matrix_manipulation_toolbar.addAction(self.data_correction_action)

        self.addToolBar(self.matrix_manipulation_toolbar)

        self.window_toolbar = QToolBar("Window toolbar")
        self.window_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(self.window_toolbar)
        self.customize_font_btn = QAction(QIcon("img/editFontIcon.png"), "Font", self)
        self.customize_font_btn.setToolTip("Open a widget that allows user to customise font and axis values")
        self.window_toolbar.addAction(self.customize_font_btn)
        self.open_2D = QAction(QIcon("img/2d_icon.png"), "Show_2d", self)
        self.open_2D.setToolTip("Open a selected line trace in new window that allows manipulation and transformations")
        self.window_toolbar.addAction(self.open_2D)
        self.exit_action_btn = QAction(QIcon("img/closeIcon.png"), "Exit", self)
        self.exit_action_btn.setToolTip("Close this heatmap window")
        self.window_toolbar.addAction(self.exit_action_btn)

    def line_trace_action(self):
        """
        Add a line segment region of interest (ROI) to the main subplot. Connect it to a function that updates line
        trace graph anytime one of the handles or the ROI itself is moved.

        :return:
        """
        if self.modes["ROI"] == False:
            self.modes["ROI"] = True

            # ROI instantiation
            line_segmet_roi = LineROI(positions=([self.data_buffer.get_x_axis_values()[0],
                                                  self.data_buffer.get_y_axis_values()[0]],
                                                 [self.data_buffer.get_x_axis_values()[-1],
                                                  self.data_buffer.get_y_axis_values()[0]]),
                                      pos=(0, 0),
                                      pen=(5, 9),
                                      edges=[self.data_buffer.get_x_axis_values()[0],
                                             self.data_buffer.get_x_axis_values()[-1],
                                             self.data_buffer.get_y_axis_values()[0],
                                             self.data_buffer.get_y_axis_values()[-1]])
            # connect signal to a slot
            line_segmet_roi.sigRegionChanged.connect(self.update_line_trace_plot)
            # make a reference to this ROI so i can use it later
            self.line_segment_roi["ROI"] = line_segmet_roi
            # add the ROI to main subplot
            self.plot_elements["main_subplot"].addItem(line_segmet_roi)
            # connect signal to a slot, this signa
            line_segmet_roi.aligned.connect(self.update_line_trace_plot)
        else:
            self.plot_elements["line_trace_graph"].clear()

    def font_action(self):
        """
        Opens a new widget that allows user to modify font sizes on axis of all graphs in this window

        :return: NoneType
        """
        self.eaw = helpers.Edit3DAxisWidget(self)
        self.eaw.show()

    def update_line_trace_plot(self):
        """
        Each time a line trace is moved this method is called to update the line trace graph element of the Heatmap
        widget.

        :return: NoneType
        """

        data = self.active_data
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        line_trace_graph = self.plot_elements["line_trace_graph"]
        new_plot = line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True)
        point = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = point
        coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        new_plot.translate(coords.x(), 0)
        # scale_x, scale_y = self.data_buffer.get_scale()
        # new_plot.scale(scale_x, 1)

        point1 = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = point1
        start_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        point2 = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
        _, scene_coords = point2
        end_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)

        # had the scale figured out wrong, this is the correct way of doing it
        scale = end_coords.x() - start_coords.x()
        num_of_points = (len(selected) - 1) or 1
        new_plot.scale(scale/num_of_points, 1)
        print(scale)

        print(start_coords.x(), end_coords.x())

        # real_scale =

    def gaussian_filter_action(self):
        """
        Following the naming convention set in the base class of the graph widgets this method is called after an action
        in the toolbar called "gaussian_filter" and it gets called when that action is triggered. Method applies
        gaussian filter to your dataset and displays it.

        If the gaussian filter data is the active data, then upon calling this method the dataset is set back to the
        default dataset. (Works like ON / OFF switch)

        :return: NoneType
        """
        if self.display != "gauss":
            self.plot_elements["img"].setImage(self.plt_data_gauss)
            self.active_data = self.plt_data_gauss
            self.display = "gauss"
        else:
            self.plot_elements["img"].setImage(self.plt_data)
            self.display = "normal"
            self.active_data = self.plt_data

    def lorentzian_filter_action(self):
        """
        I dont think i will actually need this but whatever

        :return:
        """
        pass

    def matrix_action(self):
        """
        Creates the matrix file version of this data in the same folder where the original file is located

        :return: NoneType
        """
        self.data_buffer.create_matrix_file()

    def show_2d_action(self):
        """
        Opens a line trace graph window for a line trace selected by line_trace_roi

        :return:
        """
        data = self.active_data
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        first_point = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = first_point
        start = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        start_x = start.x()
        last_point = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
        _, scene_coords = last_point
        end = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        end_x = end.x()

        x = np.linspace(start_x, end_x, len(selected))

        self.line_trace_window = LineTrace(axis_data={"y": selected, "x": x})

    def xderivative_action(self):
        """
        Replace data by derivative of the data along x axis

        :return: NoneType
        """

        der_x_data = np.diff(self.plt_data, 1, 0)
        self.plot_elements["img"].setImage(der_x_data)

    def yderivative_action(self):
        """
        Replace data by derivative of the data along y axis.

        :return: NoneType
        """

        der_x_data = np.diff(self.plt_data, 1, 1)
        self.plot_elements["img"].setImage(der_x_data)

    def correct_data_action(self):
        """
        Ask user for input. After user inputs resistance, recalculate the values of the y axis. Additionally interpolate
        data to create values on the same setpoints with the new (corrected) data.

        :return: NoneType
        """
        self.input = helpers.InputData("Please input the resistance something something to correct your data")
        self.input.submitted.connect(self.proccess_data)

    def proccess_data(self, data):
        self.correction_resistance = float(data)

        dimensions = self.data_buffer.get_matrix_dimensions()
        matrix = self.data_buffer.get_matrix()
        y_data = self.data_buffer.get_y_axis_values()
        corrected_matrix = np.zeros((dimensions[0], dimensions[1]))

        biases = [1 if voltage >= 0 else -1 for voltage in y_data]

        for row in range(dimensions[0]):
            column = matrix[row, :]
            corrected_voltages = (abs(y_data) - abs(self.correction_resistance * column)) * biases

        print(y_data)
        print(column)
        print(corrected_voltages)

    def update_iso_curve(self):
        """
        When iso line element of the histogram is moved update the data on the main plot according to the value of the
        iso line on the histogram plot.

        :return: NoneType
        """
        self.plot_elements["iso"].setLevel(self.plot_elements["isoLine"].value())

    def mouse_moved(self, evt):
        """
        When moving a mouse check if the current mouse position is within the main plot of the Heatmap window. If it is
        then change the values in the status bar to the values of the point under the mouse cursor relative to the main
        plot of the Heatmap window (basically coordinates of the mouse cursor in the main plot)

        :param evt: signal that gets emitted when mouse is moved passes position of the mouse to the slot that gets that
        signal
        :return: NoneType
        """
        pos = evt
        if self.plot_elements["main_subplot"].sceneBoundingRect().contains(pos):
            mouse_point = self.plot_elements["main_subplot"].vb.mapSceneToView(pos)
            string = "[Position: {}, {}]".format(int(mouse_point.x()), int(mouse_point.y()))
            self.statusBar().showMessage(string)


def main():

    app = QApplication(sys.argv)

    # Daniels 3D measurement example in QCoDeS
    file_location = "K:\\Measurement\\Daniel\\2017-07-04\\#117_Belle_3to6_Daimond_PLLT_LTon700_CTon910_SLon1900_17-13-25\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"

    # Josip 3D measurement example in QtLab
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat"

    # Josips 3D measurement example matrix file
    # file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"

    # Matthias huge ass file
    # file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\005802_GatevsGate_W3_1I03_NW-l_g3@2060_g5@2260_BZ_0T_-_3T_time.dat"

    data = QtLabData(file_location)
    # data = MatrixData(file_location)

    ex = Heatmap(data=data)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
