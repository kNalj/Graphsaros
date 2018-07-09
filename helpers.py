from PyQt5.QtWidgets import QProgressBar, QDialog, QApplication, QGridLayout, QMessageBox
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

import numpy as np
import os
import time
import sys
import json


def split_location_string(location: str):
    """
    Returns only the [parent directory, filename] from full location of the file

    :param location: string: location of the file on the disk
    :return: list: [parent directory, name of the file]
    """
    return [os.path.dirname(location), os.path.basename(location)]


def get_data_from_qcodes_dat_file(location):
    """
    Gets the location of the .dat file and returns numpy adarray (datatype suitable for ploting 3d graphs)

    :param location: string: location of the file on the filesystem
    :return: array: [matrix_file, x_axis_values, y_axis_values] containing 2D numpy array, array of x values, and array
                    array of y values
    """
    with open(location, "r") as file:
        data = []
        for i, line in enumerate(file):
            if i == 2:  # this line contains the format of the data matrix
                matrix_dimensions = [int(number) for number in line[2:].strip("\n").split("\t")]
            if line[0] != "#":
                array = line.strip('\n').split('\t')
                if array != [""]:
                    float_array = [float(value) for value in array]
                    data.append(float_array)

    x_axis_data = []
    y_axis_data = []
    matrix_data = np.zeros((matrix_dimensions[0], matrix_dimensions[1]))
    for i in range(matrix_dimensions[0]):
        x_axis_data.append(data[i * matrix_dimensions[1]][0])
        for j in range(matrix_dimensions[1]):
            matrix_data[i][j] = data[i * 11 + j][2]
            if i == 0:
                y_axis_data.append(data[j][2])
    return [matrix_data, x_axis_data, y_axis_data]


def get_data_from_snapshot_file(matrix_file_location):
    """
    Function that gets a matrix file location as parameter, and looks for snapshot.json file within the same directory.
    If such file exists then get data from it, otherwise show an error msg saying that there is no such a file

    :param matrix_file_location: string: absolute path to the matrix file
    :return: array: [x, y, z]
    """
    snapshot_file_location = os.path.dirname(matrix_file_location) + "\\snapshot.json"
    data_list = []
    if os.path.exists(snapshot_file_location):
        with open(snapshot_file_location) as file:
            data = json.load(file)

        data_list = get_sweep_param_data(data) + get_action_param_data(data)
        return data_list
    else:
        show_error_message("Warning", "Aborted, snapshot.json file does not exist for this measurement")
        return


def get_sweep_param_data(json_data):
    """
    Function that reads sweep parameter data from json file passed to it, used to get units for graph

    :param json_data: json format of data file that qcodes creates after running a measurement, file name is
                        snapshot.json and is located in the same directory as the mesurement output file (matrix file)
    :return: array: contining dictionary with sweep parameter data
    """

    if "loop" in json_data:
        json_data = json_data["loop"]

    x_axis_data = json_data["sweep_values"]["parameter"]
    return [x_axis_data]


def get_action_param_data(json_data, depth=False):
    """
    Function that reads action parameter data from json file passed to it, used to get units for graph.

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
        return get_action_param_data(actions[0], True)
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


def get_subfolders(path):
    """
    Helper function to find all folders within folder specified by "path"

    :param path: path to folder to scrap subfolders from
    :return: list[] of subfolders from specified path
    """
    return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0]]


def get_files_in_folder(path):
    """
    Helper function to find all files within folder specified by path

    :param path: path to folder to scrap files from
    :return: list[] of files from specified path
    """
    return [f.name for f in os.scandir(path) if f.is_file()]


def show_error_message(title, message):
    """
    Function for displaying warnings/errors

    :param title: Title of the displayed watning window
    :param message: Message shown by the displayed watning window
    :return: NoneType
    """
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowIcon(QIcon("img/warning_icon.png"))
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()


class ProgressBarWidget(QDialog):

    def __init__(self):
        super().__init__()

        self.init_ui()
        self.show()

    def init_ui(self):

        self.setWindowTitle("Procesing . . .")
        self.setGeometry(200, 200, 200, 50)
        self.grid_layout = QGridLayout()
        self.progressBar = QProgressBar()
        self.grid_layout.addWidget(self.progressBar)
        self.setLayout(self.grid_layout)

    def setValue(self, val):  # Sets value
        self.progressBar.setProperty("value", val)


def main():

    app = QApplication(sys.argv)
    ex = ProgressBarWidget()
    for i in range(0, 100):
        time.sleep(0.05)
        ex.setValue(((i + 1) / 100) * 100)
        QApplication.processEvents()
    ex.close()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()