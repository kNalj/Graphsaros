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
        data = np.loadtxt(self.location, dtype=float)
        x, y = np.shape(data)
        self.data["matrix"] = data
        return [x, y]

    def prepare_data(self):
        pass

    def get_axis_data(self):
        self.axis_window = AxisWindow(self)
        self.axis_window.submitted.connect(self.read_axis_data_from_widget)
        self.axis_window.show()

    def read_axis_data_from_widget(self, data_dict):
        x_start = float(data_dict["x"]["start"])
        x_end = float(data_dict["x"]["end"])
        step = (x_end - x_start) / (self.matrix_dimensions[0] - 1)
        x_axis_values = [x for x in np.arange(x_start, x_end, step=step)]
        self.data["x"] = x_axis_values
        x_axis_data = {"name": data_dict["x"]["name"], "unit": data_dict["x"]["unit"]}

        y_start = float(data_dict["y"]["start"])
        y_end = float(data_dict["y"]["end"])
        step = (x_end - x_start) / (self.matrix_dimensions[0] - 1)
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
