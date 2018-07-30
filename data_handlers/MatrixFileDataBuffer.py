import numpy as np


from data_handlers.DataBuffer import DataBuffer, AxisWindow


class MatrixData(DataBuffer):

    def __init__(self, location):
        super().__init__(location)

        self.matrix_dimensions = self.calculate_matrix_dimensions()

    def calculate_matrix_dimensions(self):
        data = np.loadtxt(self.location, dtype=float).transpose()
        print(data)
        print(np.shape(data))
        return np.shape(data)

    def prepare_data(self):
        pass

    def get_axis_data(self):
        self.input_axis_values()

    def input_axis_values(self):
        """
        Open a PyQt window to input axis values (start, end, steps, name, unit)

        :return: i dont know yet, but ill figure it out
        """
        self.axis_window = AxisWindow(self)
        self.axis_window.submitted.connect(self.read_axis_data_from_widget)
        self.axis_window.show()

    def read_axis_data_from_widget(self, data_dict):
        pass



def main():
    # 3D measurement
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"

    data = MatrixData(file_location)
    data.get_matrix_dimensions()


if __name__ == '__main__':
    main()
