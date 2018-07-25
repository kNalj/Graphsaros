import numpy as np

from data_handlers.DataBuffer import DataBuffer


class QtLabData(DataBuffer):

    def __init__(self, location):
        self.legend = {0: "x", 1: "y", 2: "z"}
        super().__init__(location)

        self.data = {}
        self.matrix_dimensions = self.calculate_matrix_dimensions()
        self.prepare_data()
        self.axis_values = self.get_axis_data()

    def calculate_matrix_dimensions(self):
        axis_data = np.loadtxt(self.location, dtype=float, usecols=(0, 1))
        if axis_data[0][1] == axis_data[1][1]:
            y_axis = np.unique([value[0] for value in axis_data])
            x_axis = np.unique([value[1] for value in axis_data])
            self.legend[0] = "y"
            self.legend[1] = "x"
        elif axis_data[0][0] == axis_data[1][0]:
            x_axis = np.unique([value[0] for value in axis_data])
            y_axis = np.unique([value[1] for value in axis_data])
        self.data["x"] = x_axis
        self.data["y"] = y_axis
        return [len(x_axis), len(y_axis)]

    def prepare_data(self):
        if self.get_number_of_dimension() == 2:
            return
        else:
            matrix_data = np.zeros((self.matrix_dimensions[0], self.matrix_dimensions[1]))
            z = np.loadtxt(self.location, dtype=float, usecols=2)
            num_of_elements = np.size(z)
            for i in range(self.matrix_dimensions[0]):
                for j in range(self.matrix_dimensions[1]):
                    if i * self.matrix_dimensions[1] + j < num_of_elements:
                        matrix_data[i][j] = z[(i * self.matrix_dimensions[1]) + j]

        self.data["matrix"] = matrix_data

    def get_axis_data(self):
        """
        Axis data should contain keys "name" and "value"

        :return:
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
                    for i in ["", "p", "n", "µ", "m", "k", "M", "G"]:
                        if valid_unit:
                            break
                        for j in ["A", "V", "Ω", "Ohm", "W", "var", "VA", "F", "H", "S", "C", "Ah", "J", "Wh", "eV",
                                  "T", "G", "Wb", "Hz", "dB", "s"]:
                            if unit == i+j:
                                valid_unit = True
                                break
                    if valid_unit:
                        name = data
                        data_dict[self.legend[index]]["unit"] = unit
                        data_dict[self.legend[index]]["name"] = name
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
