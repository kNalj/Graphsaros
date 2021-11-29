import numpy as np
import pandas as pd
import helpers
import json
import os

from data_handlers.QcodesDataBuffer import QcodesData


class QttData(QcodesData):

    def __init__(self, location):
        super().__init__(location)

    def get_axis_data(self):
        """
        Function that gets a matrix file location as parameter, and looks for snapshot.json file within the same directory.
        If such file exists then get data from it, otherwise show an error msg saying that there is no such a file

        :return: array: [x, y, z] or [x, y]
        """
        snapshot_file_location = os.path.dirname(self.location) + "\\snapshot.json"
        measured = {}
        if os.path.exists(snapshot_file_location):
            with open(snapshot_file_location) as file:
                json_data = json.load(file)

            data_dict = {"x": {"name": "", "unit": ""}, "y": {}, "z": {}}

            for param, data in json_data["__dataset_metadata"]["arrays"].items():
                if data["is_setpoint"]:
                    self.number_of_set_parameters += 1
                    if len(data["shape"]) == 1:
                        data_dict["x"] = data
                    else:
                        data_dict["y"][0] = data
                else:
                    measured[self.number_of_measured_parameters] = data
                    self.number_of_measured_parameters += 1

            if self.number_of_set_parameters == 1:
                data_dict["y"] = measured
            else:
                data_dict["z"] = measured

            for k, v in data_dict.items():
                print(k, v)

            return data_dict

        else:
            helpers.show_error_message("Warning", "Aborted, snapshot.json file does not exist for this measurement")
            return
