from helpers import show_error_message
from PyQt5.QtWidgets import QWidget, QGridLayout, QApplication, QLineEdit, QLabel, QDesktopWidget, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

import sys
from helpers import is_numeric


class DataBuffer:

    def __init__(self, location):

        # location is absolute path to a location of the file on the disk
        self.location = location

        # data is a dictionary containing:
        #   For 3D measurement: matrix, x, y
        #       matrix: np.array containing z axis data
        #       x: list of x axis values
        #       y: list of y axis values
        #   For 2D measurement: x, y
        #       x and y same as in 3D
        self.data = None

        # list of values containing number of steps for x and y dimensions
        self.matrix_dimensions = None

    def get_matrix_dimensions(self):
        return self.matrix_dimensions

    def get_number_of_dimension(self):
        return len(self.matrix_dimensions) + 1

    def calculate_matrix_dimensions(self):
        raise NotImplementedError

    def prepare_data(self):
        raise NotImplementedError

    def get_axis_data(self):
        raise NotImplementedError

    def get_scale(self):
        return (self.data["x"][-1] - self.data["x"][0]) / (len(self.data["x"]) - 1), \
               (self.data["y"][-1] - self.data["y"][0]) / (len(self.data["y"]) - 1)

    def get_matrix(self):
        return self.data["matrix"]

    def get_x_axis_values(self):
        return self.data["x"]

    def get_y_axis_values(self):
        return self.data["y"]

    def get_location(self):
        return self.location


class AxisWindow(QWidget):

    submitted = pyqtSignal(object)

    def __init__(self, buffer):
        super(AxisWindow, self).__init__()

        self.buffer = buffer

        self.controls = {}

        self.init_ui()
        self.show()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Input axis data")
        self.setWindowIcon(QIcon("../img/axis.png"))

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

        z_label = QLabel("Z axis data")
        z_name = QLineEdit("")
        z_name.setPlaceholderText("name")
        z_unit = QLineEdit("")
        z_unit.setPlaceholderText("unit")
        z_axis_controls = {"name": z_name, "unit": z_unit}
        self.controls["z"] = z_axis_controls

        self.submit_button = QPushButton("OK")
        self.submit_button.clicked.connect(self.submit)


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
        layout.addWidget(self.submit_button, 6, 3, 1, 1)

        self.setLayout(layout)

    def submit(self):

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

    def validate_input(self):
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
