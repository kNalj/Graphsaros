from helpers import show_error_message


class DataBuffer:

    def __init__(self, location):

        # location is absolute path to a location of the file on the disk
        self.location = location

        # data is a dictionary containing:
        #   For 3D measurement: matrix, x, y
        #       matrix: np.array containing z axis data
        #       x: list of x axis values
        #       y: list of y axis values
        #   For 2D measurement: x, y
        #       x and y same as in 3D
        self.data = None

        # list of values containing number of steps for x and y dimensions
        self.matrix_dimensions = None

    def get_matrix_dimensions(self):
        return self.matrix_dimensions

    def get_number_of_dimension(self):
        return len(self.matrix_dimensions) + 1

    def calculate_matrix_dimensions(self):
        raise NotImplementedError

    def prepare_data(self):
        raise NotImplementedError

    def get_axis_data(self):
        raise NotImplementedError

    def get_scale(self):
        return (self.data["x"][-1] - self.data["x"][0]) / (len(self.data["x"]) - 1), \
               (self.data["y"][-1] - self.data["y"][0]) / (len(self.data["y"]) - 1)

    def get_matrix(self):
        return self.data["matrix"]

    def get_x_axis_values(self):
        return self.data["x"]

    def get_y_axis_values(self):
        return self.data["y"]

    def get_location(self):
        return self.location
