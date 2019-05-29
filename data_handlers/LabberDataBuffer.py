import numpy as np
import pandas as pd
import h5py
from Script import Labber

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

        self.alternate = False

        self.log_file = Labber.LogFile(location)

        self.matrix_dimensions = self.calculate_matrix_dimensions()

        self.axis_values = self.get_axis_data()

        self.string_type = "Labber"

    def calculate_matrix_dimensions(self):
        """
        Opens file and calculates dimensions of the data matrix. Returns array representing dimensions of the matrix.

        :return: array: [x, y]
                        x - number of points on x axis
                        y - number of points on y axis
        """


        self.candidates = []
        for channel in self.log_file.getStepChannels():
            if len(channel["values"]) > 1:
                self.candidates.append(channel)

        if len(self.candidates) == 2:
            for channel in self.log_file.getStepChannels():
                data = self.log_file.getData(channel["name"])
                if self.check_if_alternate_direction(data):
                    self.alternate = True

            matrix_dimensions = [len(self.candidates[0]["values"]), len(self.candidates[1]["values"])]

            self.number_of_set_parameters = 2
        elif len(self.candidates) == 1:
            matrix_dimensions = [len(self.log_file.getData(self.log_file.getLogChannels()[0]["name"]))]
            self.axis_values = {"x": {"name": self.log_file.getStepChannels()[0]["name"],
                                      "unit": self.log_file.getStepChannels()[0]["unit"]},
                                "y": {"name": self.log_file.getLogChannels()[0]["name"],
                                      "unit": self.log_file.getLogChannels()[0]["unit"]}}
        else:
            "I need to create a widget that lets you select the things"
            pass
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

        self.textual = np.array2string(self.log_file.getData(self.log_file.getLogChannels()[0]["name"]))

        self.number_of_measured_parameters = self.log_file.getNumberOfLogs()
        names = [channel["name"] for channel in self.log_file.getLogChannels()]

        if self.get_number_of_dimension() == 3:
            x_axis = self.candidates[0]["values"]
            y_axis = self.candidates[1]["values"]
        else:
            x_axis = self.candidates[0]["values"]
            y_axis = self.candidates[1]["values"]

        if self.get_number_of_dimension() == 3:
            print("Fetching matrix values . . .")
            matrices = []
            x_dimension = self.matrix_dimensions[0]
            y_dimension = self.matrix_dimensions[1]
            for matrix in range(self.number_of_measured_parameters):
                data = self.log_file.getData(names[matrix])
                matrix_data = np.zeros((x_dimension, y_dimension))
                num_of_elements = np.size(data)
                for i in range(x_dimension):
                    for j in range(y_dimension):
                        if i * y_dimension + j < num_of_elements:
                            if self.alternate and j % 2:
                                matrix_data[i][j] = data[j][-i-1]
                            else:
                                matrix_data[i][j] = data[j][i]
                            self.progress.emit(
                                ((matrix - self.number_of_set_parameters) * x_dimension * y_dimension + i * y_dimension + j) /
                                (self.number_of_measured_parameters * x_dimension * y_dimension))
                        else:
                            pass
                matrices.append(matrix_data)

            self.data = {"x": x_axis, "y": y_axis, "matrix": matrices}
            self.progress.emit(1)
            return {"x": x_axis, "y": y_axis, "matrix": matrices}

        self.data = {"x": x_axis, "y": y_axis}
        self.progress.emit(1)
        return {"x": x_axis, "y": y_axis}

    def get_axis_data(self):
        """

        :return:
        """
        if self.get_number_of_dimension() == 3:
            data_dict = {"x": {"name": self.candidates[0]["name"], "unit": self.candidates[0]["unit"]},
                         "y": {"name": self.candidates[1]["name"], "unit": self.candidates[1]["unit"]},
                         "z": {}}

            data = [(channel["name"], channel["unit"]) for channel in self.log_file.getLogChannels()]
            for index, channel in enumerate(data):
                channel_dict = {}
                channel_dict["name"], channel_dict["unit"] = channel
                data_dict["z"][index] = channel_dict

        elif self.get_number_of_dimension() == 2:
            data_dict = {"x": {"name": self.log_file.getStepChannels()[0]["name"],
                               "unit": self.log_file.getStepChannels()[0]["unit"]},
                         "y": {"name": self.log_file.getLogChannels()[0]["name"],
                               "unit": self.log_file.getLogChannels()[0]["unit"]}}

        return data_dict

    def check_if_alternate_direction(self, data):
        """
        Check if this log file was created with alternate direction option ticked. Take the passed data set and check if
        the first and the second row are inverse of one another. If yes, the option was ticked.

        :param data:
        :return:
        """

        if (data[0] == np.flip(data[1], axis=0)).all():
            return True
        return False

def main():
    file_location = "K:\\Measurement\\Andrea\\Majo3\\1stCooldown\\2019\\02\\Data_0217\\I_sweepSG_BG+3000mV.hdf5"

    ex = LabberData(file_location)
    ex.prepare_data()


if __name__ == "__main__":
    main()