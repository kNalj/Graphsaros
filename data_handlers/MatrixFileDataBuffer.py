import numpy as np


from data_handlers.DataBuffer import DataBuffer, AxisWindow


class MatrixData(DataBuffer):

    def __init__(self, location):
        super().__init__(location)

    def calculate_matrix_dimensions(self):
        pass

    def prepare_data(self):
        pass

    def get_axis_data(self):
        data_dict = self.input_axis_values()
        return data_dict


def main():
    pass


if __name__ == '__main__':
    main()
