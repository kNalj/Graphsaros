import sys
import traceback as tb
from time import asctime


class ErrorHandler:
    def __init__(self, msg=None, exc_type=None, exc_value=None, exc_traceback=None):
        """

        :param msg:
        """
        self.msg = msg

        if exc_type is None:
            self.exc_type = sys.exc_info()[0]
        else:
            self.exc_type = exc_type

        if exc_value is None:
            self.exc_value = sys.exc_info()[1]
        else:
            self.exc_value = exc_value

        if exc_traceback is None:
            self.exc_traceback = sys.exc_info()[2]
        else:
            self.exc_traceback = exc_traceback

        self.list = tb.extract_tb(self.exc_traceback)
        self.formatted = tb.format_list(self.list)

    def format_error_msg(self):
        """

        :return:
        """
        timestamp = asctime()
        string = timestamp + "\n" + self.msg
        string = string + "\nCaught exception of type {} caused by: {}\n".format(self.exc_type, self.exc_value)
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

    @staticmethod
    def string_to_file(string):
        with open("log.txt", "a+") as file:
            print("Writing to log")
            file.write(string)
            print("Done")

    def print_full_report(self):
        print('\x1b[0;31;49m' + self.format_error_msg() + '\x1b[0m')
