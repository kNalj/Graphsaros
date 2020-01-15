from data_handlers.LabberDataBuffer import LabberData
from debug.tester_buffer import BufferTester
import os


def unit_test():
    # Unit test

    # Labber data examples
    lb11 = "..\\..\\other\\Labber_1d1\\1x1.hdf5"
    lb12 = "..\\..\\other\\Labber_1d2\\1x2.hdf5"
    lb21 = "..\\..\\other\\Labber_2d1\\2x1.hdf5"
    lb22 = "..\\..\\other\\Labber_2d2\\2x2.hdf5"

    file_dict = {"lb11": lb11, "lb12": lb12, "lb21": lb21, "lb22": lb22}

    return file_dict


def main():

    filename = os.path.basename(__file__)
    test = BufferTester(LabberData, unit_test, filename)
    test.run()


if __name__ == "__main__":
    main()
