

class DataBuffer:

    def __init__(self, location):
        self.location = location
        self.data = None
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
