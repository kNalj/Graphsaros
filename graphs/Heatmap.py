import pyqtgraph as pg
import numpy as np
from math import degrees, atan2, tan
import sys

from PyQt5.QtWidgets import QAction, QApplication, QToolBar, QComboBox, QSpinBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

from helpers import get_location_path, get_location_basename, show_error_message, shift
from widgets import DiDvCorrectionInputWidget, EditAxisWidget, InputDataWidget
from graphs.BaseGraph import BaseGraph
from graphs.LineTrace import LineTrace
from data_handlers.DataBuffer import DataBuffer
from data_handlers.Dummy2D import DummyBuffer
from data_handlers.QcodesDataBuffer import QcodesData
from custom_pg.LineROI import LineROI
from custom_pg.ColorBar import ColorBarItem
from custom_pg.ImageItem import ImageItem


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
        self.setWindowTitle(data.name)

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

        # name of the data that will be displayed (by default) will allways be matrix0 (index of the matrix of first
        # parameter will allways be 0)
        self.active_data_name = "matrix0"

        # same as above
        self.active_data_index = 0

        # by default, allways display the first measured parameter
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
        """
        This method builds and places user interface elements within the window.

        :return:
        """
        print("Initializing UI . . .")
        # Setting the position and size of the window
        self.setGeometry(50, 50, 800, 600)
        # Central widget is the mail element of the window, all other elements are added to the central widget
        self.setCentralWidget(self.plt)
        self.show()

        # Design of the window is shown in the image that can be found in the file
        # https://github.com/kNalj/Graphsaros/blob/master/docs/img/Heatmap.png
        central_item = pg.GraphicsLayout()
        frame_layout = pg.GraphicsLayout()
        central_item.addItem(frame_layout)
        # add a title to the plot, so that when exported, the image shows the name of the measurement
        main_subplot = frame_layout.addPlot(title=self.data_buffer.name)
        main_subplot.titleLabel.hide()
        # print(main_subplot.vb.menu.)
        img = ImageItem()
        # set the default data as the image data
        img.setImage(self.displayed_data_set, padding=0)
        # reposition the data to correct starting position (x0, y0)
        img.translate(self.data_buffer.get_x_axis_values()[0], self.data_buffer.get_y_axis_values()[0][0])
        # by default data is drawn on x axis: from 0 to number of points along x axis, also for y: 0 to num of points
        # on y axis (example: steping 1 param 100 to 110, and steping another 20 to 40 would result in in data being
        # drawn 0 to 10 on x axis, and 0 to 20 on y axis)
        # This is way data needs to be scaled after selecting the initial point
        (x_scale, y_scale) = self.data_buffer.get_scale()
        img.scale(x_scale, y_scale)
        main_subplot.addItem(img, padding=0)

        print("Determining graph limits . . .")
        # Seting the limits of the graph so that the user can not go out of the image range
        x_min = min(self.data_buffer.get_x_axis_values())
        x_max = max(self.data_buffer.get_x_axis_values())
        y_min = min(self.data_buffer.get_y_axis_values()[0])
        y_max = max(self.data_buffer.get_y_axis_values()[0])
        main_subplot.setLimits(xMin=x_min, xMax=x_max, yMin=y_min, yMax=y_max)

        print("Updating labels . . .")
        # Get the data about axis labels and units from the data buffer and apply them to the plot
        legend = {"left": "y", "bottom": "x"}
        print("Gathering axis data . . .")
        for side in ('left', 'bottom'):
            ax = main_subplot.getAxis(side)
            ax.setPen((60, 60, 60))
            ax.setZValue(10)
            ax.setStyle(tickLength=5)
            # ax.setPen("k", width=1.5)  # This changes the
            # print(ax._pen.width())
            # print(ax._tickSpacing)  # Yields None ?!?
            if legend[side] == "y":
                axis_data = self.data_buffer.axis_values[legend[side]][0]
            else:
                axis_data = self.data_buffer.axis_values[legend[side]]
            label_style = {'font-size': '10pt'}
            ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        # Add a controllable curve that shows values greater then selected value (similar to lines used to show
        # mountains on geographical maps)
        iso = pg.IsocurveItem(level=0.8, pen='g')
        iso.setParentItem(img)
        iso.setData(pg.gaussianFilter(self.active_data, (2, 2)))

        # Add a histogram to control the colors displayed on the image
        print("Building histogram . . .")
        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.gradient.loadPreset("thermal")
        histogram.setFixedWidth(self.histogram_width)
        axis_data = self.data_buffer.axis_values["z"][0]
        label_style = {'font-size': '8pt'}
        histogram.axis.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        print("Building color bar item . . .")
        color_bar = ColorBarItem(parent=main_subplot, image=img, label=axis_data["name"])
        color_bar.layout.setContentsMargins(10, 30, 0, 45)
        color_bar.hide()
        frame_layout.addItem(color_bar)

        # Add control for the isoLine to the histogram
        print("Building iso line . . .")
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

        # Add line trace graph to the next row of the central item
        print("Building line trace graph . . .")
        line_trace_graph = central_item.addPlot(colspan=3, pen=(60, 60, 60))
        line_trace_graph.setMaximumHeight(256)
        line_trace_graph.sigRangeChanged.connect(self.update_extra_axis_range)
        line_trace_graph.scene().sigMouseClicked.connect(self.mark_current_line_trace_point)
        line_trace_graph.hide()

        # configure axes of the line trace graph
        legend = {"left": "z", "bottom": "y", "top": "x"}
        print("Modeling axis data . . .")
        for axis in ["left", "bottom"]:
            ax = line_trace_graph.getAxis(axis)
            ax.show()
            ax.setPen((60, 60, 60))
            axis_data = self.data_buffer.axis_values[legend[axis]]
            label_style = {'font-size': '9pt'}
            ax.setLabel(axis_data[0]["name"], axis_data[0]["unit"], **label_style)

        # Add the third axis (top one) and connect it to the line trace graph
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

        # Create and add crosshair to the line trace graph
        pen = pg.mkPen("b", width=1)
        v_line = pg.InfiniteLine(angle=90, movable=False, pen=pen)
        h_line = pg.InfiniteLine(angle=0, movable=False, pen=pen)
        line_trace_graph.addItem(v_line)
        line_trace_graph.addItem(h_line)

        # save references to all elements in one dictionary
        self.plot_elements = {"central_item": central_item, "frame": frame_layout, "main_subplot": main_subplot,
                              "img": img, "histogram": histogram, "line_trace_graph": line_trace_graph, "iso": iso,
                              "isoLine": isoLine, "extra_axis": extra_axis, "extra_view_box": extra_view_box,
                              "v_line": v_line, "h_line": h_line, "line_trace_data": None, "color_bar": color_bar}

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

        print("Initializing toolbar . . .")
        # Create a toolbar
        self.tools = self.addToolBar("Tools")
        # Connect all actions to a "perform action" method. Perform action takes the name of the action and finds the
        # method that corresponds to that name. This is way for each action in the toolbar there needs to be a method
        # that has a name: actionName_action where actionName is the name of the action in the toolbar.
        self.tools.actionTriggered[QAction].connect(self.perform_action)

        # add a dropdown menu which allows a user to select the matrix to display (some measurements measure more then
        # 1 parameter
        self.matrix_selection_combobox = QComboBox()
        # fill the dropdown with matrices
        for index, matrix in enumerate(self.plt_data):
            display_member = "matrix{}".format(index)
            value_member = matrix
            self.matrix_selection_combobox.addItem(display_member, value_member)
        # Create an option that displays all matrices at the sime time
        display_member = "Side-by-side"
        value_member = None
        self.matrix_selection_combobox.addItem(display_member, value_member)
        self.matrix_selection_combobox.currentIndexChanged.connect(lambda: self.change_active_set(
            index=self.matrix_selection_combobox.currentIndex()))
        self.tools.addWidget(self.matrix_selection_combobox)

        # Adds a line to the matrix. The endpoints of this line are movable. The line_trace_graph shows data below this
        # line
        self.line_trace_btn = QAction(QIcon("img/lineGraph"), "Line_Trace", self)
        self.line_trace_btn.setToolTip("Add an adjustable line to the main graph. Data 'below' the line is displayed\n"
                                       "in the line trace graph")
        # Make the line trace action be toggleable (ON/OFF)
        self.line_trace_btn.setCheckable(True)
        self.tools.addAction(self.line_trace_btn)

        # Add actions that allow user to derivate the data along x or y axis (toggleable)
        self.der_x = QAction(QIcon("img/xDer.png"), "xDerivative", self)
        self.der_x.setToolTip("Calculate and display x derivative of the displayed data")
        self.der_x.setCheckable(True)
        self.tools.addAction(self.der_x)
        self.der_y = QAction(QIcon("img/yDer.png"), "yDerivative", self)
        self.der_y.setToolTip("Calculate and display y derivative of the displayed data")
        self.der_y.setCheckable(True)
        self.tools.addAction(self.der_y)

        # Add a dropdown that allows a user to select different kinds of data smoothening. Depending on the selected
        # option, changinh the spin boxes applies a different kind of smoothening to the active data set.
        self.smoothing_selection_combobox = QComboBox()
        for smoothing_type in ["Naive", "Gaussian"]:
            self.smoothing_selection_combobox.addItem(smoothing_type)
        self.smoothing_selection_combobox.currentIndexChanged.connect(self.smoothing_action)
        self.tools.addWidget(self.smoothing_selection_combobox)

        # Sping boxes for controling the smoothening, one for each axis. Increasing the number in the spin box increases
        # the number of neighbouring points that are taken into account when smoothening data.
        self.smoothen_x = QSpinBox()
        self.smoothen_x.valueChanged.connect(self.smoothing_action)
        self.tools.addWidget(self.smoothen_x)
        self.smoothen_y = QSpinBox()
        self.smoothen_y.valueChanged.connect(self.smoothing_action)
        self.tools.addWidget(self.smoothen_y)

        # ###############################
        # #### Matrix manipulations #####
        # ###############################

        # Add another part of the toolbar. This toolbar contains actions that create new data/files from the existing
        # data set
        self.matrix_manipulation_toolbar = QToolBar("Matrix manipulation")
        self.matrix_manipulation_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(self.matrix_manipulation_toolbar)

        # Add an action that when clicked creates a mitrix file of currently displayed data set
        self.create_matrix_file_btn = QAction(QIcon("img/matrix-512.png"), "Matrix", self)
        self.create_matrix_file_btn.setToolTip("Create a raw matrix file from currently displayed data set")
        self.matrix_manipulation_toolbar.addAction(self.create_matrix_file_btn)

        # Add an action that when clicked prompts a user to input some data, and then uses that data to apply a data
        # correction to the displayed data set
        self.data_correction_action = QAction(QIcon("img/line-chart.png"), "Correct_data", self)
        self.data_correction_action.setToolTip("Get Y(real) values calculated by formula: Y(real) = Y - (I * R)\n"
                                               "R is user input.")
        self.matrix_manipulation_toolbar.addAction(self.data_correction_action)

        # Add an action that when clicked prompts a user to input some data, and then uses that data to apply a data
        # correction to the displayed data set (dIdV)
        self.gm_didv = QAction(QIcon("img/dIdV.png"), "gm_didv_correction", self)
        self.gm_didv.setToolTip("Get dV(real) values calculated by formula: dV(real) = dV - (dI * R)\n"
                                "dV, R are user input")
        self.matrix_manipulation_toolbar.addAction(self.gm_didv)

        self.horizontal_offset = QAction(QIcon("img/horizontal_offset.png"), "Horizontal_offset", self)
        self.horizontal_offset.setToolTip("Apply horizontal offset to your data set")
        self.matrix_manipulation_toolbar.addAction(self.horizontal_offset)

        self.vertical_offset = QAction(QIcon("img/vertical_offset"), "Vertical_offset", self)
        self.vertical_offset.setToolTip("Apply vertical offset to your data set")
        self.matrix_manipulation_toolbar.addAction(self.vertical_offset)

        # ###############################
        # #### Window manipulations #####
        # ###############################

        # Additional toolbar that modifies the look of the window (increase/decrease font size, change axis text, ...)
        self.window_toolbar = QToolBar("Window toolbar")
        self.window_toolbar.actionTriggered[QAction].connect(self.perform_action)
        self.addToolBar(self.window_toolbar)

        # An action that allows user to modify fonts
        self.customize_font_btn = QAction(QIcon("img/editFontIcon.png"), "Font", self)
        self.customize_font_btn.setToolTip("Open a widget that allows user to customise font and axis values")
        self.window_toolbar.addAction(self.customize_font_btn)

        # An action that opens a 2D window and displays the data currenttly selected by the line_trace_ROI
        self.open_2D = QAction(QIcon("img/2d_icon.png"), "Show_2d", self)
        self.open_2D.setToolTip("Open a selected line trace in new window that allows manipulation and transformations")
        self.window_toolbar.addAction(self.open_2D)

        # Allow a user to zoom in to a certain part of the matrix
        self.zoom_action_btn = QAction(QIcon("img/zoomin_icon.png"), "Zoom", self)
        self.zoom_action_btn.setToolTip("Select area of graph to zoom into")
        self.window_toolbar.addAction(self.zoom_action_btn)

        # Switch between histogram look up table and color bar
        self.toggle_color_bar_btn = QAction(QIcon("img/palette_icon.png"), "Toggle_color_bar", self)
        self.toggle_color_bar_btn.setToolTip("Switch between histogram and color bar")
        self.toggle_color_bar_btn.setCheckable(True)
        self.window_toolbar.addAction(self.toggle_color_bar_btn)

        # Action that closes the current window
        self.exit_action_btn = QAction(QIcon("img/closeIcon.png"), "Exit", self)
        self.exit_action_btn.setToolTip("Close this heatmap window")
        self.window_toolbar.addAction(self.exit_action_btn)

        # self.init_line_trace_toolbar()

    def init_line_trace_toolbar(self):
        """
        TODO: Maybe finish this ?

        This should instantiate an additional toolbar which will allow user to select the matrices displayed when
        side by side mode is turned on.

        :return:
        """
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
                    img.translate(self.data_buffer.get_x_axis_values()[0], self.data_buffer.get_y_axis_values()[0][0])
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
        Method that hides/displays additional menus for controlling what is displayed in the line trace graph

        :return: NoneType
        """
        if self.modes["Side-by-side"] and self.modes["ROI"]:
            self.line_trace_toolbar.show()
        else:
            self.line_trace_toolbar.hide()

    def toggle_display(self, matrix, action):
        """
        TODO: Implement the feature, and then write documentation
        :param matrix:
        :param action:
        :return:
        """
        if action.isChecked():
            self.side_by_side_plots[matrix]["plot"].show()
            self.side_by_side_plots[matrix]["histogram"].show()
        else:
            self.side_by_side_plots[matrix]["plot"].hide()
            self.side_by_side_plots[matrix]["histogram"].hide()

        return

    def calculate_crosshair_position(self, mouse_point):
        """
        Manipulating crosshair is only posible on the x axis, the crosshair y axis gets updated automatically, and the
        calculation of the value where the horizontal line will be placed is done in this method.

        :param mouse_point: position of the mouse pointer
        :return: x, y positions where vertical and horizontal lines should be placed.
        """
        if self.plot_elements["line_trace_data"] is not None:
            x = mouse_point.x()

            num_of_point = len(self.plot_elements["line_trace_data"])
            point1 = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
            _, scene_coords = point1
            start_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
            point2 = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
            _, scene_coords = point2
            end_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
            if (180 - abs(self.line_segment_roi["ROI"].get_angle_from_points())) < 0.0000001:
                start, end = start_coords.x(), end_coords.x()
            elif abs(self.line_segment_roi["ROI"].get_angle_from_points()) < 0.0000001:
                start, end = start_coords.x(), end_coords.x()
            elif abs(90 - abs(self.line_segment_roi["ROI"].get_angle_from_points())) < 0.0000001:
                start, end = start_coords.y(), end_coords.y()
            else:
                start, end = start_coords.y(), end_coords.y()

            step = (end - start) / (num_of_point - 1)

            xp = np.arange(start, end + step, step)
            fp = self.plot_elements["line_trace_data"]
            y = np.interp(x, xp, fp)

            return x, y

    def change_crosshair_position(self, x, y):
        """
        This method updates the position of the crosshair by moving the vertical and horizontal line to the positions
        passed to the method as parameters.

        :param x: value to which the vertical line will be set to
        :param y: value to which the horizontal line will be set to
        :return: NoneType
        """
        self.plot_elements["v_line"].setPos(x)
        self.plot_elements["h_line"].setPos(y)

        return

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

        if self.line_trace_btn.isChecked():
            self.plot_elements["line_trace_graph"].show()
        else:
            self.plot_elements["line_trace_graph"].hide()

        if self.modes["ROI"] == False:
            self.modes["ROI"] = True

            if self.line_segment_roi["ROI"] is None:
                # ROI instantiation
                x0 = min(self.data_buffer.get_x_axis_values())
                y0 = min(self.data_buffer.get_y_axis_values()[0])

                x1 = min(self.data_buffer.get_x_axis_values())
                y1 = max(self.data_buffer.get_y_axis_values()[0])

                line_segmet_roi = LineROI(positions=([x0, y0], [x1, y1]),
                                          pos=(0, 0),
                                          pen=(5, 9),
                                          edges=[self.data_buffer.get_x_axis_values()[0],
                                                 self.data_buffer.get_x_axis_values()[-1],
                                                 self.data_buffer.get_y_axis_values()[0][0],
                                                 self.data_buffer.get_y_axis_values()[0][-1]])
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
        self.eaw = EditAxisWidget.Edit3DAxisWidget(self)
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
        Creates the matrix file version of this data in the same folder where the original file is located.

        :return: NoneType
        """

        def save_matrix(data):
            user_input_name = data
            new_file_location = get_location_path(location) + "\\" + user_input_name + "_generated_correction"
            file = open(new_file_location, "w")
            raw_data = np.transpose(self.displayed_data_set)
            np.savetxt(file, raw_data, delimiter="\t")
            file.close()

        location = self.data_buffer.location
        name = get_location_basename(location)
        index = self.active_data_index
        if index > self.data_buffer.number_of_measured_parameters:
            self.select_file_name = InputDataWidget.InputData("Please select the name of the output file.", default_value=name)
            self.select_file_name.submitted.connect(save_matrix)
        elif self.modes["Side-by-side"]:
            show_error_message("NO, U CANT DO THAT !",
                               "Creating a matrix file for side by side view is not possible.")
        else:
            self.data_buffer.create_matrix_file(index)

    def show_2d_action(self):
        """
        Opens a line trace graph window for a line trace selected by line_trace_roi. Get the positions of the end points
        and then create dummy 2d buffer that only has members and methods needed to easily display 2D graph in a line
        trace window.

        :return:
        """
        print("Preparing data for line trace window . . .")
        data = self.displayed_data_set
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        first_point = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = first_point
        start = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        start_x = start.y()
        last_point = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
        _, scene_coords = last_point
        end = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        end_x = end.y()

        first_point = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = first_point
        start = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        start_y = start.x()
        last_point = self.line_segment_roi["ROI"].getSceneHandlePositions(1)
        _, scene_coords = last_point
        end = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        end_y = end.x()

        x = np.linspace(start_x, end_x, len(selected))
        x2 = np.linspace(start_y, end_y, len(selected))

        label_x = self.data_buffer.axis_values["y"][0]
        label_y = self.data_buffer.axis_values["z"][self.active_data_index]
        label_extra = self.data_buffer.axis_values["x"]

        x_dict = {"values": x, "axis": label_x}
        y_dict = {"values": [selected], "axis": label_y}
        extra_axis_dict = {"values": x2, "axis": label_extra}

        title = self.data_buffer.name
        dummy = DummyBuffer(title + "Line Trace", x_dict, y_dict, extra_axis=extra_axis_dict)
        self.line_trace_window = LineTrace(dummy)

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
        self.input = InputDataWidget.InputData("Please input the resistance something something to correct your data",
                                               1, numeric=[True], placeholders=["Resistance"])
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
                        temp = shift(np.transpose(data), shift_value, 0)
                        np.add(horizontal_shift, temp, horizontal_shift)
                    else:
                        temp = shift(data, shift_value, 0)
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
        return

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
        self.didv_input = DiDvCorrectionInputWidget.DiDvCorrectionInputWidget(parent=self)
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
        self.input = InputDataWidget.InputData("Please input ranges of values to display", 4,
                                               numeric=[True, True, True, True],
                                               placeholders=["Start X value [Currently: {}]".format(current_x_min),
                                                             "End X value [Currently {}]".format(current_x_max),
                                                             "Start Y value [Currently {}]".format(current_y_min),
                                                             "End Y value [Currently {}]".format(current_y_max)])
        self.input.submitted.connect(self.zoom_to_range)

    def toggle_color_bar_action(self):
        """
        Method that switches between showing histogram or matlab like color bar. If the button is "ON" histogram is
        hidden and color bar is displayed. If the button is "OFF" (default), histogram is displayed and color bar is
        hidden.

        :return: NoneType
        """
        if self.toggle_color_bar_btn.isChecked():
            self.plot_elements["histogram"].hide()
            self.plot_elements["histogram"].setFixedWidth(0)
            self.plot_elements["color_bar"].show()
        else:
            self.plot_elements["histogram"].show()
            self.plot_elements["histogram"].setFixedWidth(self.histogram_width)
            self.plot_elements["color_bar"].hide()
        return

    def horizontal_offset_action(self):
        """
        Method that opens input window (allows user to input some data) and after submitting the data shifts the whole
        data set horizontally by the amount specified by the user.

        :return: NoneType
        """
        self.horizontal_offset_input = InputDataWidget.InputData("Apply horizontal offset", 1, ["0"], [True],
                                                                 ["Horizontal offset"])
        self.horizontal_offset_input.submitted.connect(self.x_axis_offset)
        return

    def vertical_offset_action(self):
        """
        Method that opens input window (allows user to input some data) and after submitting the data shifts the whole
        data set vertically by the amount specified by the user.

        :return: NoneType
        """
        self.vertical_offset_input = InputDataWidget.InputData("Apply vertical offset", 1, ["0"], [True],
                                                               ["Vertical offset"])
        self.vertical_offset_input.submitted.connect(self.y_axis_offset)
        return

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
        return

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
            if self.plot_elements["line_trace_data"] is not None:
                if self.modes["ROI"]:
                    mouse_point = self.plot_elements["line_trace_graph"].vb.mapSceneToView(pos)
                    x, y = self.calculate_crosshair_position(mouse_point)
                    self.change_crosshair_position(x, y)
                    string = "[Position: {}, {}]".format(round(x, 9), round(y, 9))
                    self.statusBar().showMessage(string)

    def update_line_trace_plot(self):
        """
        Each time a line trace is moved this method is called to update the line trace graph element of the Heatmap
        widget.

        :return: NoneType
        """

        self.plot_elements["line_trace_graph"].clear()
        self.update_point_label_positions()

        data = self.displayed_data_set
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        line_trace_graph = self.plot_elements["line_trace_graph"]
        new_plot = line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True)
        self.plot_elements["line_trace_data"] = selected
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
        line_trace_graph.addItem(self.plot_elements["v_line"], ignoreBounds=True)
        line_trace_graph.addItem(self.plot_elements["h_line"], ignoreBounds=True)
        self.change_crosshair_position(start_coords.x(), start_coords.y())

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
        This method gets triggered when a key press event happens. It is used to move the line trace ROI when one of the
        arrow keys gets pressed.

        :param event: event that triggered this method
        :return: NoneType
        """

        if self.modes["ROI"]:
            if event.key() in [Qt.Key_Up, Qt.Key_Down]:
                distance = abs(self.data_buffer.get_y_axis_values()[0][1] - self.data_buffer.get_y_axis_values()[0][0])
            elif event.key() in [Qt.Key_Right, Qt.Key_Left]:
                distance = abs(self.data_buffer.get_x_axis_values()[1] - self.data_buffer.get_x_axis_values()[0])
            else:
                return
            self.line_segment_roi["ROI"].arrow_move(event.key(), distance)
            point1 = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
            _, scene_coords = point1
            start_coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
            self.change_crosshair_position(start_coords.x(), start_coords.y())
        return

    def zoom_to_range(self, data):
        """
        Method that allows user to zoom to the area of the matrix specified by the lower and upper values of x and y.

        :param data: list: [xMin, xMax, yMin, yMax]
        :return: NoneType
        """

        x_min, x_max, y_min, y_max = float(data[0]), float(data[1]), float(data[2]), float(data[3])
        self.plot_elements["main_subplot"].vb.setXRange(x_min, x_max, padding=0)
        self.plot_elements["main_subplot"].vb.setYRange(y_min, y_max, padding=0)
        return

    def mark_current_line_trace_point(self):
        """
        TODO: Remember what the hell was this supposed to be
        I think the idea was to put a point on a current location of the crosshair
        :return:
        """
        pass
        # print(self.plot_elements["v_line"].value(), self.plot_elements["h_line"].value())

    def x_axis_offset(self, data):
        """
        Helper method. Calls the method that applies offset. Passes parameters that specify axis and offset amount.

        :param data: array passed trough the signal. Contains user input values.
        :return: NoneType
        """
        value = float(data[0])
        self.apply_axis_offset("x", value)
        return

    def y_axis_offset(self, data):
        """
        Helper method. Calls the method that applies offset. Passes parameters that specify axis and offset amount.


        :param data: array passed trough the signal. Contains user input values.
        :return: NoneType
        """
        value = float(data[0])
        self.apply_axis_offset("y", value)
        return

    def apply_axis_offset(self, axis, value):
        """
        Method that applies offset to data set opened in this instance of Heatmap window.

        :param axis: string: "x" or "y" to signal which axis to apply offset to
        :param value: float: the value of offset (how much will data be shifted)
        :return: NoneType
        """
        self.data_buffer.data[axis] = self.data_buffer.data[axis] + value
        self.plot_elements["img"].resetTransform()
        self.plot_elements["img"].translate(self.data_buffer.get_x_axis_values()[0],
                                            self.data_buffer.get_y_axis_values()[0][0])
        (x_scale, y_scale) = self.data_buffer.get_scale()
        self.plot_elements["img"].scale(x_scale, y_scale)
        x_min = min(self.data_buffer.get_x_axis_values())
        x_max = max(self.data_buffer.get_x_axis_values())
        y_min = min(self.data_buffer.get_y_axis_values())
        y_max = max(self.data_buffer.get_y_axis_values())
        self.plot_elements["main_subplot"].setLimits(xMin=x_min, xMax=x_max, yMin=y_min, yMax=y_max)
        return


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

    data = QcodesData("C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_Daniel_2d1\\IVVI_PLLT_set_IVVI_Ohmic_set.dat")
    data.prepare_data()

    ex = Heatmap(data=data)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
