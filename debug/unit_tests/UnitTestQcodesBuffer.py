from data_handlers.QcodesDataBuffer import QcodesData
from debug.tester_buffer import BufferTester


def unit_test():
    # Unit test

    # QCoDeS data examples
    qc11 = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_1d1\\dac_dac1_attenuated_set.dat"
    qc12 = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_1d2(long test)\\test_g1_set.dat"
    qc21 = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_2d1\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"
    qc22 = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\QCoDeS_2d2\\dac_dac5_attenuated_set_dac_dac1_attenuated_set.dat"

    file_dict = {"qc11": qc11, "qc12": qc12, "qc21": qc21, "qc22": qc22}

    qd = QcodesData(qc22)
    qd.prepare_data()
    print(qd.data["y"])
    print(qd.axis_values)

    return file_dict


def main():
    import os

    filename = os.path.basename(__file__)
    test = BufferTester(QcodesData, unit_test, filename)
    test.run()


if __name__ == "__main__":
    main()
