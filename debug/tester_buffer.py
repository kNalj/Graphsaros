import numpy as np
from debug.tester import Tester
from debug.errors import ErrorHandler
from debug.unit_tests.control_data import lb11_control, lb12_control, lb21_control, lb22_control, qc11_control, \
    qc12_control, qc21_control, qc22_control


class BufferTester(Tester):
    def __init__(self, buffer_type, unit_test, filename):
        """
        Unit test for checking if the buffers are loading in a proper way.

        :param buffer_type: One of the DataBuffer subclasses.
        :param unit_test: A function that returns files that need to be checked
        :param filename: Name of a specific unit test file which instantiated object of this class. This param is passed
        to the error handling class for easier debugging.
        """
        super().__init__(filename)

        self.buffer_type = buffer_type
        self.files = unit_test()

    def run_test(self):
        """
        Implementation of the unit test run method for buffers. Instantiate and try to load data for each of the files
        stored in self.files member variable. After loading the data compare data types and values of the data, and
        check if the axis values (for labels on graphs) were properly loaded.

        Raise a custom error handler for each caught exception and write the error traceback (with some additional data
         that allows for easier detection of bug cause) in the log file.

        :return: Number of errors that occurred during this test.
        """
        legend = {"x": "x", "y": "y", "z": "matrix"}
        error_count = 0
        key = None  # For easier debugging

        for file in self.files:
            try:
                test_subject = self.buffer_type(self.files[file])  # Check if it loads properly
                test_subject.prepare_data()  # Check that it can read data without errors

                control_name = file + "_control"  # Construct the name of the control data
                control_data = eval(control_name)  # Grab the control data

                # Test the dimensions of data
                assert test_subject.get_number_of_dimension() == control_data["dim"]["value"]
                assert isinstance(test_subject.get_number_of_dimension(), int)
                assert isinstance(test_subject.data, control_data["data"]["type"])
                assert isinstance(test_subject.axis_values, control_data["labels"]["type"])

                # Test type, shape and values of x, y and z axis data
                for key, value in legend.items():
                    if key in control_data["data"]["value"]:
                        assert isinstance(test_subject.data[value], type(control_data["data"]["value"][key]["value"]))
                        assert np.shape(test_subject.data[value]) == np.shape(control_data["data"]["value"][key]["value"])
                        assert np.allclose(test_subject.data[value], control_data["data"]["value"][key]["value"])
                        assert test_subject.axis_values[key] == control_data["labels"]["value"][key]

            except Exception:
                msg = "While testing:\n\tFile: {}\n\tAxis: {}".format(self.files[file], key)
                eh = ErrorHandler(msg)
                eh.to_file()
                error_count += 1

        return error_count
