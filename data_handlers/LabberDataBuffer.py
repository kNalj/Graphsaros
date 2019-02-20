import numpy as np
import pandas as pd
import helpers
import os
import h5py

from data_handlers.DataBuffer import DataBuffer


class LabberData(DataBuffer):

    def __init__(self, location):
        """
        Inherits: DataBuffer()

        Data buffer for labber files

        :param location: location of the file on the disk
        """
        self.legend = {1: "x", 0: "y"}
        super().__init__(location)

        self.gains = self.get_gains()

        self.matrix_dimensions = self.calculate_matrix_dimensions()

        self.axis_values = self.get_axis_data()

        self.data = {}

        self.string_type = "Labber"

    def calculate_matrix_dimensions(self):
        """
        Opens file and calculates dimensions of the data matrix. Returns array representing dimensions of the matrix.

        :return: array: [x, y]
                        x - number of points on x axis
                        y - number of points on y axis
        """

        matrix_dimensions = []
        file = h5py.File(self.location)
        channel_names = [channel[0] for channel in file["Data"]["Channel names"]]
        steping_params = file["Step config"]
        set_params = [channel[0] for channel in file["Step list"].value]
        for stepy_boye in steping_params:
            if stepy_boye in channel_names and stepy_boye in set_params:
                for item in steping_params[stepy_boye]:
                    if item == "Step items":
                        # [(1, 0, 3.05180438e-05, 0.01, 0.1, 0.055, 0.09, 0.005, 19, 0, 0.)]
                        # above comment is what this "Step items" looks like
                        # dimension of axis is third to last in the dataset displayed above
                        matrix_dimensions.append(steping_params[stepy_boye][item].value[0][-3])
        file.close()

        if not matrix_dimensions:
            # this should probably try to do a backup way of calculating dimensions, should be implemented in the
            # parrent class
            raise ValueError("File does not contain matrix dimension data (AND IT SHOULD !)")
        else:
            return matrix_dimensions

    def prepare_data(self):
        """
        TODO: Implement case where a 2d file with multiple measured parameters needs to be read.

        :return:
        """
        file = h5py.File(self.location)
        data = file["Data"]
        self.textual = np.array2string(data["Data"].value)
        self.number_of_set_parameters = 0
        self.number_of_measured_parameters = 0
        set_params = [channel[0] for channel in file["Step list"].value]
        measured_params = [channel[0] for channel in file["Log list"].value]

        for channel in data["Channel names"].value:
            if channel[0] in set_params:
                self.number_of_set_parameters += 1
            if channel[0] in measured_params:
                self.number_of_measured_parameters += 1

        if self.get_number_of_dimension() == 3:
            print("Modeling 3d data . . .")
            y_axis = pd.unique((np.array([axis_values[0] / self.gains["x"] for axis_values in data["Data"].value])).flatten("C"))
            x_axis = pd.unique((np.array([axis_values[1] / self.gains["y"] for axis_values in data["Data"].value])).flatten("C"))
            z_axis = (np.array([axis_values[1] for axis_values in data["Data"].value])).flatten("C")
        else:
            print("Modeling 2d data . . .")
            x_axis = [axis_values[0][0] for axis_values in data["Data"].value]
            y_axis = [axis_values[1][0] for axis_values in data["Data"].value]

        if self.get_number_of_dimension() == 3:
            print("Fetching matrix values . . .")
            matrices = []
            start_index = self.number_of_set_parameters
            end_index = self.number_of_set_parameters + self.number_of_measured_parameters
            x_dimension = self.matrix_dimensions[0]
            y_dimension = self.matrix_dimensions[1]
            for matrix in range(start_index, end_index):
                matrix_data = np.zeros((x_dimension, y_dimension))
                num_of_elements = np.size(matrix_data)
                for i in range(x_dimension):
                    for j in range(y_dimension):
                        if i * y_dimension + j < num_of_elements:
                            if len(z_axis) > i * y_dimension + j:
                                matrix_data[i][j] = data["Data"].value[j][2 + matrix - start_index][i] / self.gains["z"][matrix - start_index]
                                self.progress.emit(float(((matrix - start_index) * x_dimension * y_dimension + i * y_dimension + j) /
                                                   (self.number_of_measured_parameters * x_dimension * y_dimension)))
                            else:
                                # if i want to set the missing data to something other then 0 i should do it here
                                pass
                matrices.append(matrix_data)

            self.data = {"x": x_axis, "y": y_axis, "matrix": matrices}
            self.progress.emit(1)
            return {"x": x_axis, "y": y_axis, "matrix": matrices}
        else:
            pass

        self.data = {"x": x_axis, "y": y_axis}
        self.progress.emit(1)
        return {"x": x_axis, "y": y_axis}

    def get_axis_data(self):
        """

        :return:
        """
        data_dict = {"x": {"name": "", "unit": ""}, "y": {"name": "", "unit": ""}, "z": {}}
        file = h5py.File(self.location)
        channel_names = file["Data"]["Channel names"]
        channel_data = file["Channels"]

        for index, channel_name_tuple in enumerate(channel_names.value):
            for channel in channel_data.value:
                if channel_name_tuple[0] == channel[0]:
                    if index in self.legend:
                        data_dict[self.legend[index]]["name"] = channel[0]
                        data_dict[self.legend[index]]["unit"] = channel[3]
                    else:
                        mi = index - len(self.legend)
                        matrix_data = {"name": channel[0], "unit": channel[3]}
                        data_dict["z"][mi] = matrix_data

        return data_dict

    def get_gains(self):
        """

        :return:
        """
        file = h5py.File(self.location)
        channel_names = file["Data"]["Channel names"]
        channel_data = file["Channels"]
        gains = {"x": 1, "y": 1, "z": {}}

        for index, channel_name_tuple in enumerate(channel_names.value):
            for channel in channel_data.value:
                if channel_name_tuple[0] == channel[0]:
                    if index in self.legend:
                        gains[self.legend[index]] = channel[5]
                    else:
                        mi = index - len(self.legend)
                        gains["z"][mi] = channel[5]
        return gains

    def apply_gain_to_extracted_data(self):
        """

        :return:
        """
        for axis, data in self.data.items():
            if axis in ["x", "y"]:
                self.data[axis] = self.data[axis] / self.gains[axis]
            else:
                print(data)
                for index, matrix in enumerate(data):
                    self.data[axis][index] = self.data[axis][index] / self.gains["z"][index]


def main():
    file_location = "K:\\Measurement\\Andrea\\Majo3\\1stCooldown\\2019\\02\\Data_0217\\I_sweepSG_BG+3000mV.hdf5"

    ex = LabberData(file_location)
    ex.prepare_data()


if __name__ == "__main__":
    main()