import pyqtgraph as pg
import numpy as np
from math import degrees, radians, atan2, cos, sin, sqrt, tan
import ntpath
import sys
import os

from PyQt5.QtWidgets import QAction, QApplication, QToolBar, QComboBox, QSlider, QInputDialog, QSpinBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

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

    def __init__(self, data: DataBuffer, parent=None):
        """
        Inherits: BaseGraph()

        Used to display and manipulate data obtained by 3D measurements (Loop in a loop)

        :param data: DataBuffer(): Reference to a DataBuffer object that is being displayed in this window
        """
        print("Initializing heatmap window . . .")
        super().__init__(parent=parent)

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

        # saving transformations on main data buffer matrices, so that i dont need to recalculate them next time i need
        # them, gotta save that 0.1 sec bro
        self.plt_data_options = {}
        print("Loading matrices . . .")
        for i in range(len(self.plt_data)):
            name = "matrix" + str(i)
            self.plt_data_options[name] = {"xDer": None,
                                           "yDer": None,
                                           "xyDer": None,
                                           "yxDer": None,
                                           "corrected": None,
                                           "gauss": None}

        # to be able to switch between gauss, lorentz, normal, ...
        self.active_data = self.plt_data[0]

        self.active_data_name = "matrix0"

        self.active_data_index = 0

        self.displayed_data_set = self.active_data

        # indicates currently displayed data
        self.display = "normal"

        # references to all widgets in this window
        self.plot_elements = {}

        # references to all plots in side by side view
        self.side_by_side_plots = {}

        # reference to ROI
        self.line_segment_roi = {"ROI": None}

        # dictionary to keep track of options that have been turned on/off
        self.modes = {"ROI": False, "Side-by-side": False}

        # if data correction has been called at least once, this will not be None
        # need to move this to plt data options
        self.corrected_data = None

        self.unit_correction = 1000

        self.histogram_width = self.width() * 0.2

        self.init_ui()

    """
    ################################
    ######## User interface ########
    ################################
    """
    def init_ui(self):

        self.setGeometry(50, 50, 640, 400)
        self.setCentralWidget(self.plt)
        self.show()

        central_item = pg.GraphicsLayout()
        frame_layout = pg.GraphicsLayout()
        central_item.addItem(frame_layout)
        main_subplot = frame_layout.addPlot()
        img = pg.ImageItem()
        img.setImage(self.displayed_data_set, padding=0)
        img.translate(self.data_buffer.get_x_axis_values()[0], self.data_buffer.get_y_axis_values()[0])
        (x_scale, y_scale) = self.data_buffer.get_scale()
        img.scale(x_scale, y_scale)
        main_subplot.addItem(img, padding=0)
        x_min = min(self.data_buffer.get_x_axis_values())
        x_max = max(self.data_buffer.get_x_axis_values())
        y_min = min(self.data_buffer.get_y_axis_values())
        y_max = max(self.data_buffer.get_y_axis_values())
        main_subplot.setLimits(xMin=x_min, xMax=x_max, yMin=y_min, yMax=y_max)
        legend = {"left": "y", "bottom": "x"}
        print("Gathering axis data . . .")
        for side in ('left', 'bottom'):
            ax = main_subplot.getAxis(side)
            ax.setPen((60, 60, 60))
            ax.setZValue(10)
            ax.setStyle(tickLength=5)
            axis_data = self.data_buffer.axis_values[legend[side]]
            label_style = {'font-size': '10pt'}
            ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        iso = pg.IsocurveItem(level=0.8, pen='g')
        iso.setParentItem(img)
        iso.setData(pg.gaussianFilter(self.active_data, (2, 2)))

        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.gradient.loadPreset("thermal")
        histogram.setFixedWidth(self.histogram_width)
        axis_data = self.data_buffer.axis_values["z"][0]
        label_style = {'font-size': '8pt'}
        histogram.axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        histogram.vb.addItem(isoLine)
        histogram.vb.setMouseEnabled(y=False)  # makes user interaction a little easier
        isoLine.setValue(self.active_data.mean())
        isoLine.setZValue(1000)  # bring iso line above contrast controls
        isoLine.sigDragged.connect(self.update_iso_curve)

        central_item.addItem(histogram)
        self.plt.setCentralItem(central_item)
        self.plt.setBackground('w')
        central_item.nextRow()
        line_trace_graph = central_item.addPlot(colspan=2, pen=(60, 60, 60))
        line_trace_graph.setMaximumHeight(256)
        line_trace_graph.sigRangeChanged.connect(self.update_extra_axis_range)
        legend = {"left": "z", "bottom": "y", "top": "x"}
        print("Modeling axis data . . .")
        for axis in ["left", "bottom"]:
            ax = line_trace_graph.getAxis(axis)
            ax.show()
            ax.setPen((60, 60, 60))
            axis_data = self.data_buffer.axis_values[legend[axis]]
            label_style = {'font-size': '9pt'}
            if axis == "left":
                ax.setLabel(axis_data[0]["name"], axis_data[0]["unit"], **label_style)
            else:
                ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        line_trace_graph.layout.removeItem(
            line_trace_graph.getAxis("top")
        )
        extra_view_box = pg.ViewBox()
        extra_axis = pg.AxisItem("top")
        extra_axis.setPen((60, 60, 60))
        axis_data = self.data_buffer.axis_values[legend["top"]]
        label_style = {'font-size': '9pt'}
        extra_axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)
        line_trace_graph.layout.addItem(extra_axis, 0, 1)
        extra_axis.linkToView(extra_view_box)
        extra_view_box.setXLink(line_trace_graph.vb)

        pen = pg.mkPen("b", width=1)
        # v_line = pg.InfiniteLine(angle=90, movable=False, pen=pen)
        # h_line = pg.InfiniteLine(angle=0, movable=False, pen=pen)
        # line_trace_graph.addItem(v_line, ignoreBounds=True)
        # line_trace_graph.addItem(h_line, ignoreBounds=True)

        self.plot_elements = {"central_item": central_item, "frame": frame_layout, "main_subplot": main_subplot,
                              "img": img, "histogram": histogram, "line_trace_graph": line_trace_graph, "iso": iso,
                              "isoLine": isoLine, "extra_axis": extra_axis, "extra_view_box": extra_view_box}
                              # "v_line": v_line, "h_line": h_line}

        main_subplot.scene().sigMouseMoved.connect(self.mouse_moved)

        self.init_toolbar()

    def init_toolbar(self):
        """
        Create toolbar and add actions to it

        :return: NoneType
        """

        # ###############################
        # ##### Data manipulations ######
        # ###############################
        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)

        self.matrix_selection_combobox = QComboBox()
        for index, matrix in enumerate(self.plt_data):
            display_member = "matrix{}".format(index)
            value_member = matrix
            self.matrix_selection_combobox.addItem(display_member, value_member)
        display_member = "Side-by-side"
        value_member = None
        self.matrix_selection_combobox.addItem(display_member, value_member)
        self.matrix_selection_combobox.currentIndexChanged.connect(lambda: self.change_active_set(
            index=self.matrix_selection_combobox.currentIndex()))
        self.tools.addWidget(self.matrix_selection_combobox)
        self.line_trace_btn = QAction(QIcon("img/lineGraph"), "Line_Trace", self)
        self.line_trace_btn.setToolTip("Add an adjustable line to the main graph. Data 'below' the line is displayed\n"
                                       "in the line trace graph")
        self.line_trace_btn.setCheckable(True)
        self.tools.addAction(self.line_trace_btn)
        self.der_x = QAction(QIcon("img/xDer.png"), "xDerivative", self)
        self.der_x.setToolTip("Calculate and display x derivative of the displayed data")
        self.der_x.setCheckable(True)
        self.tools.addAction(self.der_x)
        self.der_y = QAction(QIcon("img/yDer.png"), "yDerivative", self)
        self.der_y.setToolTip("Calculate and display y derivative of the displayed data")
        self.der_y.setCheckable(True)
        self.tools.addAction(self.der_y)
        self.smoothing_selection_combobox = QComboBox()
        for smoothing_type in ["Naive", "Gaussian"]:
            self.smoothing_selection_combobox.addItem(smoothing_type)
        self.smoothing_selection_combobox.currentIndexChanged.connect(self.smoothing_action)
        self.tools.addWidget(self.smoothing_selection_combobox)
        self.smoothen_x = QSpinBox()
        self.smoothen_x.valueChanged.connect(self.smoothing_action)
        self.tools.addWidget(self.smoothen_x)
        self.smoothen_y = QSpinBox()
        self.smoothen_y.valueChanged.connect(self.smoothing_action)
        self.tools.addWidget(self.smoothen_y)

        # ###############################
        # #### Matrix manipulations #####
        # ###############################
        self.matrix_manipulation_toolbar = QToolBar("Matrix manipulation")
        self.matrix_manipulation_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(self.matrix_manipulation_toolbar)
        self.create_matrix_file_btn = QAction(QIcon("img/matrix-512.png"), "Matrix", self)
        self.create_matrix_file_btn.setToolTip("Create a raw matrix file from currently displayed data set")
        self.matrix_manipulation_toolbar.addAction(self.create_matrix_file_btn)
        self.data_correction_action = QAction(QIcon("img/line-chart.png"), "Correct_data", self)
        self.data_correction_action.setToolTip("Get Y(real) values calculated by formula: Y(real) = Y - (I * R)\n"
                                               "R is user input.")
        self.matrix_manipulation_toolbar.addAction(self.data_correction_action)
        # self.didv_correction_action_btn = QAction(QIcon("img/dIdV.png"), "didv_correction", self)
        # self.matrix_manipulation_toolbar.addAction(self.didv_correction_action_btn)

        self.gm_didv = QAction(QIcon("img/dIdV.png"), "gm_didv_correction", self)
        self.gm_didv.setToolTip("Get dV(real) values calculated by formula: dV(real) = dV - (dI * R)\n"
                                "dV, R are user input")
        self.matrix_manipulation_toolbar.addAction(self.gm_didv)

        # ###############################
        # #### Window manipulations #####
        # ###############################
        self.window_toolbar = QToolBar("Window toolbar")
        self.window_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(self.window_toolbar)
        self.customize_font_btn = QAction(QIcon("img/editFontIcon.png"), "Font", self)
        self.customize_font_btn.setToolTip("Open a widget that allows user to customise font and axis values")
        self.window_toolbar.addAction(self.customize_font_btn)
        self.open_2D = QAction(QIcon("img/2d_icon.png"), "Show_2d", self)
        self.open_2D.setToolTip("Open a selected line trace in new window that allows manipulation and transformations")
        self.window_toolbar.addAction(self.open_2D)
        self.zoom_action_btn = QAction(QIcon("img/zoomin_icon.png"), "Zoom", self)
        self.zoom_action_btn.setToolTip("Select area of graph to zoom into")
        self.window_toolbar.addAction(self.zoom_action_btn)
        self.exit_action_btn = QAction(QIcon("img/closeIcon.png"), "Exit", self)
        self.exit_action_btn.setToolTip("Close this heatmap window")
        self.window_toolbar.addAction(self.exit_action_btn)

        # self.init_line_trace_toolbar()

    def init_line_trace_toolbar(self):
        self.line_trace_toolbar = QToolBar("Line trace options")
        self.line_trace_toolbar.actionTriggered[QAction].connect(self.perform_action)

        for i, matrix in enumerate(self.plt_data):
            name = "matrix{}".format(i)
            toggle = QAction("M{}".format(i), self)
            toggle.setCheckable(True)
            toggle.setChecked(True)
            self.line_trace_toolbar.addAction(toggle)
            toggle.triggered.connect(lambda: self.toggle_display(name, toggle))

        self.addToolBar(Qt.RightToolBarArea, self.line_trace_toolbar)

    """
    ##################################
    ######## Helper functions ########
    ##################################
    """
    def change_active_set(self, index):
        """
        A method that changes what matrix is displayed in the main subplot, also changes data on which the actions
        from menu do the transformations. All matrices (for each measured parameter in your measurement there is one
        matrix) are selectable from a combobox (drop down) in the menu bar. Selected matrix is the ne displayed in the
        vombo box, and that is the one on which the transformations are done.

        :param index: integer: index of the data set in the combobox (also matches the index in self.plt_data)
                                After adding data to the combo box (example: doing data correction adds another matrix
                                to the combo box) additional matrices will be given index in order of adding them to
                                the combo box.
        :return: NoneType
        """
        if index == self.data_buffer.number_of_measured_parameters:
            self.plot_elements["histogram"].setFixedWidth(0)
            self.plot_elements["histogram"].hide()
            self.modes["Side-by-side"] = True
            self.plot_elements["frame"].clear()
            for i, matrix in enumerate(self.plt_data):
                name = "matrix{}".format(i)
                if name not in self.side_by_side_plots:
                    img = pg.ImageItem()
                    histogram = pg.HistogramLUTItem()
                    plot = self.plot_elements["frame"].addPlot()

                    img.setImage(matrix)
                    (x_scale, y_scale) = self.data_buffer.get_scale()
                    img.translate(self.data_buffer.get_x_axis_values()[0], self.data_buffer.get_y_axis_values()[0])
                    img.scale(x_scale, y_scale)

                    histogram.setImageItem(img)
                    histogram.gradient.loadPreset("thermal")
                    if i < self.data_buffer.number_of_measured_parameters:
                        axis_data = self.data_buffer.axis_values["z"][i]
                        label_style = {'font-size': '8pt'}
                        histogram.axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)
                    plot.addItem(img)
                    self.plot_elements["frame"].addItem(histogram)

                    for axis in ["left", "bottom"]:
                        ax = plot.getAxis(axis)
                        ax.setPen((60, 60, 60))

                    self.side_by_side_plots[name] = {"plot": plot, "img": img, "histogram": histogram}
                else:
                    # img = self.side_by_side_plots[name]["img"]
                    histogram = self.side_by_side_plots[name]["histogram"]
                    plot = self.side_by_side_plots[name]["plot"]
                    self.plot_elements["frame"].addItem(plot)
                    self.plot_elements["frame"].addItem(histogram)
        else:
            if self.modes["Side-by-side"]:
                self.plot_elements["histogram"].setFixedWidth(self.histogram_width)
                self.plot_elements["histogram"].show()
                self.plot_elements["frame"].clear()
                self.modes["Side-by-side"] = False
                self.plot_elements["frame"].addItem(self.plot_elements["main_subplot"])
            if index > self.data_buffer.number_of_measured_parameters:
                index -= 1
            self.active_data = self.plt_data[index]
            index = self.matrix_selection_combobox.currentIndex()
            name = self.matrix_selection_combobox.currentText()
            self.active_data_name = name
            self.active_data_index = index
            self.change_displayed_data_set(self.active_data)

            if index < self.data_buffer.number_of_measured_parameters:
                axis_data = self.data_buffer.axis_values["z"][index]
                label_style = {'font-size': '8pt'}
                self.plot_elements["histogram"].axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)
                label_style = {'font-size': '9pt'}
                self.plot_elements["line_trace_graph"].getAxis("left").setLabel(axis_data["name"], axis_data["unit"], **label_style)
        self.reset_transformations()

    def change_displayed_data_set(self, data_set):
        """
        A helper method for changing active data set. Changes the item which is being displayed in the imgItem element
        of the main subplot.

        :param data_set: np.array: numpy array representing one measured parameter (measured values)
        :return: NoneType
        """
        self.displayed_data_set = data_set
        self.plot_elements["img"].setImage(self.displayed_data_set)
        self.plot_elements["isoLine"].setValue(self.displayed_data_set.mean())
        self.plot_elements["histogram"].setImageItem(self.plot_elements["img"])
        self.plot_elements["histogram"].gradient.loadPreset("thermal")
        if self.modes["ROI"]:
            self.update_line_trace_plot()

    def reset_transformations(self):
        """
        Reset values of all changeable actions in the menu bar (ones that are checkable, and also smoothing spin boxes)
        If action was activated for a previously selected matrix, then deactivate that action.

        :return: NoneType
        """
        for action in self.tools.actions():
            if action.isChecked():
                action.trigger()
        self.smoothen_y.setValue(0)
        self.smoothen_x.setValue(0)

    def open_line_trace_menues(self):
        """
        Method that hdies/displays additional menues for controling what is displayed in the line trace graph

        :return: NoneType
        """
        if self.modes["Side-by-side"] and self.modes["ROI"]:
            self.line_trace_toolbar.show()
        else:
            self.line_trace_toolbar.hide()

    def toggle_display(self, matrix, action):
        if action.isChecked():
            self.side_by_side_plots[matrix]["plot"].show()
            self.side_by_side_plots[matrix]["histogram"].show()
        else:
            self.side_by_side_plots[matrix]["plot"].hide()
            self.side_by_side_plots[matrix]["histogram"].hide()

    """
    #########################
    ######## Actions ########
    #########################
    """
    def line_trace_action(self):
        """
        Add a line segment region of interest (ROI) to the main subplot. Connect it to a function that updates line
        trace graph anytime one of the handles or the ROI itself is moved.

        :return:
        """
        # self.open_line_trace_menues()

        if self.modes["ROI"] == False:
            self.modes["ROI"] = True

            if self.line_segment_roi["ROI"] is None:
                # ROI instantiation
                x0 = min(self.data_buffer.get_x_axis_values())
                y0 = min(self.data_buffer.get_y_axis_values())

                x1 = min(self.data_buffer.get_x_axis_values())
                y1 = max(self.data_buffer.get_y_axis_values())

                line_segmet_roi = LineROI(positions=([x0, y0], [x1, y1]),
                                          pos=(0, 0),
                                          pen=(5, 9),
                                          edges=[self.data_buffer.get_x_axis_values()[0],
                                                 self.data_buffer.get_x_axis_values()[-1],
                                                 self.data_buffer.get_y_axis_values()[0],
                                                 self.data_buffer.get_y_axis_values()[-1]])
                self.label_a = pg.TextItem("[A]", color=(255, 255, 255))
                self.label_a.setAnchor((0, 1))
                self.label_a.setParentItem(line_segmet_roi)
                self.label_a.setPos(x0, y0)
                self.label_b = pg.TextItem("[B]", color=(255, 255, 255))
                self.label_b.setAnchor((0, 0))
                self.label_b.setParentItem(line_segmet_roi)
                self.label_b.setPos(x1, y1)

                # connect signal to a slot
                line_segmet_roi.sigRegionChanged.connect(self.update_line_trace_plot)
                # make a reference to this ROI so i can use it later
                self.line_segment_roi["ROI"] = line_segmet_roi
                # add the ROI to main subplot
                self.plot_elements["main_subplot"].addItem(line_segmet_roi)
                self.plot_elements["main_subplot"].addItem(self.label_a)
                self.plot_elements["main_subplot"].addItem(self.label_b)
                # connect signal to a slot, this signal
                line_segmet_roi.aligned.connect(self.update_line_trace_plot)
            else:
                self.line_segment_roi["ROI"].show()
                self.label_a.show()
                self.label_b.show()
                self.plot_elements["line_trace_graph"].addItem(self.plot_elements["v_line"])
                self.plot_elements["line_trace_graph"].addItem(self.plot_elements["h_line"])

        else:
            self.modes["ROI"] = False
            self.plot_elements["line_trace_graph"].clear()
            self.line_segment_roi["ROI"].hide()
            self.label_a.hide()
            self.label_b.hide()

    def side_by_side_line_trace(self):
        pass

    def font_action(self):
        """
        Opens a new widget that allows user to modify font sizes on axis of all graphs in this window

        :return: NoneType
        """
        self.eaw = helpers.Edit3DAxisWidget(self)
        self.eaw.submitted.connect(self.edit_axis_data)
        self.eaw.show()

    def smoothing_action(self):
        """
        A method used to call a smoothing algorithm selected from the drop down menu in the toolbar.

        :return: NoneType
        """
        smoothing_type = self.smoothing_selection_combobox.currentText().lower()
        method_name = smoothing_type + "_smoothing"
        method = getattr(self, method_name)
        method()

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

        def save_matrix(data):
            user_input_name = data
            new_file_location = helpers.get_location_path(location) + "\\" + user_input_name + "_generated_correction"
            file = open(new_file_location, "w")
            raw_data = np.transpose(self.displayed_data_set)
            np.savetxt(file, raw_data, delimiter="\t")
            file.close()

        location = self.data_buffer.location
        name = helpers.get_location_basename(location)
        index = self.active_data_index
        if index > self.data_buffer.number_of_measured_parameters:
            self.select_file_name = helpers.InputData("Please select the name of the output file.", default_value=name)
            self.select_file_name.submitted.connect(save_matrix)
        elif self.modes["Side-by-side"]:
            helpers.show_error_message("NO, U CANT DO THAT !",
                                       "Creating a matrix file for side by side view is not possible.")
        else:
            self.data_buffer.create_matrix_file(index)

    def show_2d_action(self):
        """
        Opens a line trace graph window for a line trace selected by line_trace_roi

        :return:
        """
        data = self.displayed_data_set
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
        if self.der_y.isChecked():
            name = self.active_data_name
            if self.der_x.isChecked():
                if self.plt_data_options[name]["yxDer"] is None:
                    der_yx_data = np.diff(self.plt_data_options[name]["yDer"], 1, 0)
                    self.plt_data_options[name]["yxDer"] = der_yx_data
                else:
                    der_yx_data = self.plt_data_options[name]["yxDer"]
                self.change_displayed_data_set(der_yx_data)
            else:
                self.change_displayed_data_set(self.plt_data_options[name]["yDer"])
        else:
            if self.der_x.isChecked():
                name = self.active_data_name
                if self.plt_data_options[name]["xDer"] is None:
                    der_x_data = np.diff(self.active_data, 1, 0)
                    self.plt_data_options[name]["xDer"] = der_x_data
                else:
                    der_x_data = self.plt_data_options[name]["xDer"]
                self.change_displayed_data_set(der_x_data)
            else:
                self.change_displayed_data_set(self.active_data)

    def yderivative_action(self):
        """
        Replace data by derivative of the data along y axis.

        :return: NoneType
        """
        if self.der_x.isChecked():
            name = self.active_data_name
            if self.der_y.isChecked():
                if self.plt_data_options[name]["xyDer"] is None:
                    der_xy_data = np.diff(self.plt_data_options[name]["xDer"], 1, 1)
                    self.plt_data_options[name]["xyDer"] = der_xy_data
                else:
                    der_xy_data = self.plt_data_options[name]["xyDer"]
                self.change_displayed_data_set(der_xy_data)
            else:
                self.change_displayed_data_set(self.plt_data_options[name]["xDer"])

        else:
            if self.der_y.isChecked():
                name = self.active_data_name
                if self.plt_data_options[name]["yDer"] is None:
                    der_y_data = np.diff(self.active_data, 1, 1)
                    self.plt_data_options[name]["yDer"] = der_y_data
                else:
                    der_y_data = self.plt_data_options[name]["yDer"]
                self.change_displayed_data_set(der_y_data)
            else:
                self.change_displayed_data_set(self.active_data)

    def correct_data_action(self):
        """
        Ask user for input. After user inputs resistance, recalculate the values of the y axis. Additionally interpolate
        data to create values on the same setpoints with the new (corrected) data.

        :return: NoneType
        """
        self.input = helpers.InputData("Please input the resistance something something to correct your data", 1,
                                       numeric=[True], placeholders=["Resistance"])
        self.input.submitted.connect(self.apply_correction)

    def naive_smoothing(self):
        """
        Method that smoothens the data by calculating the average of the n points to the left and right of point P,
        and setting the value of P to the calculated value.

        Example:

        [[1, 4, 3],
         [2, 8, 2],
         [3, 5, 6]]

         If this example matrix is smoothened in the x axis direction with a value 1 (1 to the left and 1 to the right
          of the data point) the result matrix would be:

         [[2.5, 2.66, 3.5], -> (1+4) / 2 = 2.5 \\\\ (1+4+3) / 3 = 2.66 \\\\ (4+3) / 2 = 3.5
          [5, 4, 5]         -> (2+8) / 2 = 5 \\\\ (2+8+2) / 3 = 4 \\\\ (8+2) / 2 = 5
          [4, 4.66, 5.5]]   -> (3+5) / 2 = 4 \\\\ (3+5+6) / 3 = 4.66 \\\\ (5+6) / 2 = 5.5

        :return:
        """
        x = self.smoothen_x.value()
        y = self.smoothen_y.value()
        data = self.active_data

        vertical_shift = np.copy(data)
        horizontal_shift = np.copy(np.transpose(data))
        for i, axis in enumerate([x, y]):
            for shift_value in range(-axis, axis + 1):
                if shift_value != 0:
                    if i:
                        temp = helpers.shift(np.transpose(data), shift_value, 0)
                        np.add(horizontal_shift, temp, horizontal_shift)
                    else:
                        temp = helpers.shift(data, shift_value, 0)
                        np.add(vertical_shift, temp, vertical_shift)
        limit_vertical = len(vertical_shift) - 1
        limit_horizontal = len(horizontal_shift) - 1
        for index, row in enumerate(vertical_shift):
            low = index - y if index - y >= 0 else 0
            high = index + y if index + y <= limit_vertical else limit_vertical
            division_number = high - low + 1
            row = row / division_number
            vertical_shift[index] = row
        for index, column in enumerate(horizontal_shift):
            low = index - x if index - x >= 0 else 0
            high = index + x if index + x <= limit_horizontal else limit_horizontal
            division_number = high - low + 1
            column = column / division_number
            horizontal_shift[index] = column
        result = (vertical_shift + np.transpose(horizontal_shift)) / 2

        self.change_displayed_data_set(result)

    def gaussian_smoothing(self):
        """
        Method that smoothens the data by using existing gaussianFilter function implemented in numpy python library.

        :return:
        """
        x = self.smoothen_x.value()
        y = self.smoothen_y.value()  # apply this to displayed set, instead of this below

        smoothened_data = pg.gaussianFilter(self.active_data, (x, y))
        self.change_displayed_data_set(smoothened_data)

    def gm_didv_correction_action(self):
        """
        Method that instantiates a helper widget (InputData) used to input data necessary to perform dIdV correction.
        InputData has a signal that gets emitted when submit button is pressed. Signal carries data and is connected
        to a method that performs required action.

        :return: NoneType
        """
        self.didv_input = helpers.DiDvCorrectionInputWidget(parent=self)
        self.didv_input.submitted.connect(self.apply_gm_didv_correction)

    def zoom_action(self):
        """
        Method that instantiates a helper widget (InputData) used to input data necessary to perform zoom action.
        InputData has a signal that gets emitted when submit button is pressed. Signal carries data and is connected
        to a method that performs required action.

        :return: NoneType
        """
        current_x_min = min(self.data_buffer.get_x_axis_values())
        current_x_max = max(self.data_buffer.get_x_axis_values())
        current_y_min = min(self.data_buffer.get_y_axis_values())
        current_y_max = max(self.data_buffer.get_y_axis_values())
        self.input = helpers.InputData("Please input ranges of values to display", 4,
                                       numeric=[True, True, True, True],
                                       placeholders=["Start X value [Currently: {}]".format(current_x_min),
                                                     "End X value [Currently {}]".format(current_x_max),
                                                     "Start Y value [Currently {}]".format(current_y_min),
                                                     "End Y value [Currently {}]".format(current_y_max)])
        self.input.submitted.connect(self.zoom_to_range)

    """
    ########################
    ######## Events ########
    ########################
    """
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
            string = "[Position: {}, {}]".format(round(mouse_point.x(), 3), round(mouse_point.y(), 3))
            self.statusBar().showMessage(string)
        elif self.plot_elements["line_trace_graph"].sceneBoundingRect().contains(pos):
            mouse_point = self.plot_elements["line_trace_graph"].vb.mapSceneToView(pos)
            string = "[Position: {}, {}]".format(round(mouse_point.x(), 3), round(mouse_point.y(), 3))
            self.statusBar().showMessage(string)
            # self.plot_elements["v_line"].setPos(mouse_point.x())
            # self.plot_elements["h_line"].setPos(mouse_point.y())

    def update_line_trace_plot(self):
        """
        Each time a line trace is moved this method is called to update the line trace graph element of the Heatmap
        widget.

        :return: NoneType
        """

        self.update_point_label_positions()

        data = self.displayed_data_set
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        line_trace_graph = self.plot_elements["line_trace_graph"]
        new_plot = line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True)
        new_plot.setZValue(10)
        point = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = point
        coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)

        point1 = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = point1
        start_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        point2 = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
        _, scene_coords = point2
        end_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)

        if (180 - abs(self.line_segment_roi["ROI"].get_angle_from_points())) < 0.0000001:
            self.plot_elements["line_trace_graph"].getAxis("bottom").hide()
            self.plot_elements["extra_axis"].show()
            new_plot.translate(coords.x(), 0)
            line_trace_graph.setXRange(start_coords.x(), end_coords.x())
            scale = end_coords.x() - start_coords.x()
        elif abs(self.line_segment_roi["ROI"].get_angle_from_points()) < 0.0000001:
            self.plot_elements["line_trace_graph"].getAxis("bottom").hide()
            self.plot_elements["extra_axis"].show()
            new_plot.translate(coords.x(), 0)
            line_trace_graph.setXRange(start_coords.x(), end_coords.x())
            scale = end_coords.x() - start_coords.x()
        elif abs(90 - abs(self.line_segment_roi["ROI"].get_angle_from_points())) < 0.0000001:
            self.plot_elements["line_trace_graph"].getAxis("bottom").show()
            self.plot_elements["extra_axis"].hide()
            new_plot.translate(coords.y(), 0)
            line_trace_graph.setXRange(start_coords.y(), end_coords.y())
            scale = end_coords.y() - start_coords.y()
        else:
            self.plot_elements["line_trace_graph"].getAxis("bottom").show()
            self.plot_elements["extra_axis"].show()
            new_plot.translate(coords.y(), 0)
            line_trace_graph.setXRange(start_coords.y(), end_coords.y())
            scale = end_coords.y() - start_coords.y()

        num_of_points = len(selected) - 1
        if num_of_points == 0:
            num_of_points = 1
        new_plot.scale(scale/num_of_points, 1)

    def apply_correction(self, data):
        """
        This method gets data from a signal emitted by a window (InputData) designed to input data required to perform
        this method.
        After fetching the data, new matrix is created and filled by corrected data.

        Data is calculated using the formula: Y(real) = Y - (I * R) where R is obtained by user input in the InputWindow

        After generating new matrix, it is added to a dictionery of matrices and is available for selection in dropdown
        located in the toolbar and can be displayed it the window.

        :param data: array: contains just one member, value of R (resistance) needed to calculate the correction
                            This array is sent to this method as a signal from the InputWindow widget.
        :return: NoneType
        """
        self.correction_resistance = float(data[0])

        dimensions = self.data_buffer.get_matrix_dimensions()
        matrix = self.active_data
        y_data = self.data_buffer.get_y_axis_values()
        corrected_matrix = np.zeros((dimensions[0], dimensions[1]))

        biases = [1 if voltage >= 0 else -1 for voltage in y_data]

        for row in range(dimensions[0]):
            column = matrix[row, :]
            corrected_voltages = (abs(y_data) - abs(self.correction_resistance * column) * self.unit_correction) * biases

            xp = corrected_voltages
            fp = column

            if np.all(np.diff(y_data) > 0):
                corrected_matrix[row, :] = np.interp(y_data, xp, fp, left=0, right=0)
            else:
                reversed_y_data = y_data[::-1]
                reversed_xp = xp[::-1]
                reversed_fp = fp[::-1]

                reversed_matrix_column = np.interp(reversed_y_data, reversed_xp, reversed_fp,
                                                   left=0, right=0)
                column = reversed_matrix_column[::-1]
                corrected_matrix[row, :] = column

        display_member = "corrected_" + self.active_data_name
        value_member = corrected_matrix
        self.matrix_selection_combobox.addItem(display_member, value_member)
        # ###########################################################
        # ###########################################################
        # #### THIS THING HERE ADDS EXTRA MATRIX TO DATA BUFFER #####
        # ###########################################################
        # ###########################################################

        self.plt_data.append(value_member)
        self.plt_data_options[display_member] = {"xDer": None,
                                                 "yDer": None,
                                                 "xyDer": None,
                                                 "yxDer": None,
                                                 "corrected": None,
                                                 "gauss": None}
        # self.corrected_data = corrected_matrix

    def apply_gm_didv_correction(self, data):
        """
        This method gets data from a signal emitted by a window (InputData) designed to input data required to perform
        this method.
        After fetching the data, new matrix is created and filled by corrected data.

        Data is calculated using the formula: dV(real) = dV - (dI * R) where R and dV are obtained by user input in the
        InputWindow.

        After generating new matrix, it is added to a dictionery of matrices and is available for selection in dropdown
        located in the toolbar and can be displayed it the window.

        :param data: array: contains value of R, dV and a matrix to which we apply the correction to. Passed to this
                            method as a signal from InputWindow widget.
        :return: NoneType
        """
        self.didv_correction_resistance = float(data[0])
        self.didv_correction_dv = float(data[1])

        dimensions = self.data_buffer.get_matrix_dimensions()
        currents_matrix = data[2]
        matrix = self.active_data
        y_data = self.data_buffer.get_y_axis_values()
        corrected_matrix = np.zeros((dimensions[0], dimensions[1]))

        biases = [1 if voltage >= 0 else -1 for voltage in y_data]

        for row in range(dimensions[0]):
            column = currents_matrix[row, :]
            corrected_voltages = (abs(y_data) - abs(
                self.didv_correction_resistance * column) * self.unit_correction) * biases
            xp = corrected_voltages
            fp = matrix[row, :]
            if np.all(np.diff(y_data) > 0):
                corrected_matrix[row, :] = np.interp(y_data, xp, fp, left=0, right=0)
            else:
                reversed_y_data = y_data[::-1]
                reversed_xp = xp[::-1]
                reversed_fp = fp[::-1]

                reversed_matrix_column = np.interp(reversed_y_data, reversed_xp, reversed_fp,
                                                   left=0, right=0)
                column = reversed_matrix_column[::-1]
                corrected_matrix[row, :] = column

        didv_matrix = self.didv_correction_dv - (corrected_matrix * self.didv_correction_resistance)
        corrected_didv_matrix = corrected_matrix / didv_matrix

        display_member = "didv_" + self.active_data_name
        value_member = corrected_didv_matrix
        self.matrix_selection_combobox.addItem(display_member, value_member)
        # ###########################################################
        # ###########################################################
        # #### THIS THING HERE ADDS EXTRA MATRIX TO DATA BUFFER #####
        # ###########################################################
        # ###########################################################

        self.plt_data.append(value_member)
        self.plt_data_options[display_member] = {"xDer": None,
                                                 "yDer": None,
                                                 "xyDer": None,
                                                 "yxDer": None,
                                                 "corrected": None,
                                                 "gauss": None}
        # self.corrected_data = corrected_matrix

    def edit_axis_data(self, data):
        """
        A method that accepts data from the signal created by EditAxisWidget. It changes the appearance of the graphs
        axes by changing various parameters (font, text, ...).

        :param data: dictionary: contains user input specified in the EditAxisWidget
        :return: NoneType
        """
        for element, sides in data.items():
            if element != "histogram":
                for side, options in sides.items():
                    if side != "top":
                        axis = self.plot_elements[element].getAxis(side)
                        axis.setLabel(options["name"], options["unit"], **options["label_style"])
                        if options["ticks"]["font"] != "":
                            font = QFont()
                            font.setPixelSize(int(options["ticks"]["font"]))
                            axis.tickFont = font
                            axis.setStyle(tickTextOffset=int(int(options["ticks"]["font"])/2))
                        # axis.setTickSpacing(major=float(options["ticks"]["major"]),
                        #                     minor=float(options["ticks"]["minor"]))
                    else:
                        axis = self.plot_elements["extra_axis"]
                        axis.setLabel(options["name"], options["unit"], **options["label_style"])
                        if options["ticks"]["font"] != "":
                            font = QFont()
                            font.setPixelSize(int(options["ticks"]["font"]))
                            axis.tickFont = font
                            axis.setStyle(tickTextOffset=int(int(options["ticks"]["font"])/2))
            else:
                axis = self.plot_elements["histogram"].axis
                axis.setLabel(sides["name"], sides["unit"], **sides["label_style"])
                # axis.setTickSpacing(major=float(sides["ticks"]["major"]),
                #                     minor=float(sides["ticks"]["minor"]))
                if data["histogram"]["ticks"]["font"] != "":
                    font = QFont()
                    font.setPixelSize(int(data["histogram"]["ticks"]["font"]))
                    axis.tickFont = font
                    axis.setStyle(tickTextOffset=int(int(data["histogram"]["ticks"]["font"]) / 2),
                                  tickLength=int(5))

    def update_extra_axis_range(self):
        """
        Updates extra axis (positioned on top of the line trace graph) when the main x axis of line trace graph changes
        its value (dragged by user).

        :return: NoneType
        """

        # if ROI is visible do the adjustments
        if self.modes["ROI"]:
            # get starting and ending point of the ROI
            point1 = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
            _, scene_coords = point1
            start_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
            point2 = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
            _, scene_coords = point2
            end_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)

            # calcualate distances between points (used to calculate angle of ROI)
            x_diff = end_coords.x() - start_coords.x()
            y_diff = end_coords.y() - start_coords.y()

            # calculate angle of ROI (result is in radians)
            angle = atan2(y_diff, x_diff)

            # calculate tangent of the angle
            angle_tan = tan(angle)

            # extra axis is linked to this view box
            view_box = self.plot_elements["line_trace_graph"].vb

            # padded start of the x axis of line trace graph (pyqtgraph by default adds a padding to plots)
            # need to get the starting point of axis (not starting point of data that is being ploted)
            start_value_x_axis = view_box.state["viewRange"][0][0]
            # padded end of the x axis of line trace graph
            end_value_x_axis = view_box.state["viewRange"][0][1]

            # pyqtgraph forces padding in viewboxes (0.02 - 0.1 of total data range)
            # in the end i did not need this padding, but lets leave it here i might need it later
            padding = view_box.suggestPadding(0)

            # when line is vertical, extra axis (positioned on the top) should not be shown because its range is 0
            # begining and the end of the data is on the same point
            if abs(90 - abs(self.line_segment_roi["ROI"].get_angle_from_points())) < 0.0000001:
                pass
            # when line is horizontal set the same values as bottom axis. This is because in case when ROI line is
            # horizontal i set the bottom axis to reflect x range from the main plot (this simplifies this process)
            # Orientation of the line in this case is [B]o--------------o[A]
            elif (180 - abs(self.line_segment_roi["ROI"].get_angle_from_points())) < 0.0000001:
                start_value_extra_axis = start_value_x_axis
                end_value_extra_axis = end_value_x_axis
                self.plot_elements["extra_view_box"].setXRange(start_value_extra_axis, end_value_extra_axis, padding=0)
            # same as above, horizontal, but like this -> [A]o-------------o[B]
            elif abs(self.line_segment_roi["ROI"].get_angle_from_points()) < 0.0000001:
                start_value_extra_axis = start_value_x_axis
                end_value_extra_axis = end_value_x_axis
                self.plot_elements["extra_view_box"].setXRange(start_value_extra_axis, end_value_extra_axis, padding=0)
            # In all other cases both axes need to be shown. In this case take the value of the edges from x axis
            # which is actualy y axis in the main plot, and calculate what is the value of x on main plot for given y
            # set calculated values as end values of extra axis (one positioned on top of line trace graph)
            else:  # NOTE: This has 4 different options
                # Option 1: Both starting and ending point of the ROI are visible on line trace graph
                if (start_coords.y() > start_value_x_axis) and (end_coords.y() < end_value_x_axis):
                    delta_x_start = start_coords.y() - start_value_x_axis
                    delta_y_start = delta_x_start / angle_tan
                    delta_x_end = end_value_x_axis - end_coords.y()
                    delta_y_end = delta_x_end / angle_tan
                    start_value_extra_axis = start_coords.x() - delta_y_start
                    end_value_extra_axis = end_coords.x() + delta_y_end
                # Option 2: starting point has been dragged outside of the visible range on line trace graph
                elif (start_coords.y() < start_value_x_axis) and (end_coords.y() < end_value_x_axis):
                    delta_x_start = start_value_x_axis - start_coords.y()
                    delta_y_start = delta_x_start / angle_tan
                    delta_x_end = end_value_x_axis - end_coords.y()
                    delta_y_end = delta_x_end / angle_tan
                    start_value_extra_axis = start_coords.x() + delta_y_start
                    end_value_extra_axis = end_coords.x() + delta_y_end
                # Option 3: ending point has been draged outside of the visible range of line trace graph
                elif (start_coords.y() > start_value_x_axis) and (end_coords.y() > end_value_x_axis):
                    delta_x_start = start_coords.y() - start_value_x_axis
                    delta_y_start = delta_x_start / angle_tan
                    delta_x_end = end_coords.y() - end_value_x_axis
                    delta_y_end = delta_x_end / angle_tan
                    start_value_extra_axis = start_coords.x() - delta_y_start
                    end_value_extra_axis = end_coords.x() - delta_y_end
                # Option 4: graph has been zoomed in and neither starting or ending point are visible on the line trace
                # graph
                else:
                    delta_x_start = start_value_x_axis - start_coords.y()
                    delta_y_start = delta_x_start / angle_tan
                    delta_x_end = end_coords.y() - end_value_x_axis
                    delta_y_end = delta_x_end / angle_tan
                    start_value_extra_axis = start_coords.x() + delta_y_start
                    end_value_extra_axis = end_coords.x() - delta_y_end

                self.plot_elements["extra_view_box"].setXRange(start_value_extra_axis, end_value_extra_axis, padding=0)
            # In some cases extra axis (positioned on top of line trace graph) needs to be inverted, otherwise it
            # shows incorrect data
            if abs(degrees(angle)) > 90:
                if not self.plot_elements["extra_view_box"].xInverted():
                    self.plot_elements["extra_view_box"].invertX(True)
            else:
                if self.plot_elements["extra_view_box"].xInverted():
                    self.plot_elements["extra_view_box"].invertX(False)
        else:
            pass

    def update_point_label_positions(self):
        """
        Method that moves labels for point A and B of the LineROI when one of them (or both) get moved.

        :return: NoneType
        """
        point1 = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = point1
        coords_a = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        point2 = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
        _, scene_coords = point2
        coords_b = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)

        self.label_a.setPos(coords_a.x(), coords_a.y())
        self.label_b.setPos(coords_b.x(), coords_b.y())

    def keyPressEvent(self, event):
        """
        TODO: Write documentation

        :param event:
        :return:
        """

        if self.modes["ROI"]:
            if event.key() in [Qt.Key_Up, Qt.Key_Down]:
                distance = abs(self.data_buffer.get_y_axis_values()[1] - self.data_buffer.get_y_axis_values()[0])
            elif event.key() in [Qt.Key_Right, Qt.Key_Left]:
                distance = abs(self.data_buffer.get_x_axis_values()[1] - self.data_buffer.get_x_axis_values()[0])
            else:
                return
            self.line_segment_roi["ROI"].arrow_move(event.key(), distance)

    def zoom_to_range(self, data):
        """
        TODO: Write documentation

        :param data:
        :return:
        """

        x_min, x_max, y_min, y_max = float(data[0]), float(data[1]), float(data[2]), float(data[3])
        self.plot_elements["main_subplot"].vb.setXRange(x_min, x_max, padding=0)
        self.plot_elements["main_subplot"].vb.setYRange(y_min, y_max, padding=0)


def main():
    app = QApplication(sys.argv)

    # Daniels 3D measurement example in QCoDeS
    # file_location = "K:\\Measurement\\Daniel\\2017-07-04\\#117_Belle_3to6_Daimond_PLLT_LTon700_CTon910_SLon1900_17-13-25\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"

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
