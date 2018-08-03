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


def main():
    app = QApplication(sys.argv)
    # 3D measurement
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"

    data = MatrixData(file_location)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
