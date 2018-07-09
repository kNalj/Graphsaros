

class DataBuffer:

    def __init__(self, location):
        self.location = location

    def get_matrix_dimensions(self):
        raise NotImplementedError

    def get_number_of_dimensions(self):
        raise NotImplementedError

    def prepare_data(self):
        raise NotImplementedError

    def get_axis(self):
        raise NotImplementedError

    def get_axis_data(self):
        raise NotImplementedError
