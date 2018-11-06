import numpy as np
import pandas as pd

from data_handlers.DataBuffer import DataBuffer
from helpers import show_error_message


class QtLabData(DataBuffer):

    def __init__(self, location):
        """
        A class for representing QtLab data. Holds all data needed to plot a graph in pyqtgraph

        :param location: string: absolute path to the file which is being parsed by this DataBuffer
        """
        self.legend = {0: "x", 1: "y", 2: "z"}
        super().__init__(location)

        self.data = {}
        self.matrix_dimensions = self.calculate_matrix_dimensions()
        if self.matrix_dimensions:
            self.prepare_data()
            self.axis_values = self.get_axis_data()

    def calculate_matrix_dimensions(self):
        """
        Takes first two columns of QtLab file (x and y) and looks for unique values.

        :return: list: [len(x_axis_data), len(y_axis_data)]
        """
        axis_data = np.loadtxt(self.location, dtype=float)
        if len(axis_data) < 2:
            show_error_message("Warning", "Seems like data for file {} is incomplete".format(self.location))
        else:
            if axis_data[0][1] == axis_data[1][1]:
                y_axis = pd.unique([value[0] for value in axis_data])
                x_axis = pd.unique([value[1] for value in axis_data])
                self.legend[0] = "y"
                self.legend[1] = "x"
            elif axis_data[0][0] == axis_data[1][0]:
                x_axis = pd.unique([value[0] for value in axis_data])
                y_axis = pd.unique([value[1] for value in axis_data])
            else:
                x_axis = [value[0] for value in axis_data]
                y_axis = [value[1] for value in axis_data]
                self.data["x"] = x_axis
                self.data["y"] = y_axis
                return [len(x_axis)]
            self.data["x"] = x_axis
            self.data["y"] = y_axis
            return [len(x_axis), len(y_axis)]

    def prepare_data(self):
        """
        Method that creates np.array filled with data from file specified by location when instantiating this class.
        Data is third column of numbers in that file.

        :return: np.array: matrix
        """

        if self.get_number_of_dimension() == 2:
            return
        else:
            matrix_data = np.zeros((self.matrix_dimensions[0], self.matrix_dimensions[1]))
            matrices = []
            z = np.loadtxt(self.location, dtype=float)
            self.number_of_set_parameters = self.get_number_of_dimension() - 1
            self.number_of_measured_parameters = np.shape(z)[1] - self.number_of_set_parameters
            num_of_elements = np.shape(z)[0]
            for matrix in range(self.number_of_set_parameters,
                                self.number_of_set_parameters + self.number_of_measured_parameters):
                for i in range(self.matrix_dimensions[0]):
                    for j in range(self.matrix_dimensions[1]):
                        if i * self.matrix_dimensions[1] + j < num_of_elements:
                            matrix_data[i][j] = z[(i * self.matrix_dimensions[1]) + j][matrix]
                matrices.append(matrix_data)

        self.data["matrix"] = matrices

    def get_axis_data(self):
        """
        Returns names and units that should be used on graph when plotting this DataBuffer

        :return: dict: {x: {name: "...", unit: "..."}, y: {}, z: {}}
        """
        data_dict = {"x": {"name": "", "unit": ""}, "y": {"name": "", "unit": ""}, "z": {"name": "", "unit": ""}}
        index = -1
        with open(self.location) as file:
            for i in file:
                valid_unit = False
                if "Column" in i:
                    index += 1
                elif i.lstrip("\t#").startswith("name:"):
                    data = i.strip("#\t\n").lstrip("name: ")
                    unit = data.split(" ")[-1].strip("()[]{}")
                    for j in ["", "p", "n", "µ", "m", "k", "M", "G"]:
                        if valid_unit:
                            break
                        for k in ["A", "V", "Ω", "Ohm", "W", "var", "VA", "F", "H", "S", "C", "Ah", "J", "Wh", "eV",
                                  "T", "G", "Wb", "Hz", "dB", "s"]:
                            if unit == j+k:
                                valid_unit = True
                                break

                    name = data
                    data_dict[self.legend[index]]["name"] = name
                    if valid_unit:
                        data_dict[self.legend[index]]["unit"] = unit
                else:
                    if i[0].isdigit() or (i.startswith("-") and i[1].isdigit()):
                        break

        return data_dict


def main():
    # 2D measurement
    # file_location = "K:\\Measurement\\Daniel\\2018-02-16_shiftedSample\\20180215\\173132_ Olivia_bias24-5_gain1e6_leakage22\\173132_ Olivia_bias24-5_gain1e6_leakage22.dat"

    # 3D measurement
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat"

    data = QtLabData(file_location)


if __name__ == '__main__':
    main()
