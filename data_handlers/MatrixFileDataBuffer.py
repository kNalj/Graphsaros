import numpy as np
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal

from data_handlers.DataBuffer import DataBuffer, AxisWindow


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MatrixData(DataBuffer):

    def __init__(self, location):
        """
        Inherits: DataBuffer()

        Specific data buffer for matrix file type of data (only contains matrix with the results of the measurement)

        :param location: location of the file on hard disk
        """
        super().__init__(location)

        # Contains values of x (np.array) and y (np.array) (and z [np.ndarray()) axis.
        self.data = {}

        # contains data about units, name of the parameter, ...
        self.axis_values = {}

        # member variable with dimensions of the data (either list with length of 1 [for 2D measurement] or 2 [fpr 3D
        # measurement])
        self.matrix_dimensions = self.calculate_matrix_dimensions()

        self.get_axis_data()

    def calculate_matrix_dimensions(self):
        """
        Method that loads matrix and returns its dimensions (reason why id does both of this is because it is faster to
        go through the file just once rather then going through the file again at a later stage to get the matrix

        :return: list: [len_of_x, len_of_y]
        """
        self.data["matrix"] = []
        data = np.loadtxt(self.location, dtype=float)
        transposed = np.transpose(data)
        self.textual = np.array2string(transposed)
        self.data["matrix"].append(transposed)
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


def main():
    app = QApplication(sys.argv)
    # 3D measurement
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"

    data = MatrixData(file_location)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
