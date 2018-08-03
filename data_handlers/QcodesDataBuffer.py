import numpy as np
import helpers
import json
import os

from data_handlers.DataBuffer import DataBuffer


class QcodesData(DataBuffer):

    def __init__(self, location):
        super().__init__(location)

        self.matrix_dimensions = self.calculate_matrix_dimensions()
        self.data = self.prepare_data()
        self.axis_values = self.get_axis_data()

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
        Reads the file line by line and saves data as np.array

        :return:
        """

        data = np.loadtxt(self.location, dtype=float)
        if self.get_number_of_dimension() == 3:
            x_axis = np.unique([value[0] for value in data])
            y_axis = np.unique([value[1] for value in data])
        else:
            x_axis = np.array([value[0] for value in data])
            y_axis = np.array([value[1] for value in data])

        if self.get_number_of_dimension() == 3:
            matrix_data = np.zeros((self.matrix_dimensions[0], self.matrix_dimensions[1]))
            num_of_elements = np.size(matrix_data)
            for i in range(self.matrix_dimensions[0]):
                for j in range(self.matrix_dimensions[1]):
                    if i * self.matrix_dimensions[1] + j < num_of_elements:
                        matrix_data[i][j] = data[i * self.matrix_dimensions[1] + j][2]
            return {"x": x_axis, "y": y_axis, "matrix": matrix_data}

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
                        signify that we are using a LINL
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
                z_axis_data = json_data["actions"][0]
                return [y_axis_data, z_axis_data]
            else:
                # otherwise we only need y axis data since it's a 2D graph and there is no z
                y_axis_data = json_data["actions"][0]
                return [y_axis_data]


def main():
    # 3D
    # file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\qcodesGUI\\data\\2018-05-24\\#001_Test_11-17-26\\inst1_g1_set_inst1_g1_set_0.dat"

    # 2D
    # file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\qcodesGUI\\data\\2018-05-25\\#001_{name}_13-22-09\\inst1_g1_set.dat"

    # Daniels measurement example
    file_location = "K:\\Measurement\\Daniel\\2017-07-04\\#117_Belle_3to6_Daimond_PLLT_LTon700_CTon910_SLon1900_17-13-25\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"

    data = QcodesData(file_location)


if __name__ == '__main__':
    main()
