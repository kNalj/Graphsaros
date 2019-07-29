import numpy as np
import pandas as pd
import helpers
import json
import os

from data_handlers.DataBuffer import DataBuffer


class QcodesData(DataBuffer):

    def __init__(self, location):
        """
        Inherits: DataBuffer()

        Data buffer for qcodes files.

        :param location: string: location of the file on the disk
        """
        super().__init__(location)

        # dimensions of the matrix  (basically number of points on x and y axis)
        self.matrix_dimensions = self.calculate_matrix_dimensions()

        # get data from the file (read x, y and z data and save it as a member variable)
        self.data = {}  # self.prepare_data()

        # from snapshot.json file get data about names, units, etc. of the each individual axis
        self.axis_values = self.get_axis_data()

        self.string_type = "QCoDeS"

    def calculate_matrix_dimensions(self):
        """
        Opens the file and calculates dimensions of the data matrix. Returns array representing dimensions of the matrix

        In QCoDeS files dimensions of your measurement are stored in the third line of the output file and that is where
        they are read from.

        :return: array: [x, y]
                        x - number of points on x axis
                        y - number of points on y axis
        """
        matrix_dimensions = []
        with open(self.location, "r") as file:
            for i, line in enumerate(file):
                if i == 2:  # this line contains the format of the data matrix
                    matrix_dimensions = [int(number) for number in line[2:].strip("\n").split("\t")]
                    break

        if not matrix_dimensions:
            # this should probably try to do a backup way of calculating dimensions, should be implemented in the
            # parrent class
            raise ValueError("File does not contain matrix dimension data (AND IT SHOULD !)")
        else:
            return matrix_dimensions

    def prepare_data(self):
        """
        Reads the file line by line and saves data as list of np.arrays (some measurements measure more then just one
        parameter, which is why it was necessary to enable savig multiple matrices)

        :return: dict: {x: np.array, y: np.array, z: [np.ndarray]}
                        x: contains set values of parameter that represents x axis on the graph
                        y: contains set values of parameter that represents y axis on the graph
                        z: contains list of ndarrays, which represent results of measured parameters
        """
        data = np.loadtxt(self.location, dtype=float)
        self.textual = np.array2string(data)
        self.number_of_set_parameters = self.get_number_of_dimension() - 1
        self.number_of_measured_parameters = np.shape(data)[1] - self.number_of_set_parameters

        if self.get_number_of_dimension() == 3:
            x_axis = pd.unique([value[0] for value in data])
            y_axis = pd.unique([value[1] for value in data])
        else:
            x_axis = np.array([value[0] for value in data])
            y_axis = np.array([value[1] for value in data])

        if self.get_number_of_dimension() == 3:
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
                            if len(data) > i * y_dimension + j:
                                matrix_data[i][j] = data[i * y_dimension + j][matrix]
                                self.progress.emit(((matrix - start_index) * x_dimension * y_dimension + i * y_dimension + j) /
                                                   (self.number_of_measured_parameters * x_dimension * y_dimension))
                            else:
                                pass
                                # matrix_data[i][j] = float("NaN")
                matrices.append(matrix_data)
            self.data = {"x": x_axis, "y": y_axis, "matrix": matrices}
            self.progress.emit(1)
            self.unit_correction()
            return {"x": x_axis, "y": y_axis, "matrix": matrices}

        self.data = {"x": x_axis, "y": y_axis}
        self.progress.emit(1)
        self.unit_correction()
        return {"x": x_axis, "y": y_axis}

    def get_axis_data(self):
        """
        Function that gets a matrix file location as parameter, and looks for snapshot.json file within the same directory.
        If such file exists then get data from it, otherwise show an error msg saying that there is no such a file

        :return: array: [x, y, z] or [x, y]
        """
        snapshot_file_location = os.path.dirname(self.location) + "\\snapshot.json"
        data_list = []
        if os.path.exists(snapshot_file_location):
            with open(snapshot_file_location) as file:
                data = json.load(file)

            data_list = self.get_sweep_param_data(data) + self.get_action_param_data(data)
            data_dict = {}
            legend = {0: "x", 1: "y", 2: "z"}
            for index in range(len(data_list)):
                data_dict[legend[index]] = data_list[index]
            return data_dict
        else:
            helpers.show_error_message("Warning", "Aborted, snapshot.json file does not exist for this measurement")
            return

    def get_sweep_param_data(self, json_data):
        """
        Method that reads sweep parameter data from json file passed to it, used to get units for graph

        :param json_data: json format of data file that qcodes creates after running a measurement, file name is
                            snapshot.json and is located in the same directory as the mesurement output file (matrix file)
        :return: array: contining dictionary with sweep parameter data
        """

        if "loop" in json_data:
            json_data = json_data["loop"]

        x_axis_data = json_data["sweep_values"]["parameter"]
        return [x_axis_data]

    def get_action_param_data(self, json_data, depth=False):
        """
        Method that reads action parameter data from json file passed to it, used to get units for graph.

        :param json_data: json format of data file that qcodes creates after running a measurement, file name is
                            snapshot.json and is located in the same directory as the mesurement output file (matrix file)
        :param depth: boolean that is FALSE by default, unless there is a recursive call to self when its set to True to
                        signify that we are using a loop in a loop

        :return: array: containing one or two dictionaries (depending if its 2D or 3D measurement) containing data for all
                        action parameters
        """

        if "loop" in json_data:
            json_data = json_data["loop"]

        actions = json_data["actions"]
        if actions[0]["__class__"] == "qcodes.loops.ActiveLoop":
            return self.get_action_param_data(actions[0], True)
        else:
            if depth:
                # if depth is not 0, then we have a LINL, and we need both y and z axis data
                y_axis_data = json_data["sweep_values"]["parameter"]
                z_axis_data = {}
                for i, action in enumerate(json_data["actions"]):
                    z_axis_data[i] = json_data["actions"][i]
                return [y_axis_data, z_axis_data]
            else:
                # otherwise we only need y axis data since it's a 2D graph and there is no z
                y_axis_data = json_data["actions"][0]
                return [y_axis_data]

    def unit_correction(self):
        """
        Scan all axes and their units. Make all units comply with the SI standard.

        :return: NoneType
        """
        for axis in self.axis_values:
            if axis == "z":
                for i in self.axis_values[axis]:
                    if "unit" in self.axis_values[axis][i]:
                        unit = self.axis_values[axis][i]["unit"]
                        self.apply_unit_correction(axis, unit, matrix=i)
            else:
                unit = self.axis_values[axis]["unit"]
                self.apply_unit_correction(axis, unit)
        return

    def apply_unit_correction(self, axis, unit, matrix=None):
        """
        qCoDeS uses mV as a default unit. For this reason data needs to be corrected to V. So all of the data is
        multiplied by a value that is infront of the standard unit.

        :param axis: string x, y or z: which of the three axis to apply the correction to
        :param unit: Current unit for the axis passed by parameter axis
        :param matrix: in case that the axis is z, since z can have more then 1 matrix, we need to specify which matrix
                        are we making the correction for
        :return: NoneType
        """
        valid_unit = False
        values = {"": 1, "p": 1e-12, "n": 1e-9, "µ": 1e-6, "m": 1e-3, "k": 1e3, "M": 1e6, "G": 1e9}
        for j in ["", "p", "n", "µ", "m", "k", "M", "G"]:
            if valid_unit:
                break
            for k in ["A", "V", "Ω", "Ohm", "W", "var", "VA", "F", "H", "S", "C", "Ah", "J", "Wh", "eV",
                      "T", "G", "Wb", "Hz", "dB", "s"]:
                if unit == j + k:
                    valid_unit = True
                    break
            if valid_unit:
                if matrix is not None:
                    self.axis_values[axis][matrix]["unit"] = k
                    self.apply_gains(axis, values[j], matrix=matrix)
                else:
                    self.axis_values[axis]["unit"] = k
                    self.apply_gains(axis, values[j], matrix=matrix)
        return

    def apply_gains(self, axis, gain, matrix=None):
        """
        Since the unit changes, we also have to change the data accordingly.

        :param axis: string x, y or z: which of the three axis to apply the correction to
        :param gain: What gain needs to be applied to this data
        :param matrix: in case that the axis is z, since z can have more then 1 matrix, we need to specify which matrix
                        are we making the correction for
        :return: NoneType
        """
        if matrix is not None:
            print("apply {} multiplier to axis {} data, matrix {}".format(gain, axis, matrix))
            self.data["matrix"][matrix] *= gain
        else:
            print("apply {} multiplier to axis {} data".format(gain, axis))
            self.data[axis] *= gain


def main():

    file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_Daniel_2d1\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"
    # 3D
    #file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\qcodesGUI\\data\\2018-05-24\\#001_Test_11-17-26\\inst1_g1_set_inst1_g1_set_0.dat"

    file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_Josh_3d_2m\\\dac_dac5_attenuated_set_dac_dac1_attenuated_set.dat"

    # 2D
    # file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\qcodesGUI\\data\\2018-05-25\\#001_{name}_13-22-09\\inst1_g1_set.dat"

    # Daniels measurement example
    # file_location = "K:\\Measurement\\Daniel\\2017-07-04\\#117_Belle_3to6_Daimond_PLLT_LTon700_CTon910_SLon1900_17-13-25\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"

    data = QcodesData(file_location)
    data.prepare_data()
    # print(data.data)
    # print(data.axis_values)
    data.unit_correction()


if __name__ == '__main__':
    main()
