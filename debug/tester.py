import os
import numpy as np
import time
import getpass


class Tester:
    def __init__(self, filename):
        self.filename = filename

    def run(self):
        start_time = self.prepare_unit_test_start()
        err_num = self.run_test()
        self.finish_unit_test(start_time, err_num)

    def prepare_unit_test_start(self):
        user = getpass.getuser()
        tested_file = self.filename
        start = time.clock()

        with open("log.txt", "a+") as file:
            file.write(
                "###################################################################################################\n")
            file.write("Unit test for {} started by {}.\n".format(tested_file, user))
            file.write("Start time: {}\n\n".format(time.asctime()))

        return start

    def finish_unit_test(self, start, err_num):
        end = time.clock()
        with open("log.txt", "a+") as file:
            file.write("Unit test finished with {} error(s).\n".format(err_num))
            file.write("Execution time: {}.\n".format(end - start))
            file.write("Finish time: {}\n".format(time.asctime()))
            file.write(
                "###################################################################################################\n")

    def run_test(self):
        """
        Should be implemented in child classes, does the unit test logic for specific units

        :return: int: Number of errors that happened
        """
        raise NotImplementedError
