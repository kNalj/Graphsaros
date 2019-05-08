from helpers import show_error_message
from PyQt5.QtWidgets import QWidget, QGridLayout, QApplication, QLineEdit, QLabel, QDesktopWidget, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QIcon

import os
import sys
import subprocess
import numpy as np
from helpers import is_numeric


class DataBuffer(QObject):

    ready = pyqtSignal()
    progress = pyqtSignal(object)

    def __init__(self, location):
        super().__init__()

        # location is absolute path to a location of the file on the disk
        self.location = location

        self.name = os.path.basename(self.get_location())

        # data is a dictionary containing:
        #   For 3D measurement: matrix, x, y
        #       matrix: np.array containing z axis data
        #       x: list of x axis values
        #       y: list of y axis values
        #   For 2D measurement: x, y
        #       x and y same as in 3D
        self.data = None

        # Not all measurements have the same numbers of parameters that are being set. We might have a measurement that
        # sets two different parameters and measures one, also a measurement that is a loop in a loop which also sets
        # two parameters and measures one but its not the same thing. Also there might be more then one measured
        # parameter
        self.number_of_set_parameters = None

        # Same as number of set parameters. Its usefull to have this number available at all times. its usefull to some
        # other windows when displaying data to know how many columns are set parameters, and how many columns are data
        # to be displayed. (Example: Loop in a loop measurement has 2 parameters that are being measured. In this case
        # we want to give user to option to chose which measured parameter is displayed as a graph)
        self.number_of_measured_parameters = None

        # Textual representetion of data set. Enables wuick overview of the data in the main window
        self.textual = None

        self.string_type = ""

        # list of values containing number of steps for x and y dimensions
        self.matrix_dimensions = None

    def get_matrix_dimensions(self):
        """
        Returns dimensions of the data set represented by this object. Returns number of points on each axis

        :return: list: [length of x, length of y]
        """
        return self.matrix_dimensions

    def get_number_of_dimension(self):
        """
        Method that returns number of dimensions of this measurement, for 3D measurement its 3, for 2D its 2 ... WOW

        :return: int: number of dimensions
        """
        return len(self.matrix_dimensions) + 1

    def calculate_matrix_dimensions(self):
        """
        To be implemented in child classes. This method is different for every type of file that can be opened, therefor
        the method should be implemented in the child class.

        Usually relies on np.loadtxt and np.unique to get x and y dimensions

        :return: list: [len_of_x, len_of_y]
        """
        raise NotImplementedError

    def prepare_data(self):
        """
        Should be implemented in child classes. Creates a matrix with calculate_matrix_dimensions shape and fills it
        with data by walking through a file.

        :return:
        """
        raise NotImplementedError

    def get_axis_data(self):
        """
        Gets and saves data points of x and y axis. Should return name and unit for the axis so that it can be easily
        reached when making a graph with this data buffer.

        :return: dict: {x: {name: "example name", unit: "example unit"}, y: {name: "...", unit: "..."}, z: {}}
        """
        raise NotImplementedError

    def get_scale(self):
        """
        Method that calculates distance between points of the matrix in x and y direction. Pyqtgraph draws each point
        in distance of 1 from previous, to have correct data u need to scale your complete data and for that u need to
        know the thing that is calculated here.

        :return: tuple: (scale_x, scale_y)
        """
        x_divider = len(self.data["x"])
        if x_divider == 0:
            x_divider = 1
        y_divider = len(self.data["y"])
        if y_divider == 0:
            y_divider = 1
        return (self.data["x"][-1] - self.data["x"][0]) / x_divider, \
               (self.data["y"][-1] - self.data["y"][0]) / y_divider

    def get_matrix(self, index=None):
        """
        Returns the specified matrix of this data buffer

        :param index: specify index of the matrix to be returned. (Single data buffer may have multiple matrices as a
                    result of measuring more then one parameter). If index is set to None return a list of all matrices
                    that this data set contains.

        :return: np.array: matrix (for 3D)
        """
        if index is not None:
            return self.data["matrix"][index]
        else:
            return self.data["matrix"]

    def get_x_axis_values(self):
        """
        Method that returns points along the x axis where data points should be drawn

        :return: list: [points on x axis]
        """
        return self.data["x"]

    def get_y_axis_values(self):
        """
        Method that returns points along the y axis where data points should be drawn

        :return: list: [points on y axis]
        """
        return self.data["y"]

    def get_location(self):
        """
        Method that returns location of the file from which this data buffer was created

        :return: string: location of the original file
        """
        return self.location

    def read_axis_data_from_widget(self, data_dict):
        """
        Method that creates arrays of data (measure poitns) for x and y axis using user input data.

        This method is a slot and is being called when this class receives a signal from AxisWindow widget that the data
        has been submitted.

        :param data_dict: dictionary contining start, end, name, and unit for each axis
        :return: NoneType
        """
        x_start = float(data_dict["x"]["start"])
        x_end = float(data_dict["x"]["end"])
        step = (x_end - x_start) / (self.matrix_dimensions[0] - 1)
        x_axis_values = np.array([x for x in np.arange(x_start, x_end+step, step=step)])
        self.data["x"] = x_axis_values
        x_axis_data = {"name": data_dict["x"]["name"], "unit": data_dict["x"]["unit"]}

        y_start = float(data_dict["y"]["start"])
        y_end = float(data_dict["y"]["end"])
        step = (y_end - y_start) / (self.matrix_dimensions[1] - 1)
        y_axis_values = np.array([y for y in np.arange(y_start, y_end+step, step=step)])
        self.data["y"] = y_axis_values
        y_axis_data = {"name": data_dict["y"]["name"], "unit": data_dict["y"]["unit"]}

        z_axis_data = {"name": data_dict["z"]["name"], "unit": data_dict["z"]["unit"]}

        self.axis_values = {"x": x_axis_data, "y": y_axis_data, "z": {0: z_axis_data}}

        self.ready.emit()

    def is_data_ready(self):
        """
        Method that checks if all data required to plot a graph (Heatmap or LineTrace) is accessible in this buffer

        :return: boolean: True if all data required to plot a graph is ready, False if its not ready
        """
        if not self.matrix_dimensions:
            return False
        if "x" not in self.data or "y" not in self.data:
            return False
        if "x" not in self.axis_values or "y" not in self.axis_values:
            return False

        return True

    def create_matrix_file(self, index):
        """
        Create a matrix file for the specified matrix of this data set.

        :param index: Specify the zero based index of the matrix in this buffer. For measurements that measure more then
                    one parameter.

        :return: NoneType
        """
        name = self.location + "_matrix_{0}".format(index)
        file = open(name, "w")
        raw_data = np.transpose(self.get_matrix(index))
        np.savetxt(file, raw_data, delimiter="\t")
        file.close()

    def textual_data_representation(self):
        """
        Method that returns textual representation of the data from this data buffer. Text is created at the same time
        when data is being parsed from the source file of the buffer.

        :return: string: string representation of this buffers data
        """

        return self.textual


class AxisWindow(QWidget):

    # Signal that is emitted when you click OK button. It signals DataBuffers that axis data has been submitted
    submitted = pyqtSignal(object)

    def __init__(self, buffer):
        """
        Used to obtain data about x (and y) axis data values for buffers that do not have those (usually only matrix
        files)

        :param buffer: DataBuffer(): A reference to a data buffer for which the data is being edited
        """
        super(AxisWindow, self).__init__()

        # A reference to a buffer for which you are entering data
        self.buffer = buffer

        # References to all QLineEdits
        self.controls = {}

        self.init_ui()
        self.show()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Input axis data")
        self.setWindowIcon(QIcon("../img/axis.png"))

        # Set of QLineEdits for defining x axis data
        x_label = QLabel("X axis data")
        x_start = QLineEdit("")
        x_start.setPlaceholderText("start")
        x_end = QLineEdit("")
        x_end.setPlaceholderText("end")
        x_name = QLineEdit("")
        x_name.setPlaceholderText("name")
        x_unit = QLineEdit("")
        x_unit.setPlaceholderText("unit")
        x_axis_controls = {"start": x_start, "end": x_end, "name": x_name, "unit": x_unit}
        self.controls["x"] = x_axis_controls

        # Set of QLineEdits for defining y axis data
        y_label = QLabel("Y axis data")
        y_start = QLineEdit("")
        y_start.setPlaceholderText("start")
        y_end = QLineEdit("")
        y_end.setPlaceholderText("end")
        y_name = QLineEdit("")
        y_name.setPlaceholderText("name")
        y_unit = QLineEdit("")
        y_unit.setPlaceholderText("unit")
        y_axis_controls = {"start": y_start, "end": y_end, "name": y_name, "unit": y_unit}
        self.controls["y"] = y_axis_controls

        # Set of QLineEdits for defining z axis data
        z_label = QLabel("Z axis data")
        z_name = QLineEdit("")
        z_name.setPlaceholderText("name")
        z_unit = QLineEdit("")
        z_unit.setPlaceholderText("unit")
        z_axis_controls = {"name": z_name, "unit": z_unit}
        self.controls["z"] = z_axis_controls

        # Button for sending this data to data buffer
        self.submit_button = QPushButton("OK")
        self.submit_button.clicked.connect(self.submit)

        # Button to open folder browser to the location of this file
        self.what_is_this_btn = QPushButton("What is this ?")
        self.what_is_this_btn.clicked.connect(self.go_to_location)

        # add all elements to a layout
        layout = QGridLayout()
        layout.addWidget(x_label, 0, 0, 1, 4)
        layout.addWidget(x_start, 1, 0, 1, 1)
        layout.addWidget(x_end, 1, 1, 1, 1)
        layout.addWidget(x_name, 1, 2, 1, 1)
        layout.addWidget(x_unit, 1, 3, 1, 1)
        layout.addWidget(y_label, 2, 0, 1, 4)
        layout.addWidget(y_start, 3, 0, 1, 1)
        layout.addWidget(y_end, 3, 1, 1, 1)
        layout.addWidget(y_name, 3, 2, 1, 1)
        layout.addWidget(y_unit, 3, 3, 1, 1)
        layout.addWidget(z_label, 4, 0, 1, 4)
        layout.addWidget(z_name, 5, 0, 1, 2)
        layout.addWidget(z_unit, 5, 2, 1, 2)
        layout.addWidget(self.what_is_this_btn, 6, 0, 1, 1)
        layout.addWidget(self.submit_button, 6, 3, 1, 1)

        self.setLayout(layout)

    def submit(self):
        """
        Method that reads data from QLineEdits and saves it to a dictionary that is then passed to a DataBuffer object

        If the input data does not pass validation (start and end have to be castable to a number) then this method
        shows error message

        :return: dict: {x: {start: "...", end: "...", name: "...", unit: "..."}, y: {}, z: {}}
                            start: first point on specified axis
                            end: last point on specified axis
                            name: name of the parameter measured and displayed on that axis
                            unit: measurement unit in which this parameter is measured
        """

        x_axis = {"start": self.controls["x"]["start"].text(),
                  "end": self.controls["x"]["end"].text(),
                  "name": self.controls["x"]["name"].text(),
                  "unit": self.controls["x"]["unit"].text()}

        y_axis = {"start": self.controls["y"]["start"].text(),
                  "end": self.controls["y"]["end"].text(),
                  "name": self.controls["y"]["name"].text(),
                  "unit": self.controls["y"]["unit"].text()}

        z_axis = {"name": self.controls["z"]["name"].text(),
                  "unit": self.controls["z"]["unit"].text()}

        data_dict = {"x": x_axis, "y": y_axis, "z": z_axis}

        if not self.validate_input():
            self.submitted.emit(data_dict)
            self.close()
        else:
            title, msg = self.validate_input()
            show_error_message(title, msg)

    def go_to_location(self):
        """
        Method that gets the location of the DataBuffer for which the axis data is being edited and opens that location
        in folder explorer (allowing user to see the data in question)

        :return: NoneType
        """
        location = self.buffer.get_location()
        folder = os.path.dirname(location)
        # unfortunately this thing only works on windows :((((
        os.startfile(folder)

    def validate_input(self):
        """
        Validation for data that is being sent to a DataBuffer.

        Rules:
            start: has to be numeric
            end: has to be numeric

        :return: False if validation passes, string to display error message if something does not pass validation
        """
        for axis, data in self.controls.items():
            for name, control in data.items():
                if name in ["start", "end"]:
                    if is_numeric(control.text()):
                        continue
                    else:
                        return "Warning", "Value [{}] of axis [{}] is not numeric".format(name, axis)
        return False


def main():
    app = QApplication(sys.argv)
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"
    ex = DataBuffer(file_location)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
