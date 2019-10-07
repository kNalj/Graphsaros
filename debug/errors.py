import sys
import traceback
from time import asctime


class ErrorHandler:
    def __init__(self):
        """

        """
        self.exc_type = sys.exc_info()[0]
        self.exc_value = sys.exc_info()[1]
        self.exc_traceback = sys.exc_info()[2]

        self.list = traceback.extract_tb(self.exc_traceback)
        self.formatted = traceback.format_list(self.list)

    def format_error_msg(self):
        """

        :return:
        """
        timestamp = asctime()
        string = timestamp + "\nCaught exception of type {} cause by: {}\n".format(self.exc_type, self.exc_value)
        for frame in self.formatted:
            string = string + frame

        return string + "\n"

    def to_file(self):
        """

        :return:
        """
        with open("log.txt", "a+") as file:
            print("Writing to log")
            file.write(self.format_error_msg())
            print("Done")
