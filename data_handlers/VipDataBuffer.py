import numpy as np
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
        legend = {0: "x", 1: "y", 2: "matrix"}
        index = 0
        m_index = 0
        data = {}
        data_dict = {"x": {}, "y": {}, "matrix": {}}

        with open(self.location, "r") as file:
            for i in file:
                if i.startswith("%"):  # for whatever reason "comment" lines start with %

                    if index <= 2:
                        index += 1
                    if index == 1:
                        data[legend[index - 1]] = np.array([])
                    else:
                        data[legend[index - 1]] = {}

                    param = i.split(" ")
                    if len(param) <= 2:  # extract name and unit for sweep params
                        data_dict[legend[index - 1]]["name"] = "".join(param[1:])
                        data_dict[legend[index - 1]]["unit"] = ""
                        data[legend[index - 1]][m_index] = np.array([])
                        print(data_dict[legend[index - 1]]["name"], data_dict[legend[index - 1]]["unit"], index,
                              m_index)
                    else:  # extract name and unit for measurement params
                        data_dict[legend[index - 1]]["name"] = "".join(param[1:-1])
                        data_dict[legend[index - 1]]["unit"] = "".join(param[-1:])
                        if legend[index - 1] == "x":
                            data[legend[index - 1]] = np.array([])
                        else:
                            data[legend[index - 1]][m_index] = np.array([])
                else:
                    if i.startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", ".", "-")):
                        new_data = self.get_data_from_string(i)
                        if legend[index - 1] == "x":
                            data[legend[index - 1]] = np.concatenate((data[legend[index - 1]], new_data))
                        else:
                            data[legend[index - 1]][m_index] = np.concatenate(
                                (data[legend[index - 1]][m_index], new_data))

        data["matrix"][0] = np.split(data["matrix"][0], len(data["x"]))
        self.axis_values = {"x": data_dict["x"], "y": {0: data_dict["y"]}, "matrix": {0: data_dict["matrix"]}}
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
    location = "K:\\FaridH\\voltage_sweep_45_data_191028_16h11m42s.txt"
    buffer = VipData(location)
    buffer.prepare_data()
    print(buffer.matrix_dimensions)
    print(buffer.axis_values)


if __name__ == "__main__":
    main()
