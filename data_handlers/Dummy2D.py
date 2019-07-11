from data_handlers.DataBuffer import DataBuffer


class DummyBuffer(DataBuffer):
    """
    Dummy data buffer used to represent line trace taken in Heatmap window when it gets opened in the LineTrace window.

    """

    def __init__(self, name, x, y, extra_axis=None, location="Dummy"):

        super().__init__(location)

        self.name = name
        self.data = {"x": x["values"], "y": y["values"]}
        self.axis_values = {"x": x["axis"], "y": y["axis"]}
        if extra_axis is not None:
            self.data["extra_axis"] = extra_axis["values"]
            self.axis_values["extra_axis"] = extra_axis["axis"]
        self.matrix_dimensions = [len(x["values"]), len(y["values"])]

    def calculate_matrix_dimensions(self):
        return

    def prepare_data(self):
        return

    def get_axis_data(self):
        return


def main():
    test = DummyBuffer("test name",
                       {"values": [1, 2, 3], "axis": {"name": "test label", "unit": "test unit"}},
                       {"values": [5, 14, 23], "axis": {"name": "y test label", "unit": "y test unit"}})
    print(test.location)
    print(test.get_y_axis_values(), test.get_x_axis_values())
    print(test.axis_values)


if __name__ == "__main__":
    main()
