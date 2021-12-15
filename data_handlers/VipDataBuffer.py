import numpy as np
import pandas as pd
from data_handlers.DataBuffer import DataBuffer


class VipData(DataBuffer):
    """

    """

    def __init__(self, location):
        """

        """
        super().__init__(location)

    def calculate_matrix_dimensions(self):
        """

        """
        index = 0
        dim = []
        if self.matrix_dimensions is None:
            with open(self.location) as file:
                for i in file:
                    if i.startswith("%"):
                        index += 1

        else:
            pass

    def prepare_data(self):
        """

        """
        data = {}
        data_dict = {"x": {}, "y": {}, "matrix": {}}

        with open(self.location, "r") as file:
            for i in file:
                if i.startswith("%"):  # for whatever reason "comment" lines start with %
                    axis = i.strip("\n").split(" ")[1:]
                    if len(axis) > 1:
                        name = "".join(axis[:-1])
                        unit = axis[-1:][0]
                    else:
                        name = axis[0]
                        unit = ""
                    if not data_dict["y"]:
                        data_dict["y"][len(data_dict["y"])] = {"name": name, "unit": unit}
                    elif not data_dict["x"]:
                        data_dict["x"] = {"name": name, "unit": unit}
                    else:
                        data_dict["matrix"][len(data_dict["matrix"])] = {"name": name, "unit": unit}

        self.axis_values = {"x": data_dict["x"], "y": data_dict["y"], "matrix": data_dict["matrix"]}
        self.data = data
        return data

    def get_axis_data(self):
        """

        """
        pass

    def get_data_from_string(self, string: str) -> np.ndarray:
        """
        Helper method that extracts data from a string

        :param string: input string of values
        :return: cast all strings to floats and return it as a list
        """
        list_of_strings = string.split("\t")
        float_data = np.array([float(s) for s in list_of_strings])
        return float_data


def main():
    location = "D:\\Projects\\Graphsaros\\data\\1x1\\JPA_Pump9MHzHigher_Pumppower-2p0dBm_VNAPower_-30dBm_103_data_211207_18h18m48s.txt"
    buffer = VipData(location)
    buffer.prepare_data()
    print(buffer.matrix_dimensions)
    print(buffer.axis_values)


if __name__ == "__main__":
    main()
