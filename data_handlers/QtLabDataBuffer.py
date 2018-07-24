import numpy as np

from data_handlers.DataBuffer import DataBuffer


class QtLabData(DataBuffer):

    def __init__(self, location):
        super().__init__(location)

        self.data = {}
        self.matrix_dimensions = self.calculate_matrix_dimensions()
        self.prepare_data()
        self.axis_values = self.get_axis_data()

    def calculate_matrix_dimensions(self):
        x = np.loadtxt(self.location, dtype=float, usecols=1)
        x_axis = np.unique(x)
        self.data["x"] = x_axis

        y = np.loadtxt(self.location, dtype=float, usecols=0)
        y_axis = np.unique(y)
        self.data["y"] = y_axis
        return [len(x_axis), len(y_axis)]

    def prepare_data(self):
        if self.get_number_of_dimension() == 2:
            return
        else:
            matrix_data = np.zeros((self.matrix_dimensions[0], self.matrix_dimensions[1]))
            z = np.loadtxt(self.location, dtype=float, usecols=2)
            for i in range(self.matrix_dimensions[0]):
                for j in range(self.matrix_dimensions[1]):
                    matrix_data[i][j] = z[i * self.matrix_dimensions[1] + j]

        self.data["matrix"] = matrix_data

    def get_axis_data(self):
        """
        Axis data should contain keys "name" and "value"

        :return:
        """
        data_dict = {"x": {"name": "", "unit": ""}, "y": {"name": "", "unit": ""}, "z": {"name": "", "unit": ""}}
        legend = {0: "y", 1: "x", 2: "z"}
        index = -1
        with open(self.location) as file:
            for i in file:
                if "Column" in i:
                    index += 1
                elif i.lstrip("\t#").startswith("name:"):
                    data = i.strip("#\t\n").lstrip("name: ")
                    start = data.find("[")
                    end = data.find("]")
                    name = data[:start-1]
                    unit = data[start+1:end]
                    data_dict[legend[index]]["name"] = name
                    data_dict[legend[index]]["unit"] = unit
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
