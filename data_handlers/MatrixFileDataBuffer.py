import numpy as np
import sys
from helpers import frange
from PyQt5.QtWidgets import QApplication


from data_handlers.DataBuffer import DataBuffer, AxisWindow


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MatrixData(DataBuffer):

    def __init__(self, location):
        super().__init__(location)

        self.data = {}
        self.axis_values = {}
        self.matrix_dimensions = self.calculate_matrix_dimensions()
        self.get_axis_data()

    def calculate_matrix_dimensions(self):
        """
        Method that loads matrix and returns its dimensions (reason why id does both of this is because it is faster to
        go through the file just once rather then going through the file again at a later stage to get the matrix

        :return: list: [len_of_x, len_of_y]
        """
        data = np.loadtxt(self.location, dtype=float)
        self.data["matrix"] = np.transpose(data)
        y, x = np.shape(data)

        return [x, y]

    def prepare_data(self):
        """
        Not needed because the matrix is already parsed in the calculate_matrix_dimensions

        :return:
        """
        pass

    def get_axis_data(self):
        """
        Creates a Qt window that has fields for inputing axis data (start, end, name, unit)

        :return: dict: {x: {start: "...", end: "...", name: "...", unit: "..."}, y: {}, z: {}}
        """
        self.axis_window = AxisWindow(self)
        self.axis_window.submitted.connect(self.read_axis_data_from_widget)
        self.axis_window.show()

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
        x_axis_values = [x for x in np.arange(x_start, x_end, step=step)]
        self.data["x"] = x_axis_values
        x_axis_data = {"name": data_dict["x"]["name"], "unit": data_dict["x"]["unit"]}

        y_start = float(data_dict["y"]["start"])
        y_end = float(data_dict["y"]["end"])
        step = (y_end - y_start) / (self.matrix_dimensions[1] - 1)
        y_axis_values = [y for y in np.arange(y_start, y_end, step=step)]
        self.data["y"] = y_axis_values
        y_axis_data = {"name": data_dict["y"]["name"], "unit": data_dict["y"]["unit"]}

        z_axis_data = {"name": data_dict["z"]["name"], "unit": data_dict["z"]["unit"]}

        self.axis_values = {"x": x_axis_data, "y": y_axis_data, "z": z_axis_data}


def main():
    app = QApplication(sys.argv)
    # 3D measurement
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"

    data = MatrixData(file_location)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
